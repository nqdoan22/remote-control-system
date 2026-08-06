"""
core/machine_registry.py — Lưu trạng thái của các Client App đang kết nối.

Theo system_specification.md, mỗi machine cần expose:
  - machineId, hostname, ipAddress, status (online/offline), lastSeen
"""

import time
import logging

logger = logging.getLogger("gateway.machine_registry")


class MachineInfo:
    """Thông tin và trạng thái của một Client App."""

    __slots__ = ("machine_id", "hostname", "ip_address", "status", "last_seen")

    def __init__(self, machine_id: str, hostname: str, ip_address: str):
        self.machine_id: str = machine_id
        self.hostname: str = hostname
        self.ip_address: str = ip_address
        self.status: str = "online"
        self.last_seen: float = time.time()

    def touch(self):
        """Cập nhật last_seen — gọi mỗi khi nhận được heartbeat hoặc message."""
        self.last_seen = time.time()

    def set_offline(self):
        self.status = "offline"

    def set_online(self):
        self.status = "online"
        self.touch()

    def to_dict(self) -> dict:
        """Serialize sang dict để gửi qua WebSocket (machine.list response)."""
        return {
            "machineId": self.machine_id,
            "hostname": self.hostname,
            "ipAddress": self.ip_address,
            "status": self.status,
            "lastSeen": int(self.last_seen),
        }


class MachineRegistry:
    """
    Quản lý danh sách MachineInfo.

    Tách biệt khỏi ConnectionManager để có thể test độc lập
    và dễ thay thế storage backend sau này.
    """

    def __init__(self):
        # machineId -> MachineInfo
        self._machines: dict[str, MachineInfo] = {}

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def register(self, machine_id: str, hostname: str, ip_address: str) -> MachineInfo:
        """Đăng ký machine mới hoặc cập nhật nếu đã tồn tại."""
        if machine_id in self._machines:
            # Reconnect — cập nhật lại info và đánh dấu online
            info = self._machines[machine_id]
            info.hostname = hostname
            info.ip_address = ip_address
            info.set_online()
            logger.info("Machine '%s' reconnected (hostname='%s')", machine_id, hostname)
        else:
            info = MachineInfo(machine_id, hostname, ip_address)
            self._machines[machine_id] = info
            logger.info(
                "Machine '%s' registered (hostname='%s', ip='%s')",
                machine_id, hostname, ip_address,
            )
        return info

    def unregister(self, machine_id: str):
        """Đánh dấu machine offline khi mất kết nối (giữ lại record để hiển thị lastSeen)."""
        if machine_id in self._machines:
            self._machines[machine_id].set_offline()
            logger.info("Machine '%s' marked offline", machine_id)

    def touch(self, machine_id: str):
        """Cập nhật lastSeen — gọi khi nhận heartbeat hoặc bất kỳ message nào."""
        if machine_id in self._machines:
            self._machines[machine_id].touch()

    def mark_offline_if_stale(self, timeout_seconds: float) -> list[str]:
        """
        Quét tất cả machines, đánh dấu offline nếu lastSeen vượt quá timeout.
        Dùng bởi HeartbeatManager (Phase 5).

        Returns:
            Danh sách machineId vừa bị đánh dấu offline.
        """
        now = time.time()
        newly_offline: list[str] = []
        for machine_id, info in self._machines.items():
            if info.status == "online" and (now - info.last_seen) > timeout_seconds:
                info.set_offline()
                logger.warning(
                    "Machine '%s' timed out (last seen %.0fs ago)",
                    machine_id, now - info.last_seen,
                )
                newly_offline.append(machine_id)
        return newly_offline

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, machine_id: str) -> MachineInfo | None:
        return self._machines.get(machine_id)

    def is_online(self, machine_id: str) -> bool:
        info = self._machines.get(machine_id)
        return info is not None and info.status == "online"

    def get_all_ids(self) -> list[str]:
        """Trả về danh sách machineId của tất cả machines đã đăng ký."""
        return list(self._machines.keys())

    def get_all(self) -> list[dict]:
        """Trả về danh sách tất cả machines (online + offline) dạng dict."""
        return [info.to_dict() for info in self._machines.values()]

    def get_online(self) -> list[dict]:
        """Trả về danh sách machines đang online."""
        return [
            info.to_dict()
            for info in self._machines.values()
            if info.status == "online"
        ]
