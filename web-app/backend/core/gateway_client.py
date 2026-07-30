"""
===============================================================================
FILE: web-app/backend/core/gateway_client.py
PURPOSE: Bộ điều khiển WebSocket Client kết nối Backend với Gateway Server.
ARCHITECTURE ROLE: 
  - Đóng vai trò cầu nối duy trì kết nối WebSocket thời gian thực giữa Web App 
    Backend và Gateway.
  - Chịu trách nhiệm đóng gói, gửi lệnh điều khiển (từ API Router) tới Gateway, 
    đồng thời lắng nghe phản hồi và truyền kết quả về lại cho Frontend.
===============================================================================
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

# Import cấu hình tập trung và Schema giao thức mã hóa đã định nghĩa
from core.config import settings
from schemas.protocol import WSMessage

# Khởi tạo Logger để ghi nhật ký hoạt động mạng
logger = logging.getLogger("GatewayClient")


class GatewayClient:
    """
    Class quản lý kết nối WebSocket Client kết nối tới Gateway Server.
    Sử dụng Pattern Singleton/Managed Instance để tái sử dụng 1 kết nối duy nhất.
    """

    def __init__(self):
        # Biến lưu trữ đối tượng kết nối WebSocket trực tiếp
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        
        # Cờ đánh dấu trạng thái kết nối
        self.is_connected: bool = False
        
        # Cờ kiểm soát vòng lặp chạy ngầm duy trì kết nối
        self._running: bool = False
        
        # Task chạy ngầm duy trì lắng nghe và kết nối lại
        self._connection_task: Optional[asyncio.Task] = None
        
        # BẢNG TRA CỨU PHẢN HỒI (Pending Requests):
        # Lưu trữ các asyncio.Future đang chờ phản hồi từ Gateway.
        # Key: messageId (str) | Value: asyncio.Future (Đối tượng chứa kết quả tương lai)
        self.pending_requests: Dict[str, asyncio.Future] = {}

    # =========================================================================
    # 🌟 HÀM HIGHLIGHT 1: QUẢN LÝ VÒNG ĐỜI KẾT NỐI (START & AUTO-RECONNECT)
    # =========================================================================

    async def start(self):
        """
        Khởi chạy Service WebSocket Client chạy ngầm (Background Worker).
        Được gọi khi server FastAPI khởi động (Lifespan Startup).
        """
        if self._running:
            logger.warning("Gateway Client đã và đang chạy.")
            return

        self._running = True
        # Tạo một Task chạy ngầm không chặn (Non-blocking) toàn bộ ứng dụng FastAPI
        self._connection_task = asyncio.create_task(self._connection_loop())
        logger.info("Khởi tạo dịch vụ Gateway Client ngầm thành công.")

    async def _connection_loop(self):
        """
        Vòng lặp vĩnh cửu quản lý việc Kết nối & Tự động kết nối lại (Auto-reconnect)
        khi kết nối tới Gateway bị gián đoạn.
        """
        while self._running:
            try:
                logger.info(f"Đang kết nối tới Gateway Server tại: {settings.GATEWAY_WS_URL} ...")
                
                # Thực hiện kết nối WebSocket tới Gateway
                async with websockets.connect(settings.GATEWAY_WS_URL) as websocket:
                    self.ws = websocket
                    self.is_connected = True
                    logger.info("✅ Đã kết nối thành công tới Gateway Server!")

                    # Bắt đầu vòng lặp lắng nghe tin nhắn từ Gateway
                    await self._listen_loop()

            except (ConnectionClosedError, ConnectionClosedOK) as e:
                logger.warning(f"⚠️ Ngắt kết nối khỏi Gateway Server: {e}")
            except Exception as e:
                logger.error(f"❌ Lỗi kết nối Gateway Server: {e}")
            
            # Cập nhật trạng thái ngắt kết nối
            self.is_connected = False
            self.ws = None

            # Nếu hệ thống vẫn đang vận hành, chờ 3 giây rồi thử kết nối lại
            if self._running:
                logger.info("Chờ 3 giây trước khi tự động kết nối lại tới Gateway...")
                await asyncio.sleep(3)

    # =========================================================================
    # 🌟 HÀM HIGHLIGHT 2: VÒNG LẶP LẮNG NGHE TIN NHẮN TỪ GATEWAY
    # =========================================================================

    async def _listen_loop(self):
        """
        Vòng lặp liên tục đọc các gói tin JSON nhận được từ Gateway Server.
        """
        while self.is_connected and self.ws:
            try:
                # Chờ nhận tin nhắn thô dạng Text/JSON từ WebSocket
                raw_message = await self.ws.recv()
                
                # Chuyển đổi dữ liệu JSON và chuyển tới hàm xử lý
                await self._handle_incoming_message(raw_message)

            except (ConnectionClosedError, ConnectionClosedOK):
                break  # Bỏ vòng lặp để _connection_loop thực hiện Reconnect
            except Exception as e:
                logger.error(f"Lỗi khi nhận tin nhắn từ Gateway: {e}")

    # =========================================================================
    # 🌟 HÀM HIGHLIGHT 3: XỬ LÝ & PHÂN LOẠI TIN NHẮN NHẬN VỀ
    # =========================================================================

    async def _handle_incoming_message(self, raw_message: str):
        """
        Phân tích gói tin nhận về và khớp nối với các Request đang chờ kết quả.
        
        Args:
            raw_message (str): Chuỗi JSON thô từ WebSocket.
        """
        try:
            # Parse chuỗi JSON thành đối tượng dict
            data = json.loads(raw_message)
            
            # Đóng gói dữ liệu vào Pydantic Schema WSMessage để kiểm tra tính hợp lệ
            message = WSMessage(**data)
            
            logger.debug(f"Nhận message type='{message.type}' id='{message.messageId}' từ '{message.source}'")

            # Lấy messageId hoặc originalMessageId (nếu tin nhắn trả về là kết quả của lệnh trước đó)
            msg_id = message.messageId
            payload = message.payload
            
            # Kiểm tra xem payload có chứa ID của request gốc không (trong trường hợp error hoặc response)
            original_id = payload.get("originalMessageId") if isinstance(payload, dict) else None
            
            # Xác định ID cần giải quyết (Ưu tiên originalMessageId nếu có)
            target_id = original_id if original_id and original_id in self.pending_requests else msg_id

            # KHỚP NỐI REQUEST-RESPONSE:
            # Nếu ID này có trong Bảng tra cứu Pending Requests -> Đánh dấu Hoàn thành Future
            if target_id in self.pending_requests:
                future = self.pending_requests.pop(target_id)
                if not future.done():
                    future.set_result(message)
                    logger.info(f"✅ Đã khớp và trả kết quả cho Request ID: {target_id}")
            else:
                # Tin nhắn không thuộc Request nào đang chờ (VD: Tín hiệu Broadcast / Heartbeat ngầm)
                logger.info(f"Nhận tin nhắn sự kiện chủ động (Event/Broadcast): {message.type}")

        except Exception as e:
            logger.error(f"Không thể xử lý tin nhắn đầu vào: {e} | Raw: {raw_message}")

    # =========================================================================
    # 🌟 HÀM HIGHLIGHT 4: GỬI LỆNH VÀ CHỜ PHẢN HỒI (HÀM CỐT LÕI CHO API ROUTERS)
    # =========================================================================

    async def send_command_and_wait_response(
        self, 
        message: WSMessage, 
        timeout: Optional[int] = None
    ) -> WSMessage:
        """
        Gửi một lệnh điều khiển tới Gateway và treo chờ phản hồi (Response) 
        trong một khoảng thời gian quy định (Timeout).
        
        Args:
            message (WSMessage): Gói tin lệnh chuẩn hóa theo protocol.py
            timeout (Optional[int]): Thời gian chờ tối đa (giây). Mặc định lấy từ config.py
            
        Returns:
            WSMessage: Gói tin phản hồi nhận về từ Client/Gateway.
            
        Raises:
            RuntimeError: Khi Gateway chưa được kết nối.
            TimeoutError: Khi hết thời gian chờ mà không có phản hồi.
        """
        if not self.is_connected or not self.ws:
            raise RuntimeError("Chưa thể gửi lệnh: Kết nối tới Gateway Server đang bị ngắt!")

        # Thiết lập thời gian chờ mặc định nếu không truyền vào
        timeout_val = timeout if timeout is not None else settings.COMMAND_TIMEOUT_SECONDS

        # Tạo một đối tượng Future để làm "hộp thư chờ" kết quả bất đồng bộ
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()

        # Đăng ký ID tin nhắn vào bảng Pending Requests để hàm _handle_incoming_message lắng nghe
        self.pending_requests[message.messageId] = future

        try:
            # Chuyển đổi WSMessage Schema thành chuỗi JSON và gửi qua WebSocket
            json_payload = message.model_dump_json()
            await self.ws.send(json_payload)
            logger.info(f"🚀 Đã gửi lệnh type='{message.type}' [ID: {message.messageId}] tới destination='{message.destination}'")

            # Treo chờ cho tới khi Future có kết quả HOẶC vượt quá thời gian Timeout
            response = await asyncio.wait_for(future, timeout=timeout_val)
            return response

        except asyncio.TimeoutError:
            logger.error(f"⏰ Lệnh ID {message.messageId} bị quá thời gian chờ (Timeout {timeout_val}s)!")
            raise TimeoutError(f"Không nhận được phản hồi từ máy đích {message.destination} trong vòng {timeout_val} giây.")

        finally:
            # Luôn dọn dẹp ID khỏi bảng tra cứu để tránh rò rỉ bộ nhớ (Memory Leak)
            self.pending_requests.pop(message.messageId, None)

    async def send_fire_and_forget(self, message: WSMessage):
        """
        Gửi một tin nhắn đi mà KHÔNG CẦN CHỜ phản hồi (Dùng cho thông báo/log).
        """
        if not self.is_connected or not self.ws:
            raise RuntimeError("Không thể gửi tin nhắn: Chưa kết nối Gateway!")
        
        json_payload = message.model_dump_json()
        await self.ws.send(json_payload)
        logger.info(f"📤 Đã gửi tin nhắn Fire-and-Forget [ID: {message.messageId}]")

    # =========================================================================
    # QUẢN LÝ TẮT TIẾN TRÌNH (SHUTDOWN)
    # =========================================================================

    async def stop(self):
        """
        Đóng kết nối an toàn khi ứng dụng FastAPI dừng (Lifespan Shutdown).
        """
        logger.info("Đang dừng dịch vụ Gateway Client...")
        self._running = False
        
        # Hủy các Future đang chờ phản hồi
        for msg_id, future in self.pending_requests.items():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()

        # Đóng kết nối WebSocket
        if self.ws:
            await self.ws.close()
            self.ws = None
            
        self.is_connected = False
        logger.info("Dịch vụ Gateway Client đã ngắt hoàn toàn.")


# Khởi tạo một đối tượng Singleton duy nhất để import và dùng trên toàn hệ thống
gateway_client = GatewayClient()