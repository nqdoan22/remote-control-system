import asyncio
import websockets
import json

class GatewayClient:
    def __init__(self, gateway_url):
        self.gateway_url = gateway_url
        self.websocket = None
        self.event_handlers = {}

    def on(self, action, handler):
        """Đăng ký một hàm xử lý cho một action cụ thể."""
        self.event_handlers[action] = handler
    
    async def connect(self):
        """Kết nối tới Gateway và duy trì lắng nghe."""
        try:
            self.websocket = await websockets.connect(f"{self.gateway_url}/webapp")
            print(">>> [SUCCESS] Đã kết nối tới Gateway!")
            await self.listen()
        except Exception as e:
            print(f">>> [ERROR] Lỗi kết nối: {e}. Thử lại sau 5s...")
            await asyncio.sleep(5)
            await self.connect()

    async def listen(self):
        """Vòng lặp lắng nghe dữ liệu từ Gateway."""
        async for message in self.websocket:
            data = json.loads(message)
            self.handle_incoming_data(data)

    def handle_incoming_data(self, data):
        action = data.get("action")
        payload = data.get("payload")
        
        print(f">>> [RECEIVE] Hành động: {action}")
        
        # Gọi hàm đã đăng ký nếu action tồn tại
        if action in self.event_handlers:
            self.event_handlers[action](payload)
        else:
            print(f">>> [WARNING] Không có handler cho action: {action}")

    async def send_command(self, machine_id, module, action, payload={}):
        """Hàm dùng để Admin gửi lệnh đi."""
        message = {
            "target": machine_id,
            "module": module,
            "action": action,
            "payload": payload
        }
        await self.websocket.send(json.dumps(message))
        print(f">>> [SEND] Đã gửi lệnh {action} tới máy {machine_id}")

# Khởi chạy client
if __name__ == "__main__":
    client = GatewayClient("ws://localhost:8765")
    asyncio.run(client.connect())