"""
core/connection_manager.py — Quản lý WebSocket connections và điều phối send.

Trách nhiệm:
  - Lưu websocket của từng Client App và Web App.
  - Delegate trạng thái machine sang MachineRegistry.
  - Gửi message tới đúng đích.
  - Notify Web App khi machine online/offline.
"""

import json
import logging
import websockets

from core.machine_registry import MachineRegistry
from models.message import make_message

logger = logging.getLogger("gateway.connection_manager")


class ConnectionManager:
    def __init__(self):
        # machineId -> websocket
        self._client_sockets: dict[str, object] = {}
        # websocket của Web App (chỉ một kết nối tại một thời điểm)
        self._webapp_socket = None

        self.registry = MachineRegistry()

        # PermissionManager / CommandTracker — được gán sau khi khởi tạo từ main.py
        # để tránh circular import
        self.permission_manager = None
        self.command_tracker = None

    # ------------------------------------------------------------------
    # Client App
    # ------------------------------------------------------------------

    async def register_client(
        self,
        machine_id: str,
        websocket,
        machine_info: dict,
    ):
        """
        Đăng ký Client App sau khi xác thực thành công.
        Lưu websocket và cập nhật MachineRegistry.
        Notify Web App machine online.
        """
        self._client_sockets[machine_id] = websocket
        self.registry.register(
            machine_id=machine_id,
            hostname=machine_info.get("hostname", "unknown"),
            ip_address=machine_info.get("ipAddress", "unknown"),
        )
        logger.info("Client registered: machineId='%s'", machine_id)
        await self._notify_machine_status(machine_id, "online")

    async def unregister_client(self, machine_id: str):
        """
        Hủy đăng ký Client App khi mất kết nối.
        Xóa websocket, cập nhật registry, notify Web App offline.
        """
        if machine_id in self._client_sockets:
            del self._client_sockets[machine_id]
            self.registry.unregister(machine_id)
            logger.info("Client unregistered: machineId='%s'", machine_id)
            await self._notify_machine_status(machine_id, "offline")

    async def send_to_machine(self, machine_id: str, message: dict) -> bool:
        """
        Gửi message đến một Client App cụ thể.

        Returns:
            True nếu gửi thành công.
            False nếu machine không online hoặc gửi thất bại.
        """
        if not self.registry.is_online(machine_id):
            logger.warning(
                "Cannot send to '%s': machine is offline or not found", machine_id
            )
            return False

        websocket = self._client_sockets.get(machine_id)
        if websocket is None:
            logger.warning(
                "Cannot send to '%s': no active socket (registry/socket mismatch)", machine_id
            )
            return False

        try:
            await websocket.send(json.dumps(message))
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Socket closed while sending to '%s'", machine_id)
            # Dọn dẹp stale entry
            await self.unregister_client(machine_id)
            return False

    def touch_machine(self, machine_id: str):
        """Cập nhật lastSeen — gọi mỗi khi nhận message từ machine."""
        self.registry.touch(machine_id)

    def remove_client_socket(self, machine_id: str) -> object | None:
        """
        Xóa và trả về socket của machine khỏi _client_sockets.
        Dùng bởi HeartbeatManager để dọn socket stale mà không cần
        truy cập trực tiếp vào attribute private.

        Returns:
            WebSocket object nếu tồn tại, None nếu không có.
        """
        return self._client_sockets.pop(machine_id, None)

    # ------------------------------------------------------------------
    # Web App
    # ------------------------------------------------------------------

    async def register_webapp(self, websocket):
        """
        Đăng ký Web App sau khi xác thực thành công.
        Nếu đã có kết nối cũ thì đóng lại trước.
        """
        if self._webapp_socket is not None:
            logger.warning("New Web App connection — closing existing session")
            try:
                await self._webapp_socket.close(code=4000, reason="Replaced by new connection")
            except Exception:
                pass

        self._webapp_socket = websocket
        logger.info("Web App registered")

    async def unregister_webapp(self):
        """Hủy đăng ký Web App khi mất kết nối."""
        self._webapp_socket = None
        logger.info("Web App unregistered")

    async def send_to_webapp(self, message: dict) -> bool:
        """
        Gửi message đến Web App.

        Returns:
            True nếu gửi thành công.
            False nếu Web App không kết nối.
        """
        if self._webapp_socket is None:
            logger.warning("Cannot send to Web App: not connected")
            return False

        try:
            await self._webapp_socket.send(json.dumps(message))
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Socket closed while sending to Web App")
            await self.unregister_webapp()
            return False

    # ------------------------------------------------------------------
    # Machine Registry queries (convenience wrappers)
    # ------------------------------------------------------------------

    def get_online_machines(self) -> list[dict]:
        """Trả về danh sách machines đang online."""
        return self.registry.get_online()

    def get_all_machines(self) -> list[dict]:
        """Trả về tất cả machines (online + offline)."""
        return self.registry.get_all()

    def is_machine_online(self, machine_id: str) -> bool:
        return self.registry.is_online(machine_id)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _notify_machine_status(self, machine_id: str, status: str):
        """
        Gửi event machine.status về Web App khi machine online/offline.
        Web App dùng event này để cập nhật dashboard realtime.
        """
        info = self.registry.get(machine_id)
        event = make_message(
            msg_type="machine.status",
            payload={
                "machineId": machine_id,
                "status": status,
                "hostname": info.hostname if info else "unknown",
                "ipAddress": info.ip_address if info else "unknown",
                "lastSeen": int(info.last_seen) if info else 0,
            },
            destination="webapp",
        )
        await self.send_to_webapp(event)
