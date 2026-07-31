"""
===============================================================================
FILE: client-app/modules/live_screen.py
PURPOSE: Truyền luồng video màn hình thời gian thực (Live Screen Stream) qua WebSocket.
ARCHITECTURE ROLE:
  - Advanced Module - Chạy vòng lặp bất đồng bộ trong Background Task.
  - BẮT BUỘC có xác nhận Permission từ End User trước khi khởi tạo luồng.
  - Kiểm soát FPS và Chất lượng nén JPEG để tối ưu đường truyền Mạng LAN.
===============================================================================
"""

import asyncio
import base64
import io
import logging
from typing import Callable, Optional
import mss
from PIL import Image

from config import settings

logger = logging.getLogger("LiveScreenModule")


class LiveScreenStreamer:
    """
    Class quản lý trạng thái Bật/Tắt luồng Stream Màn hình.
    """

    def __init__(self):
        self.is_streaming: bool = False
        self._stream_task: Optional[asyncio.Task] = None

    async def start_stream(self, send_frame_callback: Callable[[str], None], monitor_index: int = 0):
        """
        Bắt đầu luồng Stream màn hình.
        
        Args:
            send_frame_callback: Hàm callback nhận chuỗi Base64 JPEG để gửi qua WebSocket.
            monitor_index: Chỉ số màn hình cần stream (0: Màn hình tổng).
        """
        if self.is_streaming:
            logger.warning("⚠️ Luồng Stream màn hình đã đang chạy trước đó!")
            return

        self.is_streaming = True
        logger.info(f"📹 [LIVE SCREEN] Khởi chạy luồng stream màn hình (FPS: {settings.SCREEN_FPS})...")

        # Tạo Background Task để không làm đóng băng event loop chính
        self._stream_task = asyncio.create_task(
            self._stream_loop(send_frame_callback, monitor_index)
        )

    async def stop_stream(self):
        """
        Dừng luồng Stream màn hình.
        """
        if not self.is_streaming:
            return

        self.is_streaming = False
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
            self._stream_task = None

        logger.info("🛑 [LIVE SCREEN] Đã dừng luồng stream màn hình.")

    async def _stream_loop(self, send_frame_callback: Callable[[str], None], monitor_index: int):
        """
        Vòng lặp chụp và gửi khung hình theo FPS.
        """
        frame_delay = 1.0 / max(1, settings.SCREEN_FPS)

        try:
            with mss.mss() as sct:
                while self.is_streaming:
                    start_time = asyncio.get_event_loop().time()

                    # 1. Kiểm tra monitor index
                    if monitor_index < 0 or monitor_index >= len(sct.monitors):
                        selected_monitor = sct.monitors[0]
                    else:
                        selected_monitor = sct.monitors[monitor_index]

                    # 2. Chụp khung hình thô
                    sct_img = sct.grab(selected_monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                    # 3. Nén JPEG vào bộ nhớ đệm RAM
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=settings.JPEG_QUALITY, optimize=True)
                    buffer.seek(0)

                    # 4. Mã hóa Base64 và gọi Callback gửi dữ liệu
                    base64_frame = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    
                    # Gọi hàm gửi qua WebSocket
                    if callable(send_frame_callback):
                        send_frame_callback(base64_frame)

                    # 5. Tính toán thời gian ngủ để duy trì FPS ổn định
                    elapsed = asyncio.get_event_loop().time() - start_time
                    sleep_time = max(0.0, frame_delay - elapsed)
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Lỗi trong vòng lặp Live Screen Stream: {str(e)}")
            self.is_streaming = False


# Tạo instance singleton cho module live_screen
screen_streamer = LiveScreenStreamer()