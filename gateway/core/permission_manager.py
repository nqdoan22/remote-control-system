"""
core/permission_manager.py — Xử lý Permission Confirmation flow.

Theo api_contract.md — Permission Confirmation Messages:

  1. Web App gửi sensitive command (vd: screen.live.start)
  2. Gateway intercept → gửi permission.request xuống Client App
  3. Client App hiển thị dialog, End User Accept/Reject
  4. Client App gửi permission.response { granted: true/false }
  5a. granted=true  → Gateway forward lệnh gốc xuống Client App
  5b. granted=false → Gateway trả PERMISSION_DENIED về Web App

  Timeout: nếu không nhận permission.response trong PERMISSION_TIMEOUT giây
           → Gateway trả PERMISSION_TIMEOUT về Web App

Lưu ý thiết kế:
  - Mỗi pending request được lưu theo permissionId (UUID).
  - asyncio.Event dùng để chờ response từ Client App mà không block event loop.
  - Timeout được xử lý bằng asyncio.wait_for.
"""

import asyncio
import logging
import uuid

import config
from models.message import make_message, make_error, get_payload

logger = logging.getLogger("gateway.permission_manager")


class PendingPermission:
    """Lưu thông tin một permission request đang chờ End User phản hồi."""

    __slots__ = (
        "permission_id",
        "machine_id",
        "feature",
        "original_message",
        "requested_by",
        "event",
        "granted",
    )

    def __init__(
        self,
        permission_id: str,
        machine_id: str,
        feature: str,
        original_message: dict,
        requested_by: str,
    ):
        self.permission_id = permission_id
        self.machine_id = machine_id
        self.feature = feature
        self.original_message = original_message
        self.requested_by = requested_by
        self.event = asyncio.Event()  # set khi nhận permission.response
        self.granted: bool | None = None  # None = chưa có response


class PermissionManager:
    """
    Quản lý toàn bộ permission confirmation flow.
    Một instance được chia sẻ qua toàn bộ Gateway.
    """

    def __init__(self):
        # permissionId -> PendingPermission
        self._pending: dict[str, PendingPermission] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def request(
        self,
        machine_id: str,
        original_message: dict,
        requested_by: str,
        manager,  # ConnectionManager — tránh circular import bằng type hint string
    ) -> tuple[bool, str]:
        """
        Gửi permission.request xuống Client App và chờ phản hồi.

        Returns:
            (True, "")                  — End User chấp nhận
            (False, "PERMISSION_DENIED")   — End User từ chối
            (False, "PERMISSION_TIMEOUT")  — Hết thời gian chờ
        """
        from models.message import get_type, get_message_id

        permission_id = str(uuid.uuid4())
        msg_type = get_type(original_message)
        # feature = phần trước .start  (vd: "screen.live.start" → "screen.live")
        feature = msg_type.rsplit(".start", 1)[0] if msg_type.endswith(".start") else msg_type
        original_msg_id = get_message_id(original_message)

        pending = PendingPermission(
            permission_id=permission_id,
            machine_id=machine_id,
            feature=feature,
            original_message=original_message,
            requested_by=requested_by,
        )
        self._pending[permission_id] = pending

        # Gửi permission.request xuống Client App
        request_msg = make_message(
            msg_type="permission.request",
            payload={
                "permissionId": permission_id,
                "feature": feature,
                "requestedBy": requested_by,
                "originalMessageId": original_msg_id,
            },
            destination=machine_id,
        )
        sent = await manager.send_to_machine(machine_id, request_msg)
        if not sent:
            del self._pending[permission_id]
            return False, "MACHINE_OFFLINE"

        logger.info(
            "Permission requested: feature='%s' machine='%s' permissionId='%s'",
            feature, machine_id, permission_id,
        )

        # Chờ End User phản hồi, tối đa PERMISSION_TIMEOUT giây
        try:
            await asyncio.wait_for(
                pending.event.wait(),
                timeout=config.PERMISSION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Permission timeout: feature='%s' machine='%s' permissionId='%s'",
                feature, machine_id, permission_id,
            )
            del self._pending[permission_id]
            return False, "PERMISSION_TIMEOUT"

        # Nhận được response
        del self._pending[permission_id]

        if pending.granted:
            logger.info(
                "Permission granted: feature='%s' machine='%s'", feature, machine_id
            )
            return True, ""
        else:
            logger.info(
                "Permission denied: feature='%s' machine='%s'", feature, machine_id
            )
            return False, "PERMISSION_DENIED"

    def resolve(self, permission_id: str, granted: bool) -> bool:
        """
        Nhận permission.response từ Client App và giải quyết pending request.

        Returns:
            True  — tìm thấy và giải quyết thành công
            False — không tìm thấy permissionId (đã timeout hoặc không hợp lệ)
        """
        pending = self._pending.get(permission_id)
        if pending is None:
            logger.warning(
                "Received permission.response for unknown permissionId '%s' (expired or invalid)",
                permission_id,
            )
            return False

        pending.granted = granted
        pending.event.set()  # unblock asyncio.wait_for trong request()
        return True

    def has_pending(self, permission_id: str) -> bool:
        return permission_id in self._pending
