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
        
        # Hàng đợi chứa các tin nhắn outbound (gửi từ Client -> Gateway)
        self.send_queue: Optional[asyncio.Queue] = None

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
        self.send_queue = asyncio.Queue()

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
        Lấy các tin nhắn trong Queue ra và đẩy lên Gateway qua kết nối WebSocket.
        """
        while self.running and self.websocket:
            # Lấy tin nhắn từ hàng đợi
            msg_dict = await self.send_queue.get()
            try:
                raw_json = json.dumps(msg_dict)
                await self.websocket.send(raw_json)
                logger.debug(f"[SEND] Đã gửi envelope: type={msg_dict.get('type')}")
            except Exception as e:
                logger.error(f"Lỗi khi gửi gói tin lên Gateway: {e}")
            finally:
                self.send_queue.task_done()

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

            # Đóng gói theo chuẩn WSMessage Envelope (protocol.py)
            heartbeat_msg = {
                "messageId": str(uuid.uuid4()),
                "type": "system.heartbeat",
                "timestamp": int(time.time()),
                "source": settings.CLIENT_ID,
                "destination": "gateway",
                "payload": {
                    "status": "online",
                    "cpu_usage": cpu,
                    "ram_usage": ram,
                    "ip_address": settings.IP_ADDRESS,
                    "hostname": settings.HOSTNAME
                }
            }
            await self.send_queue.put(heartbeat_msg)

    async def _send_auth_message(self):
        """
        Gửi gói tin xác thực đăng ký ban đầu khi vừa kết nối WebSocket thành công.
        Khớp 100% với MessageHandler._handle_auth của Gateway (role + machineId + machineSecret).
        """
        auth_msg = {
            "messageId": str(uuid.uuid4()),
            "type": "system.auth",
            "timestamp": int(time.time()),
            "source": settings.CLIENT_ID,
            "destination": "gateway",
            "payload": {
                "role": "agent",
                "machineId": settings.CLIENT_ID,
                "machineSecret": settings.CLIENT_SECRET,
                "hostname": settings.HOSTNAME,
                "ip_address": settings.IP_ADDRESS,
                "os_info": settings.OS_INFO
            }
        }
        await self.send_queue.put(auth_msg)

    # =========================================================================
    # PUBLIC METHOD (Hàm công khai cho bên ngoài gọi để gửi tin nhắn)
    # =========================================================================
    def send_message_threadsafe(self, message_dict: Dict[str, Any]):
        """
        Hàm Thread-safe cho phép các Thread khác (như GUI PyQt6) đẩy tin nhắn 
        vào Queue để gửi về Gateway mà không gây xung đột Thread.
        """
        if self.loop and self.send_queue:
            asyncio.run_coroutine_threadsafe(
                self.send_queue.put(message_dict), 
                self.loop
            )
        else:
            logger.warning("Chưa thể gửi tin nhắn do Async Event Loop chưa sẵn sàng.")