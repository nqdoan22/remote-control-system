# gateway/core/connection_manager.py
import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Gateway.ConnectionManager")

class ConnectionManager:
    """Gateway là trung tâm giao tiếp, quản lý toàn bộ kết nối WebSocket[cite: 14, 16]."""
    
    def __init__(self):
        # Lưu các máy trạm, phục vụ Machine Registry[cite: 16].
        self.active_agents = {}
        self.webapp_connections = set()

    async def register_webapp(self, websocket):
        self.webapp_connections.add(websocket)

    async def unregister_webapp(self, websocket):
        if websocket in self.webapp_connections:
            self.webapp_connections.remove(websocket)

    async def register_agent(self, machine_id: str, websocket):
        # Client App phải được xác thực trước khi tham gia vào Machine Registry[cite: 14, 18].
        self.active_agents[machine_id] = {
            "websocket": websocket,
            "last_seen": time.time(),
            "status": "online" # Hệ thống phải hiển thị trạng thái Online/Offline[cite: 13, 14].
        }
        await self.broadcast_status_to_webapp(machine_id, "online")

    async def unregister_agent(self, machine_id: str):
        if machine_id in self.active_agents:
            self.active_agents.pop(machine_id)
            await self.broadcast_status_to_webapp(machine_id, "offline")

    def update_heartbeat(self, machine_id: str):
        # Gateway giám sát trạng thái kết nối thông qua Heartbeat để cập nhật Online/Offline[cite: 17, 18].
        if machine_id in self.active_agents:
            self.active_agents[machine_id]["last_seen"] = time.time()

    def get_agent_socket(self, machine_id: str):
        agent_info = self.active_agents.get(machine_id)
        if agent_info and agent_info["status"] == "online":
            return agent_info["websocket"]
        return None

    async def broadcast_status_to_webapp(self, machine_id: str, status: str):
        # Bắn Event thông báo trạng thái Machine về Web App bằng cấu trúc chuẩn[cite: 18].
        import json
        notification = {
            "messageId": f"evt-{int(time.time())}",
            "type": "machine.status_change",
            "timestamp": int(time.time()),
            "source": "gateway",
            "destination": "webapp",
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