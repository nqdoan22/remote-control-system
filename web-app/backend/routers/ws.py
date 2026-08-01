"""
===============================================================================
FILE: web-app/backend/routers/ws.py
PURPOSE: WebSocket Endpoint /ws - cầu nối thời gian thực giữa Browser và Gateway.
ARCHITECTURE ROLE:
  - Tiếp nhận kết nối WebSocket từ Frontend (ReactJS) tại ws://localhost:8000/ws.
  - Xác thực JWT Access Token truyền qua Query Param.
  - Chuyển tiếp lệnh điều khiển từ Browser tới Gateway (qua gateway_client).
  - Định tuyến phản hồi / sự kiện broadcast từ Gateway trả về đúng Browser.
===============================================================================
"""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from core.gateway_client import gateway_client
from core.ws_connection_manager import ws_connection_manager
from core.security import decode_access_token
from core.config import settings
from schemas.protocol import WSMessage

logger = logging.getLogger("WSRouter")
router = APIRouter()


async def _forward_to_browser(websocket: WebSocket, queue: asyncio.Queue) -> None:
    """
    Task chạy nền (Background Task) của từng Browser:
    Đọc tin nhắn từ hàng đợi (do gateway_client đẩy vào) và gửi về Browser.
    """
    while True:
        raw_message = await queue.get()
        try:
            await websocket.send_text(raw_message)
        except Exception as e:
            logger.error(f"[WS Router] Lỗi gửi tin nhắn về Browser: {e}")
            break


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    machine_id: str = Query(""),
):
    """
    Endpoint WebSocket chính:
      - Yêu cầu: ws://localhost:8000/ws?token=<JWT>&machine_id=<client-app-01>
      - machine_id là tùy chọn (Dashboard có thể kết nối mà không cần chọn máy).
    """
    # 1. Xác thực JWT Token từ Query Param
    token_data = decode_access_token(token)
    if token_data is None:
        logger.warning("[WS Router] Từ chối kết nối: JWT Token không hợp lệ hoặc hết hạn.")
        await websocket.close(code=4401, reason="Token không hợp lệ hoặc đã hết hạn")
        return

    # 2. Đăng ký Browser và tạo hàng đợi nhận tin riêng
    queue = await ws_connection_manager.connect(websocket, machine_id)

    # 3. Khởi chạy Task chuyển tiếp tin nhắn từ Gateway về Browser
    forward_task = asyncio.create_task(_forward_to_browser(websocket, queue))

    try:
        # 4. Vòng lặp nhận lệnh từ Browser
        while True:
            raw_message = await websocket.receive_text()

            try:
                msg = WSMessage(**json.loads(raw_message))
            except Exception as e:
                logger.warning(f"[WS Router] Tin nhắn không hợp lệ từ Browser: {e}")
                continue

            # 🔧 THÊM MỚI: Xử lý gói tin Heartbeat system.ping NGAY tại Backend
            # (Frontend dùng để kiểm tra đường ống /ws còn sống).
            # Trả về system.pong trực tiếp KHÔNG forward xuống Gateway để kết nối
            # Browser <-> Backend sống độc lập, kể cả khi Gateway đang rớt mạng.
            if msg.type == "system.ping":
                pong_msg = WSMessage(
                    type="system.pong",
                    source=settings.BACKEND_SOURCE_ID,
                    destination="webapp",
                    payload={"replyTo": msg.messageId},
                )
                await websocket.send_text(pong_msg.model_dump_json())
                continue

            # Kiểm tra Backend đã kết nối Gateway chưa
            if not gateway_client.is_connected:
                error_msg = WSMessage(
                    type="error",
                    source="webapp-backend",
                    destination="webapp",
                    payload={
                        "code": "GATEWAY_OFFLINE",
                        "message": "Backend chưa kết nối tới Gateway Server.",
                        "originalMessageId": msg.messageId,
                    },
                )
                await websocket.send_text(error_msg.model_dump_json())
                continue

            # Chuyển tiếp lệnh tới Gateway (gateway_client ghi nhận để trả về đúng Browser)
            # 🔧 THÊM MỚI: Bọc try/except để lỗi tạm thời ở Gateway (VD: rớt kết nối đúng
            # lúc đang gửi) KHÔNG làm đóng kết nối WebSocket Browser. Nếu để Exception
            # lan lên trên, FastAPI sẽ đóng socket Browser -> Frontend báo "MẤT KẾT NỐI
            # WEBSOCKET" vĩnh viễn. Thay vào đó ta trả về gói lỗi nhưng vẫn giữ socket sống.
            try:
                await gateway_client.send_browser_message(raw_message, msg, websocket)
            except Exception as e:
                logger.error(f"[WS Router] Lỗi chuyển tiếp lệnh tới Gateway: {e}")
                error_msg = WSMessage(
                    type="error",
                    source=settings.BACKEND_SOURCE_ID,
                    destination="webapp",
                    payload={
                        "code": "GATEWAY_ERROR",
                        "message": "Không thể gửi lệnh tới Gateway Server. Vui lòng thử lại.",
                        "originalMessageId": msg.messageId,
                    },
                )
                await websocket.send_text(error_msg.model_dump_json())

    except WebSocketDisconnect:
        logger.info("[WS Router] Browser đã ngắt kết nối.")
    except Exception as e:
        logger.error(f"[WS Router] Lỗi xử lý kết nối WebSocket: {e}")
    finally:
        # 5. Dọn dẹp tài nguyên khi Browser ngắt kết nối
        ws_connection_manager.disconnect(websocket)
        gateway_client.remove_browser_pending(websocket)
        forward_task.cancel()
