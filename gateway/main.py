# gateway/main.py
"""
===============================================================================
FILE: gateway/main.py
PURPOSE: File khởi chạy chính (Entrypoint) của dịch vụ WebSocket Gateway Broker.
ARCHITECTURE ROLE:
  - Lắng nghe kết nối WebSocket trên cổng 8765 (0.0.0.0:8765).
  - Điều hướng các sự kiện Socket mới kết nối hoặc ngắt kết nối.
  - Vận hành tiến trình kiểm tra Heartbeat chạy ngầm (Background Task).
  - Đảm bảo cơ chế Graceful Shutdown khi dừng ứng dụng.
===============================================================================
"""

import asyncio
import logging
import signal
import sys
import os
from typing import Set

# Thư viện quản lý WebSocket bất đồng bộ
import websockets
from websockets.server import WebSocketServerProtocol

# Import các Schemas và Components nội bộ
from schemas.protocol import WSMessage
from core.connection_manager import manager
from handlers.message_handler import handler

# =============================================================================
# CẤU HÌNH LOGGING SYSTEM
# =============================================================================
# Thiết lập định dạng Log giúp dễ dàng theo dõi trên Terminal hoặc Docker Container
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Gateway.Main")

# Địa chỉ IP và Cổng mạng lắng nghe mặc định
HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
PORT = int(os.getenv("GATEWAY_PORT", 8765))
HEARTBEAT_INTERVAL_SECONDS = 5.0   # Tần suất quét kiểm tra Heartbeat (5s)
HEARTBEAT_TIMEOUT_SECONDS = 15.0   # Ngưỡng coi như Agent đã rớt mạng (15s)


# =============================================================================
# 1. TIẾN TRÌNH QUÉT HEARTBEAT NGẦM (BACKGROUND TASK)
# =============================================================================
async def heartbeat_monitor_loop() -> None:
    """
    Vòng lặp chạy ngầm không chặn (Non-blocking Task).
    Định kỳ mỗi 5 giây quét danh sách Agent để phát hiện máy rớt mạng (Timeout > 15s).
    """
    logger.info("[HEARTBEAT] Đã khởi chạy tiến trình giám sát Heartbeat (Mỗi 5 giây).")
    
    while True:
        try:
            # Tạm dừng tiến trình trong 5 giây trước khi thực hiện lượt quét tiếp theo
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)

            # Gọi ConnectionManager lấy danh sách các máy đã chết (mất liên lạc > 15s)
            dead_agent_ids = manager.check_dead_connections(timeout_seconds=HEARTBEAT_TIMEOUT_SECONDS)

            for machine_id in dead_agent_ids:
                logger.warning(f"[HEARTBEAT TIMEOUT] Máy '{machine_id}' không gửi Heartbeat trong 15s -> Đánh dấu OFFLINE.")

                # Xóa Agent khỏi bảng đăng ký kết nối
                await manager.unregister_agent(machine_id)

                # Báo sự kiện cho tất cả WebApp Admin giao diện biết máy này vừa Offline
                offline_notification = WSMessage(
                    type="agent.status",
                    source="gateway",
                    destination="webapp",
                    payload={
                        "machineId": machine_id,
                        "status": "offline",
                        "reason": "Heartbeat timeout (>15s)"
                    }
                )
                await manager.broadcast_to_webapps(offline_notification.model_dump_json())

        except asyncio.CancelledError:
            # Sự kiện xảy ra khi Server chuẩn bị tắt (Graceful Shutdown)
            logger.info("[HEARTBEAT] Tiến trình giám sát Heartbeat đang dừng...")
            break
        except Exception as e:
            logger.error(f"[HEARTBEAT ERROR] Lỗi phát sinh trong vòng lặp Heartbeat: {e}")


