"""
===============================================================================
FILE: client-app/modules/live_screen.py
PURPOSE: Truyền luồng video màn hình thời gian thực (Live Screen Stream) qua WebSocket.
ARCHITECTURE ROLE:
  - Advanced Module - Chạy vòng lặp chụp màn hình trên một WORKER THREAD riêng.
  - BẮT BUỘC có xác nhận Permission từ End User trước khi khởi tạo luồng.
  - Kiểm soát FPS và Chất lượng nén JPEG để tối ưu đường truyền Mạng LAN.

GHI CHÚ ỔN ĐỊNH (LiveScreen instability fix):
  - mss.grab() + PIL JPEG encode + base64 là các thao tác đồng bộ nặng. Trước đây
    vòng lặp này chạy trên chính asyncio event loop của GatewayService nên mỗi
    frame làm ĐÓNG BĂNG toàn bộ luồng xử lý mạng: client không nhận/xử lý kịp
    lệnh screen.live.stop/start, heartbeat bị trễ, các response khác bị timeout.
    Hậu quả: khi Admin rời trang (unmount gửi stop) mà stream vẫn chưa tắt được,
    lần bật lại sau đó bị từ chối ALREADY_RUNNING.
  - Giải pháp: vòng lặp chụp chạy trên một threading.Thread riêng (daemon).
    Event loop của GatewayService luôn rảnh để nhận lệnh điều khiển tức thì,
    stop/start/restart luôn hoạt động tin cậy.
===============================================================================
"""

import base64
import io
import logging
import threading
import time
from typing import Callable, Optional

import mss
from PIL import Image

from config import settings

logger = logging.getLogger("LiveScreenModule")

# Thời gian tối đa (giây) chờ worker thread thoát khi stop_stream()
_STOP_JOIN_TIMEOUT = 2.0


class LiveScreenStreamer:
    """
    Class quản lý trạng thái Bật/Tắt luồng Stream Màn hình.

    Luồng chụp chạy trên một worker thread độc lập, không bao giờ chặn
    asyncio event loop của GatewayService.
    """

    def __init__(self):
        self.is_streaming: bool = False
        self._worker: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None

    def start_stream(
        self,
        send_frame_callback: Callable[[str, int, int], None],
        monitor_index: int = 0,
        fps: Optional[int] = None,
    ):
        """
        Bắt đầu luồng Stream màn hình trên một worker thread.

        Nếu đang có stream cũ chưa tắt (VD: lần trước Admin rời trang đột ngột
        mà lệnh stop chưa kịp về), tự động DỪNG stream cũ rồi khởi động lại —
        nhờ vậy lệnh start LUÔN thành công, không còn bị từ chối ALREADY_RUNNING.

        Args:
            send_frame_callback: Callback nhận (base64_jpeg, width, height) để gửi
                                  qua WebSocket (frameIndex/timestamp do bên gọi
                                  tự đánh số theo api_contract.md). Callback được
                                  gọi từ worker thread — phải là hàm thread-safe
                                  (CommandDispatcher dùng send_message_threadsafe).
            monitor_index: Chỉ số màn hình cần stream (0: Màn hình tổng).
            fps: Số khung hình/giây do Web App yêu cầu (payload.fps).
                 None = dùng settings.SCREEN_FPS.
        """
        if self.is_streaming:
            logger.warning("⚠️ Luồng Live Screen cũ vẫn đang chạy — tự động dừng rồi khởi động lại.")
            self.stop_stream()

        effective_fps = fps or settings.SCREEN_FPS
        logger.info(f"📹 [LIVE SCREEN] Khởi chạy luồng stream màn hình (FPS: {effective_fps})...")

        self.is_streaming = True
        self._stop_event = threading.Event()
        self._worker = threading.Thread(
            target=self._capture_loop,
            args=(send_frame_callback, monitor_index, effective_fps, self._stop_event),
            name="LiveScreenCaptureThread",
            daemon=True,
        )
        self._worker.start()

    def stop_stream(self):
        """
        Dừng luồng Stream màn hình.

        Idempotent: nếu chưa có stream nào đang chạy thì bỏ qua (không báo lỗi),
        để lệnh stop từ Web App luôn thành công dù stream đã tự ngắt vì lỗi.
        """
        if not self.is_streaming:
            return

        self.is_streaming = False
        if self._stop_event:
            self._stop_event.set()

        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=_STOP_JOIN_TIMEOUT)
        self._worker = None

        logger.info("🛑 [LIVE SCREEN] Đã dừng luồng stream màn hình.")

    def _capture_loop(
        self,
        send_frame_callback: Callable[[str, int, int], None],
        monitor_index: int,
        fps: int,
        stop_event: threading.Event,
    ):
        """
        Vòng lặp chụp và gửi khung hình theo FPS — chạy trên worker thread.

        Dùng stop_event.wait() thay vì time.sleep() để lệnh stop có thể đánh
        thức worker thoát ngay lập tức (không phải chờ hết chu kỳ ngủ).
        """
        frame_delay = 1.0 / max(1, fps)

        try:
            with mss.mss() as sct:
                while self.is_streaming and not stop_event.is_set():
                    start_time = time.monotonic()

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

                    if callable(send_frame_callback):
                        send_frame_callback(base64_frame, img.width, img.height)

                    # 5. Nếu đang có lệnh dừng thì thoát ngay, không ngủ thêm
                    if stop_event.is_set():
                        break

                    # 6. Tính toán thời gian ngủ để duy trì FPS ổn định
                    elapsed = time.monotonic() - start_time
                    sleep_time = max(0.0, frame_delay - elapsed)
                    if sleep_time > 0:
                        stop_event.wait(sleep_time)

        except Exception as e:
            logger.error(f"❌ Lỗi trong vòng lặp Live Screen Stream: {e}")
            self.is_streaming = False


# Tạo instance singleton cho module live_screen
screen_streamer = LiveScreenStreamer()
