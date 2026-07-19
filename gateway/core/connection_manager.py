# gateway/core/connection_manager.py
import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Gateway.ConnectionManager")

class ConnectionManager:
    """Quản lý tập trung các kết nối vật lý WebSocket trong mạng LAN."""
    
    def __init__(self):
        # Lưu các máy trạm: { machine_id: {"websocket": ws, "last_seen": timestamp, "status": "online"} }
        self.active_agents = {}
        # Lưu kết nối từ Web App Backend (hỗ trợ nhiều kết nối nếu Web App mở rộng)
        self.webapp_connections = set()

    async def register_webapp(self, websocket):
        """Đăng ký kết nối từ Web App Backend."""
        self.webapp_connections.add(websocket)
        logger.info(f"🟢 Web App Backend đã kết nối vào Gateway. Tổng số: {len(self.webapp_connections)}")

    async def unregister_webapp(self, websocket):
        """Hủy đăng ký kết nối Web App khi ngắt socket."""
        if websocket in self.webapp_connections:
            self.webapp_connections.remove(websocket)
            logger.info("🛑 Web App Backend đã ngắt kết nối khỏi Gateway.")

    async def register_agent(self, machine_id: str, websocket):
        """Đăng ký thiết bị Agent sau khi xác thực thành công."""
        self.active_agents[machine_id] = {
            "websocket": websocket,
            "last_seen": time.time(),
            "status": "online"
        }
        logger.info(f"🖥️ Agent [{machine_id}] đăng ký thành công vào hệ thống.")
        await self.broadcast_status_to_webapp(machine_id, "online")

    async def unregister_agent(self, machine_id: str):
        """Loại bỏ Agent khỏi Registry khi mất kết nối."""
        if machine_id in self.active_agents:
            self.active_agents.pop(machine_id)
            logger.warn(f"💥 Agent [{machine_id}] đã mất kết nối hoặc bị ngắt bỏ.")
            await self.broadcast_status_to_webapp(machine_id, "offline")

    def update_heartbeat(self, machine_id: str):
        """Cập nhật thời gian tương tác cuối cùng để tính toán trạng thái Live/Dead."""
        if machine_id in self.active_agents:
            self.active_agents[machine_id]["last_seen"] = time.time()
            logger.debug(f"💓 Nhận Heartbeat từ {machine_id}")

    def get_agent_socket(self, machine_id: str):
        """Lấy socket vật lý để gửi lệnh."""
        agent_info = self.active_agents.get(machine_id)
        if agent_info and agent_info["status"] == "online":
            return agent_info["websocket"]
        return None

    async def broadcast_status_to_webapp(self, machine_id: str, status: str):
        """Thông báo thời gian thực về Web App khi có máy Online/Offline."""
        import json
        notification = {
            "type": "machine.status_change",
            "timestamp": int(time.time()),
            "payload": {
                "machineId": machine_id,
                "status": status
            }
        }
        dead_sockets = set()
        for ws in self.webapp_connections:
            try:
                await ws.send(json.dumps(notification))
            except Exception:
                dead_sockets.add(ws)
                
        for ws in dead_sockets:
            await self.unregister_webapp(ws)