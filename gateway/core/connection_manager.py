# gateway/core/connection_manager.py
import json
import logging
from typing import Dict, Set, Optional
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger("ConnectionManager")

class ConnectionManager:
    def __init__(self):
        self.active_agents: Dict[str, WebSocketServerProtocol] = {}
        self.agent_info: Dict[str, dict] = {}
        self.web_apps: Set[WebSocketServerProtocol] = set()

    async def register_agent(self, machine_id: str, websocket: WebSocketServerProtocol, info: Optional[dict] = None):
        self.active_agents[machine_id] = websocket
        if info:
            self.agent_info[machine_id] = info
        logger.info(f"Agent da ket noi & dang ky: machine_id='{machine_id}' (Tong Agent: {len(self.active_agents)})")

    def unregister_agent(self, websocket: WebSocketServerProtocol) -> Optional[str]:
        disconnected_id = None
        for machine_id, ws in list(self.active_agents.items()):
            if ws == websocket:
                disconnected_id = machine_id
                del self.active_agents[machine_id]
                self.agent_info.pop(machine_id, None)
                logger.info(f"Agent da ngat ket noi: machine_id='{disconnected_id}' (Con lai: {len(self.active_agents)})")
                break
        return disconnected_id

    # ==========================================
    # QUẢN LÝ KẾT NỐI WEB APP (ADMIN)
    # ==========================================
    async def register_webapp(self, websocket: WebSocketServerProtocol):
        """Đăng ký kết nối từ Web App Admin / Backend."""
        self.web_apps.add(websocket)
        logger.info(f"Web App ket noi thanh cong (Tong WebApp: {len(self.web_apps)})")

    def unregister_webapp(self, websocket: WebSocketServerProtocol):
        """Hủy kết nối Web App."""
        if websocket in self.web_apps:
            self.web_apps.remove(websocket)
            logger.info(f"Web App ngat ket noi (Con lai: {len(self.web_apps)})")

    # ==========================================
    # CHUYỂN TIẾP THÔNG ĐIỆP (MESSAGE ROUTING)
    # ==========================================
    async def send_to_agent(self, machine_id: str, message_str: str) -> bool:
        """Gửi lệnh từ Web App đến một Agent cụ thể."""
        agent_ws = self.active_agents.get(machine_id)
        if agent_ws:
            try:
                await agent_ws.send(message_str)
                return True
            except Exception as e:
                logger.error(f"Lỗi khi gửi dữ liệu tới Agent '{machine_id}': {e}")
                return False
        else:
            logger.warning(f"Khong tim thay Agent '{machine_id}' trong danh sach Online!")
            return False

    async def broadcast_to_webapps(self, message_str: str):
        """Chuyển tiếp phản hồi / stream / event từ Agent về cho tất cả Web App đang lắng nghe."""
        if not self.web_apps:
            return
        
        # Tạo danh sách các socket bị lỗi để dọn dẹp sau khi gửi
        dead_sockets = set()
        for ws in self.web_apps:
            try:
                await ws.send(message_str)
            except Exception as e:
                logger.error(f"Lỗi gửi dữ liệu về Web App: {e}")
                dead_sockets.add(ws)

        # Xóa các socket die
        for ws in dead_sockets:
            self.unregister_webapp(ws)

# Khởi tạo một Instance duy nhất (Singleton Pattern)
manager = ConnectionManager()