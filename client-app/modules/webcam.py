"""
===============================================================================
FILE: client-app/modules/webcam.py
PURPOSE: Quản lý thiết bị Camera phần cứng, stream video và kích hoạt Đèn báo đỏ.
ARCHITECTURE ROLE:
  - Advanced Module - Tương tác Phần cứng trực tiếp (OpenCV).
  - Tích hợp tính năng Bảo mật: Bắt buộc mở Red Indicator Overlay khi Camera active.
  - Quản lý giải phóng tài nguyên Hardware (cap.release) an toàn tránh treo Camera.
===============================================================================
"""

import asyncio
import base64
import logging
from typing import Callable, Optional
import cv2

from config import settings

logger = logging.getLogger("WebcamModule")


class WebcamStreamer:
    """
    Class quản lý thiết bị Camera và truyền luồng Video Webcam.
    """

    def __init__(self):
        self.is_streaming: bool = False
        self._stream_task: Optional[asyncio.Task] = None
        self._cap: Optional[cv2.VideoCapture] = None

    async def start_webcam(
        self,
        send_frame_callback: Callable[[str, int, int], None],
        camera_index: int = 0,
        fps: Optional[int] = None,
    ) -> bool:
        """
        Mở Camera và bắt đầu gửi luồng hình ảnh.

        Lưu ý: điều khiển Red Indicator (đèn báo đỏ) KHÔNG còn nằm trong module này
        — CommandDispatcher chịu trách nhiệm bật/tắt đèn qua signal riêng, vì đó là
        thao tác UI phải chạy trên Main GUI Thread trong khi module này chạy trên
        Gateway Service Thread (asyncio loop).
        """
        if self.is_streaming:
            logger.warning("⚠️ Webcam đã đang hoạt động!")
            return True

        # 1. Thử kết nối Phần cứng Camera
        self._cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW) # CAP_DSHOW giúp mở nhanh hơn trên Windows
        if not self._cap.isOpened():
            logger.error(f"❌ Không thể truy cập Camera ở index {camera_index}.")
            return False

        self.is_streaming = True
        effective_fps = fps or settings.WEBCAM_FPS
        logger.info(f"📷 [WEBCAM] Đã bật Webcam (FPS: {effective_fps})...")

        # 2. Tạo Background Task stream video
        self._stream_task = asyncio.create_task(
            self._webcam_loop(send_frame_callback, effective_fps)
        )
        return True

    async def stop_webcam(self):
        """
        Tắt Camera và Giải phóng tài nguyên Phần cứng.
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

        # Giải phóng thiết bị phần cứng để ứng dụng khác có thể dùng Camera
        if self._cap:
            self._cap.release()
            self._cap = None

        logger.info("🛑 [WEBCAM] Đã tắt Webcam và giải phóng phần cứng.")

    async def _webcam_loop(self, send_frame_callback: Callable[[str, int, int], None], fps: int):
        """
        Vòng lặp đọc Frame từ OpenCV và nén gửi đi.
        """
        frame_delay = 1.0 / max(1, fps)

        try:
            while self.is_streaming and self._cap and self._cap.isOpened():
                start_time = asyncio.get_event_loop().time()

                # Đọc 1 frame từ Camera
                ret, frame = self._cap.read()
                if not ret:
                    logger.warning("⚠️ Không thể đọc dữ liệu từ Camera Frame.")
                    await asyncio.sleep(0.1)
                    continue

                # Nén Frame trực tiếp sang định dạng JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), settings.JPEG_QUALITY]
                result, encimg = cv2.imencode('.jpg', frame, encode_param)

                if result:
                    # Mã hóa Base64
                    base64_frame = base64.b64encode(encimg).decode('utf-8')
                    height, width = frame.shape[:2]

                    if callable(send_frame_callback):
                        send_frame_callback(base64_frame, width, height)

                # Tính toán thời gian nghỉ duy trì FPS
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_time = max(0.0, frame_delay - elapsed)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Lỗi trong vòng lặp Webcam: {str(e)}")
            self.is_streaming = False


webcam_streamer = WebcamStreamer()