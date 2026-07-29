# gateway/handlers/message_handler.py
import json
import logging
from websockets.server import WebSocketServerProtocol
from core.connection_manager import manager

logger = logging.getLogger("MessageHandler")

# Mã Secret tĩnh dùng để xác thực Agent đơn giản (Sẽ khớp với config.py của Client Agent)
AGENT_SECRET_KEY = "d8e8fca2dc0f896fd7cb4cb0031ba249"

async def handle_incoming_message(websocket: WebSocketServerProtocol, raw_message: str):
    """
    Xử lý mọi thông điệp WebSocket đi vào Gateway.
    Cấu trúc Message chuẩn:
    {
      "messageId": "uuid",
      "type": "system.auth | system.register | process.list | ...",
      "source": "webapp | client-01 | mac-XXXX",
      "destination": "gateway | client-01 | mac-XXXX | webapp",
      "payload": { ... }
    }
    Ghi chú: Gateway chấp nhận cả "system.auth" (Backend) và "system.register" (Client App)
    để xác thực kết nối. Source của Agent có thể là "client-XX" hoặc "mac-XXXX".
    """
    try:
        data = json.loads(raw_message)
        msg_type = data.get("type")
        source = data.get("source")
        destination = data.get("destination")
        payload = data.get("payload", {})
        message_id = data.get("messageId")

    except json.JSONDecodeError:
        logger.error("Dữ liệu nhận được không đúng định dạng JSON!")
        return

    # ==========================================
    # 1. XỬ LÝ XÁC THỰC KẾT NỐI (system.auth / system.register)
    # ==========================================
    # Client gửi "system.register", Backend gửi "system.auth", Gateway chấp nhận cả hai
    if msg_type in ("system.auth", "system.register"):
        # Xác thực từ Client Agent
        # Backend cũ gửi source="client-XX", Client App mới gửi source="mac-XXXX"
        if source and source != "webapp":
            # Client cũ gửi "machineSecret", Client mới gửi "secret" — check cả hai
            machine_secret = payload.get("machineSecret") or payload.get("secret")
            if machine_secret == AGENT_SECRET_KEY:
                await manager.register_agent(source, websocket)
                response = {
                    "messageId": message_id,
                    "type": "response",
                    "source": "gateway",
                    "destination": source,
                    "payload": {"success": True, "data": {"message": "Authenticated successfully"}}
                }
                await websocket.send(json.dumps(response))
            else:
                logger.warning(f"Agent '{source}' xác thực thất bại! Sai machineSecret.")
                await websocket.close(1008, "Policy Violation: Authentication Failed")

        # Xác thực từ Web App / Backend
        elif source == "webapp":
            webapp_secret = payload.get("secret") or payload.get("token")
            if webapp_secret == AGENT_SECRET_KEY:
                await manager.register_webapp(websocket)
                response = {
                    "messageId": message_id,
                    "type": "response",
                    "source": "gateway",
                    "destination": "webapp",
                    "payload": {"success": True, "data": {"message": "Web App Authenticated"}}
                }
                await websocket.send(json.dumps(response))
            else:
                logger.warning(f"Web App xác thực thất bại! Sai secret.")
                await websocket.close(1008, "Policy Violation: Authentication Failed")
        return

    # ==========================================
    # 2. XỬ LÝ CÁC LỆNH HỆ THỐNG (machine.list, ...)
    # ==========================================

    if msg_type == "machine.list":
        machines = [
            {
                "machineId": mid,
                "hostname": mid,
                "ipAddress": "N/A",
                "status": "online",
                "lastSeen": None
            }
            for mid in manager.active_agents.keys()
        ]
        response = {
            "messageId": message_id,
            "type": "response",
            "source": "gateway",
            "destination": source,
            "payload": {
                "success": True,
                "data": {"machines": machines}
            }
        }
        await websocket.send(json.dumps(response))
        return

    # ==========================================
    # 3. XỬ LÝ ĐỊNH TUYẾN THÔNG ĐIỆP (ROUTING)
    # ==========================================
    
    # Trường hợp 3.1: Tin nhắn gửi ĐẾN một Máy Client cụ thể (Lệnh từ Web App)
    if destination and destination != "gateway" and destination != "webapp":
        success = await manager.send_to_agent(destination, raw_message)
        if not success:
            # Nếu gửi thất bại (Agent Offline), báo lỗi về cho Web App
            error_response = {
                "messageId": message_id,
                "type": "error",
                "source": "gateway",
                "destination": source,
                "payload": {
                    "code": "MACHINE_OFFLINE",
                    "message": f"Target machine '{destination}' is offline or not found."
                }
            }
            await websocket.send(json.dumps(error_response))

    # Trường hợp 2.2: Phản hồi hoặc Luồng dữ liệu (Stream/Heartbeat) TỪ Agent GỬI VỀ Web App
    else:
        # Tự động gửi về tất cả các Web App Client đang lắng nghe
        await manager.broadcast_to_webapps(raw_message)