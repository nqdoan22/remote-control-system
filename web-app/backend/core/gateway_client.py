import asyncio
import websockets
import json
import logging

# Cấu hình logging để dễ debug và làm báo cáo
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GatewayClient")

class GatewayClient:
    def __init__(self, gateway_url):
        self.gateway_url = gateway_url
        self.websocket = None
        self.event_handlers = {}

    def on(self, action, handler):
        self.event_handlers[action] = handler
    
    async def connect(self):
        """Kết nối và giữ kết nối bằng vòng lặp while."""
        while True:
            try:
                # Thêm ping_interval để kiểm tra kết nối còn sống không
                async with websockets.connect(f"{self.gateway_url}/webapp", ping_interval=20) as ws:
                    self.websocket = ws
                    logger.info(">>> [SUCCESS] Đã kết nối tới Gateway!")
                    await self.listen() # Chạy lắng nghe
            except Exception as e:
                logger.error(f">>> [ERROR] Lỗi kết nối: {e}. Thử lại sau 5s...")
                await asyncio.sleep(5)
            finally:
                self.websocket = None # Reset khi mất kết nối

    async def listen(self):
        """Vòng lặp lắng nghe."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                # Chạy handler ở task riêng để không làm chặn vòng lặp listen
                asyncio.create_task(self.handle_incoming_data(data))
        except websockets.ConnectionClosed:
            logger.warning(">>> [WARNING] Kết nối bị đóng, thoát listen loop.")

    async def handle_incoming_data(self, data):
        """Xử lý dữ liệu với try-except bao quanh để bảo vệ loop."""
        try:
            action = data.get("action")
            payload = data.get("payload")
            
            if action in self.event_handlers:
                await self.event_handlers[action](payload)
            else:
                logger.warning(f">>> [WARNING] Không có handler cho: {action}")
        except Exception as e:
            logger.error(f">>> [CRITICAL] Lỗi trong handler {data.get('action')}: {e}")

    async def send_command(self, machine_id, module, action, payload={}):
        """Gửi lệnh đi với kiểm tra kết nối."""
        if self.websocket and self.websocket.open:
            message = {
                "target": machine_id,
                "module": module,
                "action": action,
                "payload": payload
            }
            await self.websocket.send(json.dumps(message))
            logger.info(f">>> [SEND] {action} tới {machine_id}")
        else:
            logger.error(">>> [ERROR] Không thể gửi lệnh: WebSocket chưa kết nối!")

# Cách sử dụng mẫu:
# async def my_handler(payload):
#     print("Đã nhận dữ liệu:", payload)
# client.on("screen_data", my_handler)