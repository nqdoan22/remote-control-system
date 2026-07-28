# gateway/main.py
import asyncio
import logging
import os
import websockets

# Cấu hình log ra file admin.log (PHẢI gọi trước mọi import có logging)
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [GATEWAY] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "admin.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)

from core.connection_manager import manager
from handlers.message_handler import handle_incoming_message

logger = logging.getLogger("GatewayMain")

HOST = "0.0.0.0"  # Lắng nghe trên mọi Interface mạng LAN
PORT = 8765

async def router(websocket):
    """Vòng lặp lắng nghe tin nhắn cho từng kết nối WebSocket."""
    try:
        async for message in websocket:
            await handle_incoming_message(websocket, message)
    except websockets.exceptions.ConnectionClosedError:
        pass
    except Exception as e:
        logger.error(f"Lỗi không xác định trên Socket: {e}")
    finally:
        # Tự động dọn dẹp khi socket đóng
        agent_id = manager.unregister_agent(websocket)
        manager.unregister_webapp(websocket)
        
        # Nếu là Agent rớt kết nối, thông báo cho WebApp biết máy đó đã Offline
        if agent_id:
            offline_event = {
                "type": "machine_offline",
                "source": agent_id,
                "destination": "webapp",
                "payload": {"status": "offline"}
            }
            await manager.broadcast_to_webapps(json.dumps(offline_event))

async def main():
    logger.info(f"Gateway Server đang khởi chạy tại ws://{HOST}:{PORT} ...")
    async with websockets.serve(router, HOST, PORT):
        await asyncio.Future()  # Giữ cho server chạy vô tận

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Gateway Server đã dừng!")