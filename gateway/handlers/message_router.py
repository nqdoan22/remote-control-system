"""
handlers/message_router.py — Điều phối message giữa Web App và Client App.

Trách nhiệm theo system_architecture.md:
  - Routing: Web App → Client App, Client App → Web App
  - Authorization: kiểm tra nguồn gửi có được phép gửi message type đó không
  - Handle tại Gateway: machine.list, heartbeat, permission.response
  - Error: MACHINE_OFFLINE, MACHINE_NOT_FOUND, INVALID_COMMAND, AUTHORIZATION_FAILED
  - Permission: intercept SENSITIVE_MESSAGE_TYPES → PermissionManager flow

Không xử lý Business Logic — chỉ route đúng nơi.
"""

import asyncio
import logging

import config
from core.command_tracker import CommandTracker
from core.connection_manager import ConnectionManager
from core.permission_manager import PermissionManager
from models.message import (
    make_response,
    make_error,
    get_type,
    get_payload,
    get_message_id,
)

logger = logging.getLogger("gateway.message_router")

# ---------------------------------------------------------------------------
# Authorization rules
# ---------------------------------------------------------------------------

# Message types chỉ Web App được phép gửi (Command direction: webapp → machine)
_WEBAPP_ALLOWED_TYPES: frozenset[str] = frozenset({
    # Machine management (handled at Gateway)
    "machine.list",
    # Application
    "application.list",
    "application.start",
    "application.stop",
    # Process
    "process.list",
    "process.kill",
    # Screen
    "screen.screenshot",
    "screen.live.start",
    "screen.live.stop",
    # Webcam
    "webcam.start",
    "webcam.stop",
    # Keylogger
    "keylogger.start",
    "keylogger.stop",
    # File
    "file.list",
    "file.upload",
    "file.download",
    # Power
    "power.lock",
    "power.restart",
    "power.shutdown",
    "power.sleep",
})

# Message types chỉ Client App được phép gửi (Response/Event direction: machine → webapp)
# "machine.status" không nằm trong danh sách này — đó là event Gateway tự sinh ra
# để notify Web App (xem ConnectionManager._notify_machine_status), Client App
# không bao giờ gửi loại message này.
_CLIENT_ALLOWED_TYPES: frozenset[str] = frozenset({
    "response",
    "error",
    "heartbeat",
    "screen.live.frame",
    "webcam.frame",
    "keylogger.data",
    "permission.response",
})

# Message types được xử lý tại Gateway, không forward xuống Client App
_GATEWAY_HANDLED_TYPES: frozenset[str] = frozenset({
    "machine.list",
    "heartbeat",
    "permission.response",
})


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

async def route_from_webapp(
    message: dict,
    manager: ConnectionManager,
    permission_manager: "PermissionManager | None" = None,
    admin_user: str = "unknown",
    command_tracker: "CommandTracker | None" = None,
) -> None:
    """
    Xử lý message gửi từ Web App.
    Web App phải chỉ định machineId trong payload.destinationMachineId.
    """
    msg_type = get_type(message)
    msg_id = get_message_id(message)

    # Authorization
    if msg_type not in _WEBAPP_ALLOWED_TYPES:
        logger.warning("Web App sent unauthorized message type '%s'", msg_type)
        await manager.send_to_webapp(
            make_error(
                "INVALID_COMMAND",
                f"Message type '{msg_type}' is not allowed from Web App.",
                original_message_id=msg_id,
            )
        )
        return

    # machine.list — xử lý tại Gateway
    if msg_type == "machine.list":
        await _handle_machine_list(manager, msg_id)
        return

    # Các lệnh còn lại cần destinationMachineId
    payload = get_payload(message)
    machine_id = payload.get("destinationMachineId", "")

    if not machine_id:
        await manager.send_to_webapp(
            make_error(
                "INVALID_COMMAND",
                "payload.destinationMachineId is required.",
                original_message_id=msg_id,
            )
        )
        return

    # Kiểm tra machine tồn tại và online
    if not manager.registry.get(machine_id):
        await manager.send_to_webapp(
            make_error("MACHINE_NOT_FOUND", f"Machine '{machine_id}' not found.", original_message_id=msg_id)
        )
        return

    if not manager.is_machine_online(machine_id):
        await manager.send_to_webapp(
            make_error("MACHINE_OFFLINE", f"Machine '{machine_id}' is offline.", original_message_id=msg_id)
        )
        return

    # Intercept sensitive features → permission confirmation flow
    if msg_type in config.SENSITIVE_MESSAGE_TYPES and permission_manager is not None:
        granted, error_code = await permission_manager.request(
            machine_id=machine_id,
            original_message=message,
            requested_by=admin_user,
            manager=manager,
        )
        if not granted:
            await manager.send_to_webapp(
                make_error(
                    error_code,
                    f"Permission {error_code.lower().replace('_', ' ')} for '{msg_type}'.",
                    original_message_id=msg_id,
                )
            )
            return
        # granted=True → tiếp tục forward bên dưới

    # Forward message xuống Client App
    # Bỏ destinationMachineId khỏi payload trước khi forward
    forward_payload = {k: v for k, v in payload.items() if k != "destinationMachineId"}
    forward_message = {**message, "payload": forward_payload, "destination": machine_id}

    ok = await manager.send_to_machine(machine_id, forward_message)
    if not ok:
        await manager.send_to_webapp(
            make_error("MACHINE_OFFLINE", f"Failed to deliver to '{machine_id}'.", original_message_id=msg_id)
        )
        return

    # Theo dõi TIMEOUT: nếu Client App không phản hồi (response/error) trong
    # COMMAND_TIMEOUT giây, báo lỗi TIMEOUT về Web App. Chạy nền để không
    # chặn việc xử lý các message tiếp theo từ Web App.
    if command_tracker is not None:
        event = command_tracker.track(machine_id, msg_id)
        asyncio.create_task(
            _watch_command_timeout(command_tracker, manager, machine_id, msg_id, event)
        )


