# gateway/main.py
import asyncio
import logging
import websockets
from core.connection_manager import manager
from handlers.message_handler import handle_incoming_message

# Cấu hình log
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [GATEWAY MAIN] - %(levelname)s - %(message)s")
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
                "type": "system.heartbeat",
                "source": agent_id,
                "destination": "webapp",
                "payload": {"status": "offline"}
            }
            await manager.broadcast_to_webapps(str(offline_event).replace("'", '"'))

async def main():
    logger.info(f"🚀 Gateway Server đang khởi chạy tại ws://{HOST}:{PORT} ...")
    async with websockets.serve(router, HOST, PORT):
        await asyncio.Future()  # Giữ cho server chạy vô tận

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Gateway Server đã dừng!")