# =============================================================================
# 2. HÀM XỬ LÝ VÒNG ĐỜI KẾT NỐI WEBSOCKET (SOCKET LIFECYCLE HOOK)
# =============================================================================
async def ws_router_loop(websocket: WebSocketServerProtocol) -> None:
    """
    Hàm callback đại diện cho MỖI kết nối WebSocket mở ra.
    Quản lý luồng nhận dữ liệu từ khi Client kết nối tới khi ngắt kết nối.
    """
    remote_address = websocket.remote_address
    logger.info(f"[NEW CONNECTION] Nhận kết nối Socket mới từ IP/Port: {remote_address}")

    try:
        # Vòng lặp liên tục hứng từng tin nhắn (Raw JSON String) gửi tới từ Socket
        async for raw_message in websocket:
            # Đẩy chuỗi JSON thô sang cho MessageHandler phân loại & xác thực
            await handler.process_message(websocket, raw_message)

    except websockets.exceptions.ConnectionClosedOK:
        # Client ngắt kết nối bình thường (Clean Close)
        logger.info(f"[DISCONNECT CLEAN] Kết nối từ {remote_address} đã đóng bình thường.")
        
    except websockets.exceptions.ConnectionClosedError as e:
        # Client bị ngắt kết nối đột ngột (Rớt mạng, đứt cáp...)
        logger.warning(f"[DISCONNECT ABRUPT] Kết nối từ {remote_address} bị ngắt bất ngờ (Code: {e.code}).")
        
    except Exception as e:
        logger.error(f"[SOCKET ERROR] Lỗi không xác định tại Socket {remote_address}: {e}")
        
    finally:
        # [QUAN TRỌNG] Dọn dẹp tài nguyên và gỡ trạng thái khi Socket bị đóng
        await handler.handle_disconnect(websocket)


# =============================================================================
# 3. HÀM KHỞI CHẠY CHÍNH (MAIN ASYNC ENTRYPOINT)
# =============================================================================
async def main() -> None:
    """
    Hàm điều phối trung tâm: Khởi chạy Server Websockets và Background Heartbeat Task.
    """
    logger.info("==========================================================")
    logger.info(f"   ĐANG KHỞI CHẠY WEBSOCKET GATEWAY BROKER (PORT {PORT})   ")
    logger.info("==========================================================")

    # 1. Kích hoạt Tiến trình Quét Heartbeat ngầm
    heartbeat_task = asyncio.create_task(heartbeat_monitor_loop())

    # 2. Cấu hình và Khởi tạo WebSocket Server
    # max_size=None cho phép truyền các gói tin lớn (như hình ảnh Screen/Webcam Base64)
    async with websockets.serve(
        ws_router_loop,
        HOST,
        PORT,
        max_size=None,          # Không giới hạn dung lượng frame nhận vào
        ping_interval=None,     # Tắt ping/pong mặc định của thư viện để dùng custom system.ping
        ping_timeout=None
    ) as server:
        logger.info(f"[SERVER STARTED] Gateway đang lắng nghe tại ws://{HOST}:{PORT}")

        # Tạo Event để giữ chương trình luôn chạy cho đến khi nhận tín hiệu Tắt (Shutdown)
        stop_event = asyncio.Event()

        # Đăng ký bắt các tín hiệu tắt ứng dụng từ Hệ điều hành (CTRL+C hoặc Docker Stop)
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                # Tránh lỗi trên môi trường OS không hỗ trợ add_signal_handler (như một số bản Windows)
                pass

        # Chờ tín hiệu dừng từ hệ thống
        await stop_event.wait()
        
        logger.info("[SHUTDOWN] Đã nhận tín hiệu dừng hệ thống! Đang tiến hành đóng Gateway...")

    # 3. Dọn dẹp tiến trình ngầm khi Server đóng
    heartbeat_task.cancel()
    await asyncio.gather(heartbeat_task, return_exceptions=True)
    logger.info("[SHUTDOWN COMPLETE] Gateway đã tắt an toàn thành công.")


# =============================================================================
# 4. ĐIỂM THI HÀNH CHƯƠNG TRÌNH (PROGRAM EXECUTION)
# =============================================================================
if __name__ == "__main__":
    try:
        # Chạy Event Loop chính của Asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[EXIT] Đã dừng chương trình bằng bàn phím (Ctrl+C).")