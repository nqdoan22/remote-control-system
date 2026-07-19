# web-app/backend/core/gateway_client.py
import asyncio
import websockets
import json
import uuid
import time

class GatewayClient:
    """Quản lý kết nối từ Web App Backend tới Gateway."""

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self.websocket = None
        self.pending_responses = {} 
        self.listen_task = None

    async def connect(self):
        try:
            # Backend Web App kết nối tới Gateway qua endpoint /webapp
            self.websocket = await websockets.connect(f"{self.gateway_url}/webapp")
            self.listen_task = asyncio.create_task(self._listen_loop())
        except Exception as e:
            print(f"❌ Kết nối Gateway thất bại: {e}")

    async def _listen_loop(self):
        """Vòng lặp lắng nghe phản hồi."""
        try:
            async for message in self.websocket:
                response_data = json.loads(message)
                # Đọc định danh theo chuẩn camelCase của Protocol: messageId[cite: 15, 18].
                msg_id = response_data.get("messageId")
                
                if msg_id and msg_id in self.pending_responses:
                    future = self.pending_responses[msg_id]
                    if not future.done():
                        future.set_result(response_data)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def send_command_and_wait(self, machine_id: str, msg_type: str, payload: dict = {}, timeout: int = 10):
        if not self.websocket:
            raise Exception("Chưa kết nối tới Gateway WebSocket!")

        message_id = str(uuid.uuid4())
        
        # Thiết lập gói tin tuân thủ cấu trúc chuẩn: messageId, type, timestamp, source, destination, payload[cite: 18].
        message = {
            "messageId": message_id,
            "type": msg_type,           # Tên message sử dụng quy tắc module.action[cite: 18].
            "timestamp": int(time.time()),
            "source": "webapp",         # Nguồn gửi là webapp[cite: 18].
            "destination": machine_id,  # Đích đến là machine_id của Client App[cite: 18].
            "payload": payload
        }

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_responses[message_id] = future

        try:
            await self.websocket.send(json.dumps(message))
            response = await asyncio.wait_for(future, timeout=timeout)
            
            # Xử lý các mã lỗi hệ thống (Standard Error Codes) như PERMISSION_DENIED, TIMEOUT[cite: 18].
            if response.get("type") == "error":
                err_payload = response.get("payload", {})
                raise Exception(f"[{err_payload.get('code')}] {err_payload.get('message')}")
                
            return response.get("payload", {})
        
        except asyncio.TimeoutError:
            raise Exception(f"⏰ Lỗi TIMEOUT: Hết thời gian chờ phản hồi[cite: 18].")
        finally:
            self.pending_responses.pop(message_id, None)

gateway_client = GatewayClient("ws://localhost:8765")