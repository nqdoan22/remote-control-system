import json
import logging
import os
import time
from websockets.server import WebSocketServerProtocol
from core.connection_manager import manager

logger = logging.getLogger("MessageHandler")

AGENT_SECRET_KEY = os.getenv("AGENT_SECRET_KEY", "d8e8fca2dc0f896fd7cb4cb0031ba249")

async def handle_incoming_message(websocket: WebSocketServerProtocol, raw_message: str):
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
        machine_secret = payload.get("machineSecret")

        if source and not source.startswith("webapp"):
            if machine_secret == AGENT_SECRET_KEY:
                await manager.register_agent(source, websocket, {
                    "hostname": payload.get("hostname", source),
                    "ip_address": payload.get("ip_address", "")
                })
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
    # 2. XỬ LÝ machine.list - TRẢ VỀ DANH SÁCH MÁY
    # ==========================================
    if msg_type == "machine.list":
        machines = []
        for machine_id in manager.active_agents:
            info = manager.agent_info.get(machine_id, {})
            machines.append({
                "machineId": machine_id,
                "hostname": info.get("hostname", machine_id),
                "ipAddress": info.get("ip_address", ""),
                "status": "online",
                "lastSeen": int(time.time())
            })
        response = {
            "messageId": message_id,
            "type": "response",
            "source": "gateway",
            "destination": source,
            "payload": {"success": True, "data": {"machines": machines}}
        }
        await websocket.send(json.dumps(response))
        return

    # ==========================================
    # 3. XỬ LÝ ĐỊNH TUYẾN THÔNG ĐIỆP (ROUTING)
    # ==========================================
    
    if destination and destination != "gateway" and destination != "webapp":
        success = await manager.send_to_agent(destination, raw_message)
        if not success:
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

    else:
        await manager.broadcast_to_webapps(raw_message)