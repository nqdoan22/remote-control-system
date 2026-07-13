# web-app/backend/core/gateway_client.py
import asyncio
import websockets
import json
import uuid

class GatewayClient:
    """Quản lý kết nối từ Web App Backend tới Gateway qua WebSocket."""

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self.websocket = None
        self.pending_responses = {}  # Nơi lưu trữ các request đang đợi Agent trả lời
        self.listen_task = None

    async def connect(self):
        """Thiết lập kết nối và chạy loop lắng nghe dữ liệu trả về từ Gateway."""
        try:
            self.websocket = await websockets.connect(f"{self.gateway_url}/webapp")
            print(f"🔌 Connected to Gateway at {self.gateway_url}")
            # Chạy tác vụ lắng nghe ngầm mà không làm nghẽn luồng chính
            self.listen_task = asyncio.create_task(self._listen_loop())
        except Exception as e:
            print(f"❌ Failed to connect to Gateway: {e}")

    async def _listen_loop(self):
        """Vòng lặp lắng nghe liên tục phản hồi từ Gateway."""
        try:
            async for message in self.websocket:
                response_data = json.loads(message)
                # Đọc request_id để biết gói tin này trả lời cho lệnh nào
                req_id = response_data.get("request_id")
                if req_id and req_id in self.pending_responses:
                    # Gỏ cửa hộp thư và nhét dữ liệu vào cho hàm đang đợi nhận
                    future = self.pending_responses[req_id]
                    if not future.done():
                        future.set_result(response_data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection to Gateway closed.")

    async def send_command_and_wait(self, machine_id: str, module: str, action: str, payload: dict = {}, timeout: int = 10):
        """Gửi lệnh xuống một máy và đợi phản hồi đồng bộ từ Agent trong khoảng timeout."""
        if not self.websocket:
            raise Exception("Chưa kết nối tới Gateway WebSocket!")

        # Tạo một ID duy nhất cho lượt yêu cầu này
        request_id = str(uuid.uuid4())
        message = {
            "request_id": request_id,
            "target": machine_id,
            "module": module,
            "action": action,
            "payload": payload,
        }

        # Tạo một "Hộp thư đợi" cho request_id này
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_responses[request_id] = future

        try:
            # Gửi lệnh đi xuống Gateway
            await self.websocket.send(json.dumps(message))
            
            # Chờ Agent trả lời trong giới hạn giây (timeout)
            response = await asyncio.wait_for(future, timeout=timeout)
            return response.get("data", {})
        
        except asyncio.TimeoutError:
            raise Exception(f"⏰ Hết thời gian chờ phản hồi (Timeout) từ máy {machine_id}")
        finally:
            # Dọn dẹp hộp thư sau khi xong việc để tránh rác RAM
            self.pending_responses.pop(request_id, None)

# Khởi tạo instance dùng chung cho toàn bộ app backend
gateway_client = GatewayClient("ws://localhost:8765")