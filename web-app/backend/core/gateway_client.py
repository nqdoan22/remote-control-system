# web-app/backend/core/gateway_client.py
import json
import logging
import asyncio
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
        
        Parameters:
        - machine_id: UUID của máy bị điều khiển (đích)
        - action: Tên chức năng (VD: 'process.list', 'webcam.start', 'power.shutdown')
        - payload: Các tham số truyền kèm (VD: {"pid": 1234})
        """
        if payload is None:
            payload = {}

        # Đóng gói thông điệp theo chuẩn communication_protocol.md
        command_packet = {
            "messageId": f"cmd-{asyncio.get_event_loop().time()}",
            "type": action,
            "source": "webapp",
            "destination": machine_id,
            "payload": payload
        }

        try:
            # Mở kết nối tạm thời tới Gateway để bắn lệnh
            async with websockets.connect(self.ws_url, timeout=5) as ws:
                # 1. Gửi gói tin Xác thực vai trò 'webapp'
                auth_packet = {
                    "type": "system.auth",
                    "source": "webapp",
                    "payload": {"secret": settings.AGENT_SECRET_KEY}
                }
                await ws.send(json.dumps(auth_packet))
                
                # Đọc phản hồi xác thực từ Gateway
                _ = await ws.recv()

                # 2. Gửi lệnh chính thức tới Agent
                logger.info(f"📤 Gửi lệnh '{action}' tới máy '{machine_id}' qua Gateway...")
                await ws.send(json.dumps(command_packet))
                
                return {"success": True, "message": "Command sent to Gateway"}

        except Exception as e:
            logger.error(f"❌ Không thể kết nối tới Gateway WebSocket tại {self.ws_url}: {e}")
            return {"success": False, "error": f"Gateway connection error: {str(e)}"}

# Khởi tạo một đối tượng duy nhất
gateway_client = GatewayClient()