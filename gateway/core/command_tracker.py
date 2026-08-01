"""
core/command_tracker.py — Phát hiện TIMEOUT khi Client App không phản hồi lệnh.

Theo api_contract.md, mỗi Request phải có đúng một Response, và error code
`TIMEOUT` được dùng khi "Client App không phản hồi trong thời gian quy định".
Trước đây Gateway forward lệnh xuống Client App theo kiểu fire-and-forget,
không có cơ chế nào tạo ra mã lỗi này.

Giới hạn thiết kế:
  Message `response`/`error` theo api_contract.md không mang originalMessageId
  (chỉ error response mới có field này), nên Gateway không thể correlate chính
  xác từng response với từng command nếu nhiều command cùng in-flight tới cùng
  một machine. Vì vậy module này theo dõi tối đa MỘT command đang chờ phản hồi
  cho mỗi machine tại một thời điểm — khớp với mô hình request/response tuần tự
  mà api_contract.md mô tả. Nếu một command mới được forward trong khi command
  trước đó chưa có phản hồi, command cũ được xem là đã bị thay thế (không báo
  TIMEOUT giả cho nó nữa).
"""

import asyncio
import logging

logger = logging.getLogger("gateway.command_tracker")


class CommandTracker:
    """Theo dõi command đang chờ phản hồi từ Client App, mỗi machine tối đa một command."""

    def __init__(self):
        # machineId -> (messageId, asyncio.Event)
        self._pending: dict[str, tuple[str, asyncio.Event]] = {}

    def track(self, machine_id: str, message_id: str) -> asyncio.Event:
        """
        Đăng ký một command đang chờ phản hồi.
        Nếu machine đã có command khác đang chờ, coi như bị thay thế —
        unblock waiter cũ để nó không báo TIMEOUT giả.
        """
        old = self._pending.get(machine_id)
        if old is not None:
            old[1].set()

        event = asyncio.Event()
        self._pending[machine_id] = (message_id, event)
        return event

    def resolve(self, machine_id: str) -> None:
        """Gọi khi nhận được response/error từ machine — unblock waiter đang chờ."""
        entry = self._pending.get(machine_id)
        if entry is not None:
            entry[1].set()

    def clear(self, machine_id: str, message_id: str) -> None:
        """Dọn entry sau khi wait kết thúc, chỉ nếu vẫn là entry của command này."""
        entry = self._pending.get(machine_id)
        if entry is not None and entry[0] == message_id:
            del self._pending[machine_id]
