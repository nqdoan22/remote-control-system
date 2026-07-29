# web-app/backend/core/gateway_client.py
import json
import logging
import asyncio
import uuid
import websockets
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger("GatewayClient")

class GatewayClient:
    """
    Lớp hỗ trợ FastAPI Backend gửi lệnh tới Gateway qua giao thức WebSocket.
    """
    def __init__(self):
        self.ws_url = settings.GATEWAY_WS_URL

    async def send_command(self, machine_id: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Gửi lệnh điều khiển tới một Máy trạm (Machine) cụ thể thông qua Gateway.
        Đợi phản hồi thực tế từ Agent thay vì return ngay lập tức.
        """
        if payload is None:
            payload = {}

        message_id = str(uuid.uuid4())
        command_packet = {
            "messageId": message_id,
            "type": action,
            "source": "webapp",
            "destination": machine_id,
            "timestamp": int(asyncio.get_event_loop().time()),
            "payload": payload
        }

        try:
            async with websockets.connect(self.ws_url, timeout=10) as ws:
                auth_packet = {
                    "type": "system.auth",
                    "source": "webapp",
                    "payload": {"secret": settings.AGENT_SECRET_KEY}
                }
                await ws.send(json.dumps(auth_packet))
                _ = await ws.recv()

                logger.info(f"📤 Gửi lệnh '{action}' tới máy '{machine_id}'...")
                await ws.send(json.dumps(command_packet))

                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    resp = json.loads(raw)
                    if resp.get("messageId") == message_id:
                        return resp.get("payload", {"success": False, "error": "Empty response"})

        except asyncio.TimeoutError:
            logger.error(f"⏳ Timeout chờ phản hồi từ Agent '{machine_id}' cho lệnh '{action}'")
            return {"success": False, "error": "Agent response timeout"}
        except Exception as e:
            logger.error(f"❌ Lỗi kết nối Gateway: {e}")
            return {"success": False, "error": f"Gateway connection error: {str(e)}"}

gateway_client = GatewayClient()