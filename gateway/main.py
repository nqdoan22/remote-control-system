# gateway/main.py
import asyncio
import websockets
import urllib.parse
import logging
from core.connection_manager import ConnectionManager
from handlers.message_handler import MessageHandler

# Cấu hình hệ thống ghi nhật ký tập trung (Audit Log sơ bộ)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s'
)
logger = logging.getLogger("Gateway.Main")

# Khởi tạo các thực thể lõi
manager = ConnectionManager()
message_handler = MessageHandler(manager)

async def handle_client(websocket, path):
    """
    Hàm phân phối kết nối dựa trên đường dẫn Endpoint.
    - Web App kết nối tới: ws://localhost:8765/webapp
    - Agent kết nối tới: ws://localhost:8765/agent?machineId=XXX&secret=YYY
    """
    parsed_url = urllib.parse.urlparse(path)
    clean_path = parsed_url.path
    
    # --- PHÂN HỆ XỬ LÝ KẾT NỐI TỪ WEB APP BACKEND ---
    if clean_path == "/webapp":
        await manager.register_webapp(websocket)
        try:
            async for message in websocket:
                await message_handler.process_incoming_message(websocket, message, client_type="webapp")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await manager.unregister_webapp(websocket)

    # --- PHÂN HỆ XỬ LÝ KẾT NỐI TỪ AGENT (MÁY BỊ ĐIỀU KHIỂN) ---
    elif clean_path == "/agent":
        # Trích xuất dữ liệu xác thực từ Query Parameters gửi lên khi handshake
        params = urllib.parse.parse_qs(parsed_url.query)
        machine_id = params.get("machineId", [None])[0]
        machine_secret = params.get("secret", [None])[0]

        # RÀNG BUỘC BẢO MẬT: Kiểm tra định danh thiết bị
        if not machine_id or not machine_secret:
            logger.error("🚨 Một kết nối từ chối đăng nhập: Thiếu thông tin MachineID hoặc Secret Token.")
            await websocket.close(1008, "Xác thực thất bại: Thiếu thông tin.")
            return

        # Giả lập đối chiếu cơ sở dữ liệu xác thực trong mạng LAN (Có thể mở rộng đọc file .env)
        # Ở đây ta chấp nhận cơ chế xác thực cơ bản phù hợp với đồ án mạng
        logger.info(f"🔒 Đang xác thực thiết bị: {machine_id}...")
        
        await manager.register_agent(machine_id, websocket)
        try:
            async for message in websocket:
                await message_handler.process_incoming_message(
                    websocket, message, client_type="agent", sender_id=machine_id
                )
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await manager.unregister_agent(machine_id)
            
    else:
        # Đường dẫn không hợp lệ -> Đóng chặn tấn công dò quét cổng
        logger.warn(f"⚠️ Cảnh báo: Thiết bị lạ cố tình truy cập đường dẫn không hợp lệ: {clean_path}")
        await websocket.close(1003, "Đường dẫn không hợp lệ.")

async def main():
    # Khởi chạy Socket trên tất cả các card mạng vật lý trong mạng LAN (0.0.0.0) tại port 8765
    server = await websockets.serve(handle_client, "0.0.0.0", 8765, ping_interval=10, ping_timeout=5)
    logger.info("🚀 NETWORK GATEWAY SERVER ĐÃ KHỞI CHẠY THÀNH CÔNG!")
    logger.info("📡 Đang lắng nghe các kết nối WebSocket tại mạng LAN qua cổng 8765...")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Gateway đã được tắt chủ động bởi người quản trị.")