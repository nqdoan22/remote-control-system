"""
handlers/client_handler.py — Xử lý kết nối từ Client App.

Flow theo security_design.md:
  1. Client App kết nối WebSocket tới /client
  2. Message đầu tiên PHẢI là auth.client
  3. Gateway validate machineId + machineSecret
  4. Nếu hợp lệ → gửi response success, chuyển sang receive loop
  5. Nếu không hợp lệ → gửi error AUTHENTICATION_FAILED, đóng kết nối
"""

import json
import logging
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol

from core.auth_manager import validate_client
from core.connection_manager import ConnectionManager
from handlers.message_router import route_from_client
from models.message import (
    make_response,
    make_error,
    get_type,
    get_payload,
    get_message_id,
    validate_message,
)

logger = logging.getLogger("gateway.client_handler")

# Giây — thời gian chờ message auth.client đầu tiên
AUTH_TIMEOUT = 10


async def handle_client(websocket: WebSocketServerProtocol, manager: ConnectionManager):
    """Entry point cho kết nối từ Client App."""
    remote = websocket.remote_address
    machine_id: str | None = None

    try:
        # ------------------------------------------------------------------
        # Bước 1: Chờ message auth.client đầu tiên
        # ------------------------------------------------------------------
        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=AUTH_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Client %s did not send auth.client within %ds", remote, AUTH_TIMEOUT)
            await _send(websocket, make_error(
                "AUTHENTICATION_FAILED",
                "Authentication timeout. Send auth.client as first message.",
            ))
            await websocket.close(code=4001, reason="Authentication timeout")
            return

        # ------------------------------------------------------------------
        # Bước 2: Parse và validate message format
        # ------------------------------------------------------------------
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Client %s sent invalid JSON", remote)
            await _send(websocket, make_error("AUTHENTICATION_FAILED", "Invalid JSON"))
            await websocket.close(code=4001, reason="Invalid JSON")
            return

        ok, reason = validate_message(message)
        if not ok:
            logger.warning("Client %s sent malformed message: %s", remote, reason)
            await _send(websocket, make_error("AUTHENTICATION_FAILED", reason))
            await websocket.close(code=4001, reason="Malformed message")
            return

        msg_type = get_type(message)
        if msg_type != "auth.client":
            logger.warning(
                "Client %s sent '%s' before auth.client", remote, msg_type
            )
            await _send(websocket, make_error(
                "AUTHENTICATION_FAILED",
                f"Expected auth.client as first message, got '{msg_type}'",
            ))
            await websocket.close(code=4001, reason="Expected auth.client")
            return

        # ------------------------------------------------------------------
        # Bước 3: Validate credentials
        # ------------------------------------------------------------------
        payload = get_payload(message)
        m_id = payload.get("machineId", "")
        m_secret = payload.get("machineSecret", "")
        hostname = payload.get("hostname", "unknown")
        ip_address = payload.get("ipAddress", str(remote[0]) if remote else "unknown")

        auth_ok, auth_reason = validate_client(m_id, m_secret)

        if not auth_ok:
            logger.warning(
                "Client %s authentication failed: %s", remote, auth_reason
            )
            await _send(
                websocket,
                make_error(
                    "AUTHENTICATION_FAILED",
                    auth_reason,
                    original_message_id=get_message_id(message),
                ),
            )
            await websocket.close(code=4001, reason="Authentication failed")
            return

        # ------------------------------------------------------------------
        # Bước 4: Xác thực thành công
        # ------------------------------------------------------------------
        machine_id = m_id
        machine_info = {
            "machineId": machine_id,
            "hostname": hostname,
            "ipAddress": ip_address,
        }

        logger.info(
            "Client authenticated: machineId='%s' hostname='%s' ip='%s'",
            machine_id, hostname, ip_address,
        )

        await _send(
            websocket,
            make_response(
                success=True,
                data={},
                destination=machine_id,
            ),
        )

        # Đăng ký vào ConnectionManager
        await manager.register_client(machine_id, websocket, machine_info)

        # ------------------------------------------------------------------
        # Bước 5: Receive loop — xử lý các message tiếp theo
        # ------------------------------------------------------------------
        async for raw in websocket:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from '%s'", machine_id)
                continue

            ok, reason = validate_message(message)
            if not ok:
                logger.warning("Malformed message from '%s': %s", machine_id, reason)
                continue

            msg_type = get_type(message)
            logger.debug("Received '%s' from machine '%s'", msg_type, machine_id)

            await route_from_client(message, machine_id, manager, manager.permission_manager)

    except websockets.exceptions.ConnectionClosed as exc:
        logger.info("Client '%s' (%s) disconnected: %s", machine_id or "unauthenticated", remote, exc)

    finally:
        if machine_id:
            await manager.unregister_client(machine_id)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _send(websocket: WebSocketServerProtocol, message: dict):
    """Gửi message JSON, bỏ qua nếu kết nối đã đóng."""
    try:
        await websocket.send(json.dumps(message))
    except websockets.exceptions.ConnectionClosed:
        pass
