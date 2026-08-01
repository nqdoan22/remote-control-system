"""
===============================================================================
FILE: web-app/backend/core/ws_connection_manager.py
PURPOSE: Quản lý kết nối WebSocket từ Browser (Admin) và định tuyến tin nhắn
         giữa Browser <-> Gateway.
ARCHITECTURE ROLE:
  - Đóng vai trò "Cầu nối" (Bridge) giữa Browser và Gateway Server.
  - Mỗi Browser kết nối tới /ws sẽ có 1 hàng đợi (asyncio.Queue) riêng để
    nhận tin nhắn từ Gateway, tránh làm nghẽn vòng lặp lắng nghe chung.
  - Định tuyến tin nhắn broadcast theo máy (machine_id) để tránh lộ
    luồng dữ liệu (frame màn hình/webcam) sang các Admin đang xem máy khác.
===============================================================================
"""

import asyncio
import logging
from typing import Dict, Optional
from fastapi import WebSocket

logger = logging.getLogger("WSConnectionManager")


class WSConnectionManager:
    """
    Lớp quản lý tập trung các kết nối WebSocket Browser.
    Cấu trúc: { websocket: {"machine_id": str, "queue": asyncio.Queue} }
    """

    def __init__(self):
        self._connections: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, machine_id: str) -> asyncio.Queue:
        """Chấp nhận kết nối Browser và trả về hàng đợi nhận tin từ Gateway."""
        await websocket.accept()
        queue: asyncio.Queue = asyncio.Queue()
        self._connections[websocket] = {"machine_id": machine_id or "", "queue": queue}
        logger.info(
            f"[WS Bridge] Browser kết nối, target machine_id='{machine_id}' | "
            f"Tổng kết nối: {len(self._connections)}"
        )
        return queue

    def disconnect(self, websocket: WebSocket) -> None:
        """Gỡ Browser ra khỏi danh sách quản lý khi ngắt kết nối."""
        info = self._connections.pop(websocket, None)
        if info:
            logger.info(
                f"[WS Bridge] Browser ngắt kết nối, machine_id='{info['machine_id']}' | "
                f"Còn lại: {len(self._connections)}"
            )

    def get_queue(self, websocket: WebSocket) -> Optional[asyncio.Queue]:
        """Lấy hàng đợi nhận tin của một Browser cụ thể."""
        info = self._connections.get(websocket)
        return info["queue"] if info else None

    def get_queues_for_machine(self, machine_id: str):
        """Lấy hàng đợi của các Browser đang xem một máy Agent cụ thể."""
        if not machine_id:
            return []
        return [
            info["queue"]
            for info in self._connections.values()
            if info["machine_id"] == machine_id
        ]

    def get_all_queues(self):
        """Lấy hàng đợi của TẤT CẢ Browser đang kết nối."""
        return [info["queue"] for info in self._connections.values()]

    def push_to_queues(self, queues, message_json: str) -> None:
        """Đẩy chuỗi JSON vào các hàng đợi đã chỉ định (Non-blocking)."""
        for queue in queues:
            try:
                queue.put_nowait(message_json)
            except Exception as e:
                logger.error(f"[WS Bridge] Lỗi đẩy tin nhắn vào hàng đợi Browser: {e}")


# Singleton Instance dùng chung toàn hệ thống
ws_connection_manager = WSConnectionManager()
