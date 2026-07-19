# web-app/backend/core/gateway_client.py
import asyncio
import websockets
import json
import uuid
import time

class GatewayClient:
    """Quản lý kết nối từ Web App Backend tới Gateway qua WebSocket chuẩn hóa."""

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self.websocket = None
        self.pending_responses = {}  # Lưu trữ các request đang đợi Agent trả lời bằng messageId
        self.listen_task = None

    async def connect(self):
        """Thiết lập kết nối và chạy loop lắng nghe dữ liệu trả về từ Gateway."""
        try:
            self.websocket = await websockets.connect(f"{self.gateway_url}/webapp")
            print(f"🔌 Connected to Gateway at {self.gateway_url}")
            self.listen_task = asyncio.create_task(self._listen_loop())
        except Exception as e:
            print(f"❌ Failed to connect to Gateway: {e}")

    async def _listen_loop(self):
        """Vòng lặp lắng nghe liên tục phản hồi từ Gateway theo chuẩn Protocol mới."""
        try:
            async for message in self.websocket:
                response_data = json.loads(message)
                # Đọc định danh theo chuẩn trường messageId mới (camelCase)
                msg_id = response_data.get("messageId")
                
                if msg_id and msg_id in self.pending_responses:
                    future = self.pending_responses[msg_id]
                    if not future.done():
                        future.set_result(response_data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection to Gateway closed.")

    async def send_command_and_wait(self, machine_id: str, msg_type: str, payload: dict = {}, timeout: int = 10):
        """Gửi lệnh xuống một máy theo đúng cấu trúc JSON quy định trong tài liệu thiết kế."""
        if not self.websocket:
            raise Exception("Chưa kết nối tới Gateway WebSocket!")

        # Tạo messageId duy nhất theo chuẩn cấu trúc chung
        message_id = str(uuid.uuid4())
        
        # Thiết lập gói tin tuân thủ tuyệt đối quy ước đặt tên trường camelCase và cấu trúc Protocol
        message = {
            "messageId": message_id,
            "type": msg_type,           # Định dạng dạng "module.action"
            "timestamp": int(time.time()),
            "source": "webapp",
            "destination": machine_id,  # Máy đích nhận lệnh
            "payload": payload          # Dữ liệu đi kèm lệnh
        }

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_responses[message_id] = future

        try:
            # Truyền gói tin qua mạng LAN xuống Gateway
            await self.websocket.send(json.dumps(message))
            
            # Chờ Agent phản hồi trong giới hạn giây (timeout)
            response = await asyncio.wait_for(future, timeout=timeout)
            
            # TƯ DUY BẢO MẬT: Xử lý và bóc tách lỗi hệ thống chuẩn hóa nếu đầu Agent/Gateway từ chối
            if response.get("type") == "error":
                err_payload = response.get("payload", {})
                raise Exception(f"[{err_payload.get('code')}] {err_payload.get('message')}")
                
            return response.get("payload", {})  # Trả về payload kết quả cho router xử lý
        
        except asyncio.TimeoutError:
            raise Exception(f"⏰ Hết thời gian chờ phản hồi (Timeout) cho lệnh [{msg_type}] tới máy {machine_id}")
        finally:
            # Dọn dẹp RAM lưu trữ bộ đệm Future
            self.pending_responses.pop(message_id, None)

# Khởi tạo instance dùng chung cho toàn bộ app backend
gateway_client = GatewayClient("ws://localhost:8765")