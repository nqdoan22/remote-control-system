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
      "type": "system.auth | process.list | ...",
      "source": "webapp | client-01",
      "destination": "gateway | client-01 | webapp",
      "payload": { ... }
    }
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
    # 1. XỬ LÝ XÁC THỰC KẾT NỐI (system.auth)
    # ==========================================
    if msg_type == "system.auth":
        # Xác thực từ Client Agent
        if source and source.startswith("client"):
            machine_secret = payload.get("machineSecret")
            if machine_secret == AGENT_SECRET_KEY:
                await manager.register_agent(source, websocket)
                # Gửi phản hồi thành công về cho Agent
                response = {
                    "messageId": message_id,
                    "type": "response",
                    "source": "gateway",
                    "destination": source,
                    "payload": {"success": True, "data": {"message": "Authenticated successfully"}}
                }
                await websocket.send(json.dumps(response))
            else:
                logger.warning(f"❌ Agent '{source}' xác thực thất bại! Sai machineSecret.")
                await websocket.close(1008, "Policy Violation: Authentication Failed")

        # Xác thực từ Web App / Backend
        elif source == "webapp":
            await manager.register_webapp(websocket)
            response = {
                "messageId": message_id,
                "type": "response",
                "source": "gateway",
                "destination": "webapp",
                "payload": {"success": True, "data": {"message": "Web App Authenticated"}}
            }
            await websocket.send(json.dumps(response))
        return

    # ==========================================
    # 2. XỬ LÝ ĐỊNH TUYẾN THÔNG ĐIỆP (ROUTING)
    # ==========================================
    
    # Trường hợp 2.1: Tin nhắn gửi ĐẾN một Máy Client cụ thể (Lệnh từ Web App)
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