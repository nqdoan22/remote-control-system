"""
===============================================================================
FILE: client-app/core/gateway_service.py
PURPOSE: Xử lý giao tiếp WebSocket bất đồng bộ giữa Client App và Gateway Server.
ARCHITECTURE ROLE:
  - Chạy trên một QThread riêng biệt để tránh làm treo Main GUI Thread của PyQt6.
  - Sử dụng asyncio để duy trì kết nối WebSocket hai chiều thời gian thực.
  - Tự động điểm danh (Heartbeat) và tự động kết nối lại khi mất mạng.
  - Đóng gói và giải nén tin nhắn chuẩn Envelope (WSMessage Schema protocol.py).
===============================================================================
"""

import asyncio
import json
import logging
import time
import uuid
import psutil
from typing import Optional, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosed

from PyQt6.QtCore import QThread, pyqtSignal

# Import cấu hình ứng dụng
from config import settings

logger = logging.getLogger("GatewayService")


class GatewayService(QThread):
    """
    Service chạy ngầm dưới dạng QThread, quản lý toàn bộ vòng đời kết nối WebSocket.
    """

    # =========================================================================
    # SIGNALS (Tín hiệu gửi về cho Main Thread / PyQt6 GUI tiêu thụ)
    # =========================================================================
    connected_signal = pyqtSignal()                      # Phát ra khi kết nối Gateway thành công
    disconnected_signal = pyqtSignal()                   # Phát ra khi bị rớt kết nối
    message_received_signal = pyqtSignal(dict)           # Phát ra khi nhận được tin nhắn WSMessage từ Gateway
    metrics_signal = pyqtSignal(float, float)            # Phát ra mức tiêu thụ CPU/RAM mỗi chu kỳ Heartbeat


    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Hàng đợi tin nhắn ĐIỀU KHIỂN (ưu tiên cao): auth.client, heartbeat,
        # response/error, permission.response, keylogger.data. Luôn được gửi
        # TRƯỚC frame stream để response (VD: application.list, process.list)
        # không bị kẹt sau hàng trăm frame -> Backend không bị timeout 15s.
        self.control_queue: Optional[asyncio.Queue] = None
        # Hàng đợi FRAME STREAM (screen.live.frame / webcam.frame): có giới hạn.
        # Nếu đầy thì bỏ frame cũ nhất (chỉ frame mới nhất có giá trị hiển thị),
        # tránh việc flood frame làm nghẽn đường gửi điều khiển.
        self.frame_queue: Optional[asyncio.Queue] = None

    # =========================================================================
    # CHÍNH (Vòng lặp QThread)
    # =========================================================================
    def run(self):
        """
        Điểm khởi chạy của QThread. Khởi tạo Event Loop của asyncio tại đây.
        """
        logger.info("Đang khởi tạo Asyncio Event Loop trong Worker Thread...")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Khởi tạo Queue trong cùng Event Loop của Asyncio
        self.control_queue = asyncio.Queue()
        self.frame_queue = asyncio.Queue(maxsize=3)

        # Chạy tác vụ chính bất đồng bộ
        try:
            self.loop.run_until_complete(self._main_loop())
        except Exception as e:
            logger.error(f"Lỗi không mong muốn trong Async Event Loop: {e}")
        finally:
            self.loop.close()
            logger.info("Asyncio Event Loop đã dừng.")

    def stop(self):
        """
        Hàm dừng Thread an toàn từ bên ngoài.
        """
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

    # =========================================================================
    # ASYNC LOOPS (Các vòng lặp xử lý mạng)
    # =========================================================================
    async def _main_loop(self):
        """
        Vòng lặp chính quản lý Auto-Reconnect (Tự động kết nối lại khi rớt mạng).
        """
        while self.running:
            try:
                logger.info(f"Đang kết nối tới Gateway tại: {settings.GATEWAY_WS_URL}")
                async with websockets.connect(settings.GATEWAY_WS_URL) as ws:
                    self.websocket = ws
                    logger.info(">>> ĐÃ KẾT NỐI THÀNH CÔNG TỚI GATEWAY! <<<")
                    
                    # Phát tín hiệu báo cho GUI biết đã Online
                    self.connected_signal.emit()

                    # 1. Gửi tin nhắn Đăng ký / Báo danh ban đầu (system.auth)
                    await self._send_auth_message()

                    # 2. Chạy đồng thời 3 Task bất đồng bộ:
                    #    - Task 1: Nhận tin nhắn từ Gateway
                    #    - Task 2: Gửi tin nhắn từ Queue lên Gateway
                    #    - Task 3: Gửi Heartbeat điểm danh định kỳ
                    consumer_task = asyncio.create_task(self._receive_loop())
                    producer_task = asyncio.create_task(self._send_loop())
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                    # Chờ cho đến khi 1 trong các Task bị lỗi (VD: rớt kết nối)
                    done, pending = await asyncio.wait(
                        [consumer_task, producer_task, heartbeat_task],
                        return_when=asyncio.FIRST_EXCEPTION
                    )

                    # Hủy các task còn lại khi có sự cố
                    for task in pending:
                        task.cancel()

            except (ConnectionClosed, OSError, Exception) as e:
                logger.warning(f"Mất kết nối tới Gateway ({e}). Thử lại sau {settings.RECONNECT_INTERVAL_SECONDS}s...")
                self.disconnected_signal.emit()
                self.websocket = None

            # Chờ một khoảng thời gian trước khi thử re-connect
            if self.running:
                await asyncio.sleep(settings.RECONNECT_INTERVAL_SECONDS)

    async def _receive_loop(self):
        """
        Lắng nghe liên tục các gói tin WebSocket từ Gateway gửi tới Client.
        """
        async for raw_message in self.websocket:
            try:
                data = json.loads(raw_message)
                logger.debug(f"[RECV] Nhận envelope: type={data.get('type')}, msgId={data.get('messageId')}")
                
                # Phát tín hiệu mang dữ liệu dict về Main Thread để CommandDispatcher xử lý
                self.message_received_signal.emit(data)

            except json.JSONDecodeError:
                logger.error(f"Gói tin nhận được không phải định dạng JSON hợp lệ: {raw_message}")

    async def _send_loop(self):
        """
        Gửi tin nhắn lên Gateway, LUÔN ưu tiên hàng đợi điều khiển trước.
        Frame stream (screen.live.frame / webcam.frame) chỉ được gửi khi không
        còn tin nhắn điều khiển nào đang chờ, và được giới hạn số lượng (bỏ
        frame cũ) để không làm chậm response.
        """
        while self.running and self.websocket:
            # 1. Ưu tiên tuyệt đối: gửi hết tin nhắn điều khiển đang chờ
            try:
                control_msg = self.control_queue.get_nowait()
            except asyncio.QueueEmpty:
                control_msg = None

            if control_msg is not None:
                await self._send_one(control_msg)
                self.control_queue.task_done()
                continue

            # 2. Không có tin điều khiển -> chờ tin đầu tiên từ 1 trong 2 queue.
            #    Nếu control xuất hiện trước frame, nó vẫn được ưu tiên.
            control_task = asyncio.create_task(self.control_queue.get())
            frame_task = asyncio.create_task(self.frame_queue.get())
            done, pending = await asyncio.wait(
                {control_task, frame_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                try:
                    msg = task.result()
                except (asyncio.QueueEmpty, asyncio.CancelledError):
                    continue
                await self._send_one(msg)
                if task is control_task:
                    self.control_queue.task_done()
                else:
                    self.frame_queue.task_done()

    async def _send_one(self, msg_dict: Dict[str, Any]):
        """Serialize và gửi một tin nhắn lên Gateway (bọc lỗi để không chết vòng lặp)."""
        try:
            raw_json = json.dumps(msg_dict)
            await self.websocket.send(raw_json)
            logger.debug(f"[SEND] Đã gửi envelope: type={msg_dict.get('type')}")
        except Exception as e:
            logger.error(f"Lỗi khi gửi gói tin lên Gateway: {e}")

    async def _heartbeat_loop(self):
        """
        Gửi tín hiệu Heartbeat điểm danh kèm thông số CPU/RAM định kỳ lên Gateway.
        Khớp với Schema MachineUpdate trong machine.py.
        """
        while self.running and self.websocket:
            await asyncio.sleep(settings.HEARTBEAT_INTERVAL_SECONDS)
            
            # Đọc tài nguyên phần cứng thời gian thực via psutil
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent

            # Cập nhật chỉ số CPU/RAM lên giao diện chính
            self.metrics_signal.emit(cpu, ram)

            # Đóng gói theo chuẩn WSMessage Envelope. LƯU Ý: type PHẢI là "heartbeat"
            # (không phải "system.heartbeat") — đây là literal duy nhất mà
            # gateway/handlers/message_router.py::_CLIENT_ALLOWED_TYPES chấp nhận
            # từ Client App, xem docs/api_contract.md.
            heartbeat_msg = {
                "messageId": str(uuid.uuid4()),
                "type": "heartbeat",
                "timestamp": int(time.time()),
                "source": settings.CLIENT_ID,
                "destination": "gateway",
                "payload": {
                    "status": "online",
                    "cpu_usage": cpu,
                    "ram_usage": ram,
                }
            }
            await self.control_queue.put(heartbeat_msg)

    async def _send_auth_message(self):
        """
        Gửi gói tin xác thực đăng ký ban đầu khi vừa kết nối WebSocket thành công.
        Khớp với handlers/client_handler.py::handle_client của Gateway — message đầu
        tiên PHẢI có type="auth.client" và payload chứa machineId/machineSecret/
        hostname/ipAddress (xem docs/api_contract.md + security_design.md).
        """
        auth_msg = {
            "messageId": str(uuid.uuid4()),
            "type": "auth.client",
            "timestamp": int(time.time()),
            "source": settings.CLIENT_ID,
            "destination": "gateway",
            "payload": {
                "machineId": settings.CLIENT_ID,
                "machineSecret": settings.CLIENT_SECRET,
                "hostname": settings.HOSTNAME,
                "ipAddress": settings.IP_ADDRESS,
            }
        }
        await self.control_queue.put(auth_msg)

    # =========================================================================
    # PUBLIC METHOD (Hàm công khai cho bên ngoài gọi để gửi tin nhắn)
    # =========================================================================
    def send_message_threadsafe(self, message_dict: Dict[str, Any]):
        """
        Hàm Thread-safe cho phép các Thread khác (như GUI PyQt6) đẩy tin nhắn
        vào Queue để gửi về Gateway mà không gây xung đột Thread.

        Message điều khiển (response/error/heartbeat/...) đi vào control_queue
        (ưu tiên cao). Message frame stream (screen.live.frame/webcam.frame)
        đi vào frame_queue có giới hạn — khi đầy sẽ bỏ frame cũ để không bao giờ
        nghẽn đường gửi của các lệnh điều khiển khác.
        """
        if self.loop and self.control_queue and self.frame_queue:
            msg_type = message_dict.get("type", "")
            if msg_type in ("screen.live.frame", "webcam.frame"):
                asyncio.run_coroutine_threadsafe(
                    self._put_frame(message_dict),
                    self.loop,
                )
            else:
                asyncio.run_coroutine_threadsafe(
                    self.control_queue.put(message_dict),
                    self.loop,
                )
        else:
            logger.warning("Chưa thể gửi tin nhắn do Async Event Loop chưa sẵn sàng.")

    async def _put_frame(self, message_dict: Dict[str, Any]):
        """
        Đẩy frame vào frame_queue giới hạn. Nếu queue đầy, bỏ frame cũ nhất
        (drop-oldest) rồi thêm frame mới — chỉ frame gần nhất mới có giá trị
        hiển thị, các frame trung gian vứt bỏ không ảnh hưởng chất lượng stream.
        """
        try:
            self.frame_queue.put_nowait(message_dict)
        except asyncio.QueueFull:
            try:
                self.frame_queue.get_nowait()
                self.frame_queue.task_done()
            except asyncio.QueueEmpty:
                pass
            try:
                self.frame_queue.put_nowait(message_dict)
            except asyncio.QueueFull:
                logger.debug("Frame queue vẫn đầy, bỏ frame.")

    def run_coroutine_threadsafe(self, coro):
        """
        Cho phép các Thread khác (Main GUI Thread) lên lịch chạy một coroutine
        (VD: webcam_streamer.start_webcam(...)) ngay trên Event Loop của Thread
        này. Bắt buộc phải dùng hàm này thay vì gọi await trực tiếp, vì các
        module streaming tạo asyncio.Task/Queue gắn với Event Loop đang chạy —
        chúng phải chạy chung Loop với _send_loop/_receive_loop thì mới đẩy được
        frame vào queue gửi đi.

        Lưu ý: Live Screen (modules/live_screen.py) KHÔNG còn dùng hàm này nữa —
        vòng lặp chụp đã được chuyển sang threading.Thread riêng để không chặn
        event loop (xem ghi chú trong live_screen.py).
        """
        if self.loop:
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        logger.warning("Chưa thể lên lịch coroutine do Async Event Loop chưa sẵn sàng.")
        return None