async def _watch_command_timeout(
    command_tracker: CommandTracker,
    manager: ConnectionManager,
    machine_id: str,
    message_id: str,
    event: asyncio.Event,
) -> None:
    """Chờ response/error từ machine; nếu hết COMMAND_TIMEOUT mà chưa có, báo TIMEOUT."""
    try:
        await asyncio.wait_for(event.wait(), timeout=config.COMMAND_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning(
            "Command '%s' to machine '%s' timed out waiting for response",
            message_id, machine_id,
        )
        await manager.send_to_webapp(
            make_error(
                "TIMEOUT",
                f"Machine '{machine_id}' did not respond in time.",
                original_message_id=message_id,
            )
        )
    finally:
        command_tracker.clear(machine_id, message_id)


async def route_from_client(
    message: dict,
    machine_id: str,
    manager: ConnectionManager,
    permission_manager: "PermissionManager | None" = None,
    command_tracker: "CommandTracker | None" = None,
) -> None:
    """
    Xử lý message gửi từ Client App.
    """
    msg_type = get_type(message)

    # Cập nhật lastSeen mỗi khi nhận bất kỳ message nào
    manager.touch_machine(machine_id)

    # Authorization
    if msg_type not in _CLIENT_ALLOWED_TYPES:
        logger.warning(
            "Machine '%s' sent unauthorized message type '%s'", machine_id, msg_type
        )
        # Không gửi error về Client App — chỉ log và bỏ qua
        return

    # heartbeat — xử lý tại Gateway, không forward
    if msg_type == "heartbeat":
        logger.debug("Heartbeat from machine '%s'", machine_id)
        return

    # permission.response — giải quyết pending request
    if msg_type == "permission.response":
        if permission_manager is not None:
            payload = get_payload(message)
            permission_id = payload.get("permissionId", "")
            granted = bool(payload.get("granted", False))
            if permission_id:
                permission_manager.resolve(permission_id, granted)
            else:
                logger.warning(
                    "permission.response from '%s' missing permissionId", machine_id
                )
        return

    # response / error — đánh dấu command tương ứng đã được giải quyết
    # (unblock CommandTracker để không báo TIMEOUT giả)
    if msg_type in ("response", "error") and command_tracker is not None:
        command_tracker.resolve(machine_id)

    # response / error / frame / keylogger.data — forward lên Web App
    forward_message = {**message, "source": machine_id, "destination": "webapp"}
    sent = await manager.send_to_webapp(forward_message)
    if not sent:
        logger.warning(
            "Dropped '%s' from machine '%s': Web App not connected", msg_type, machine_id
        )


# ---------------------------------------------------------------------------
# Gateway-handled commands
# ---------------------------------------------------------------------------

async def _handle_machine_list(manager: ConnectionManager, original_msg_id: str) -> None:
    """Trả về danh sách tất cả machines cho Web App."""
    machines = manager.get_all_machines()
    await manager.send_to_webapp(
        make_response(
            success=True,
            data={"machines": machines},
            destination="webapp",
        )
    )
    logger.debug("machine.list → returned %d machines", len(machines))
