"""
===============================================================================
FILE: client-app/modules/webcam.py
PURPOSE: Quản lý thiết bị Camera phần cứng, stream video và kích hoạt Đèn báo đỏ.
ARCHITECTURE ROLE:
  - Advanced Module - Tương tác Phần cứng trực tiếp (OpenCV).
  - Tích hợp tính năng Bảo mật: Bắt buộc mở Red Indicator Overlay khi Camera active.
  - Quản lý giải phóng tài nguyên Hardware (cap.release) an toàn tránh treo Camera.

KHẮC PHỤC BUG "WEBCAM XÁM / WEBCAM TRỐNG":
  Triệu chứng: đèn camera SÁNG (thiết bị đã mở) nhưng video không có hình mặt
  người — hoặc toàn màu xám, hoặc không hiện gì (màn hình trống).
  Nguyên nhân phổ biến với OpenCV + DSHOW trên Windows:
    1. Webcam chưa "warm-up": vài chục frame đầu auto-exposure/auto-white-balance
       chưa kịp tự chỉnh → frame đầu toàn màu xám đồng nhất.
    2. Định dạng video sai: webcam xuất MJPEG nhưng DSHOW xin định dạng thô
       (YUY2/RGB) → driver trả frame xám placeholder. Fix: xin FOURCC = MJPG.
    3. Webcam đang bị ứng dụng khác chiếm giữ (Camera app, Zoom, trình duyệt,
       hoặc 2 instance client-app cùng lúc) hoặc Windows chặn quyền camera cho
       desktop app → DSHOW vẫn "mở" được (đèn sáng) nhưng không có tín hiệu thật.
    4. Ép thuộc tính camera (FOURCC/resolution) SAI sẽ làm hỏng luồng capture:
       camera mở được nhưng read() thất bại hoặc ra frame rỗng → màn hình trống.

  Chiến lược fix trong code (không làm hỏng camera đang chạy tốt):
    - Mở camera với cấu hình MẶC ĐỊNH trước (như code gốc); chỉ thử MJPG khi
      cần phục hồi, KHÔNG ép property ngay từ đầu.
    - Chờ lấy được frame có TÍN HIỆU THẬT (warm-up) TRƯỚC khi báo start thành
      công. Nếu quá thời gian mà vẫn chỉ ra frame xám/trống → báo lỗi rõ ràng
      cho Admin (kèm gợi ý nguyên nhân) thay vì hiện màn hình trống.
    - Trong vòng lặp: bỏ qua frame xám nhất thời; nếu kẹt xám kéo dài, tự mở lại
      camera (thử MJPG) 1 lần; vẫn thất bại thì dừng stream và log rõ.
===============================================================================
"""

import asyncio
import base64
import logging
from typing import Callable, Optional, Tuple
import cv2

from config import settings

logger = logging.getLogger("WebcamModule")

# Số frame tối đa chờ camera "warm-up" ngay khi khởi động (trước khi báo thành công).
# Nếu hết số frame này mà vẫn không có frame có tín hiệu thật → coi như lỗi.
_STARTUP_VALIDATION_FRAMES = 30

# Thời gian (giây) tối đa chờ camera ra frame thật khi khởi động (phòng trường hợp
# cap.read() bị treo do driver) — tránh đóng băng toàn bộ Client App.
_STARTUP_VALIDATION_TIMEOUT = 6.0

# Ngưỡng độ lệch chuẩn (std) để coi một frame là "xám/đen/trắng đồng nhất"
# (placeholder mất tín hiệu). Frame thật của bất kỳ cảnh nào gần như luôn có
# std lớn hơn nhiều con số này; chỉ frame "mất tín hiệu" mới std ≈ 0.
_BLANK_FRAME_STD_THRESHOLD = 2.0

# Số frame xám liên tiếp tối đa trong lúc stream trước khi thử mở lại camera.
_MAX_CONSECUTIVE_BLANK_BEFORE_REINIT = 30


class WebcamStreamer:
    """
    Class quản lý thiết bị Camera và truyền luồng Video Webcam.
    """

    def __init__(self):
        self.is_streaming: bool = False
        self._stream_task: Optional[asyncio.Task] = None
        self._cap: Optional[cv2.VideoCapture] = None
        self._camera_index: int = 0

    # ------------------------------------------------------------------
    # Camera helpers
    # ------------------------------------------------------------------
    def _open_camera(self, camera_index: int, try_mjpg: bool = False) -> Optional[cv2.VideoCapture]:
        """
        Mở camera phần cứng. Mặc định dùng cấu hình của driver (không ép thuộc
        tính) vì ép sai sẽ làm hỏng capture. Nếu `try_mjpg=True` thì xin thêm
        FOURCC = MJPG — nhiều webcam xuất MJPEG và chỉ cho ảnh đúng khi được xin
        đúng định dạng. Lần lượt thử backend DSHOW → MSMF → ANY.
        """
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
        for backend in backends:
            try:
                cap = cv2.VideoCapture(camera_index, backend)
                if not cap.isOpened():
                    cap.release()
                    continue
                if try_mjpg:
                    try:
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                    except Exception as e:
                        logger.debug(f"Không set FOURCC=MJPG (backend {backend}): {e}")
                return cap
            except Exception as e:
                logger.debug(f"Backend {backend} mở camera thất bại: {e}")
        return None

    @staticmethod
    def _is_blank_frame(frame) -> bool:
        """
        True nếu frame gần như đồng nhất màu (xám/đen/trắng) — dấu hiệu camera
        chưa warm-up xong hoặc đang mất tín hiệu (bị ứng dụng khác chiếm giữ /
        bị chặn quyền riêng tư / xin sai định dạng video).
        """
        try:
            mean, stddev = cv2.meanStdDev(frame)
            if mean is None or stddev is None or stddev.size == 0:
                return True
            return float(stddev.item(0)) < _BLANK_FRAME_STD_THRESHOLD
        except Exception:
            return True

    def _wait_valid_frame(self, cap: cv2.VideoCapture, max_frames: int) -> bool:
        """
        Đọc tối đa `max_frames` frame từ camera (chạy trong thread riêng để không
        chặn event loop). Trả True khi có ít nhất 1 frame có tín hiệu thật.
        Các frame này đồng thời là bước "warm-up" cho auto-exposure/white-balance.
        """
        for _ in range(max_frames):
            ok, frame = cap.read()
            if ok and not self._is_blank_frame(frame):
                return True
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def start_webcam(
        self,
        send_frame_callback: Callable[[str, int, int], None],
        camera_index: int = 0,
        fps: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Mở Camera và bắt đầu gửi luồng hình ảnh.

        Chỉ báo THÀNH CÔNG khi đã lấy được frame có tín hiệu thật (đã warm-up).
        Nếu camera mở được nhưng chỉ cho frame xám/trống → trả (False, lý do)
        để CommandDispatcher báo lỗi rõ ràng cho Admin.

        Lưu ý: điều khiển Red Indicator (đèn báo đỏ) KHÔNG còn nằm trong module này
        — CommandDispatcher chịu trách nhiệm bật/tắt đèn qua signal riêng, vì đó là
        thao tác UI phải chạy trên Main GUI Thread trong khi module này chạy trên
        Gateway Service Thread (asyncio loop).
        """
        if self.is_streaming:
            logger.warning("⚠️ Webcam đã đang hoạt động!")
            return True, ""

        self._camera_index = camera_index

        # 1. Mở camera (cấu hình mặc định trước — an toàn, không làm hỏng capture)
        self._cap = self._open_camera(camera_index)
        if self._cap is None:
            logger.error(f"❌ Không thể truy cập Camera ở index {camera_index}.")
            return False, "Không tìm thấy thiết bị webcam trên máy."

        # 2. Chờ camera warm-up và phải có frame tín hiệu THẬT trước khi báo thành
        #    công. Chạy trong thread để không treo event loop nếu driver camera kẹt.
        try:
            valid = await asyncio.wait_for(
                asyncio.to_thread(self._wait_valid_frame, self._cap, _STARTUP_VALIDATION_FRAMES),
                timeout=_STARTUP_VALIDATION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            valid = False
            logger.error("⚠️ Quá thời gian chờ webcam ra frame thật (driver camera có thể bị treo).")

        if not valid:
            logger.error("❌ Webcam mở được nhưng không nhận được frame có tín hiệu thật (toàn xám/trống).")
            self._cap.release()
            self._cap = None
            return False, (
                "Webcam đã mở nhưng không nhận được tín hiệu hình ảnh. Kiểm tra: "
                "1) camera có đang bị ứng dụng khác chiếm giữ không; "
                "2) Windows Settings → Privacy → Camera đã bật cho desktop apps chưa; "
                "3) chỉ chạy 1 instance client-app."
            )

        # 3. Chỉ khi có tín hiệu thật mới chính thức bật stream
        self.is_streaming = True
        effective_fps = fps or settings.WEBCAM_FPS
        logger.info(f"📷 [WEBCAM] Đã bật Webcam (FPS: {effective_fps})...")

        self._stream_task = asyncio.create_task(
            self._webcam_loop(send_frame_callback, effective_fps)
        )
        return True, ""

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

        - Bỏ qua frame xám nhất thời (đang chuyển cảnh/tự chỉnh) — không gửi cho Admin.
        - Nếu kẹt frame xám kéo dài: thử mở lại camera (xin FOURCC=MJPG) 1 lần.
        - Vẫn thất bại: dừng stream và log rõ để Debug.
        """
        frame_delay = 1.0 / max(1, fps)
        blank_streak = 0
        reinit_done = False

        try:
            while self.is_streaming and self._cap and self._cap.isOpened():
                start_time = asyncio.get_event_loop().time()

                # Đọc 1 frame từ Camera
                ret, frame = self._cap.read()
                if not ret:
                    logger.warning("⚠️ Không thể đọc dữ liệu từ Camera Frame.")
                    await asyncio.sleep(0.1)
                    continue

                # Bỏ qua frame xám/đồng nhất (mất tín hiệu tạm thời / đang tự chỉnh)
                if self._is_blank_frame(frame):
                    blank_streak += 1
                    if blank_streak == 1 or blank_streak % 15 == 0:
                        logger.warning(
                            f"⚠️ Webcam trả về frame xám (liên tiếp {blank_streak} frame). "
                            "Có thể camera đang bị ứng dụng khác chiếm giữ hoặc bị chặn quyền riêng tư."
                        )

                    # Kẹt lâu → thử mở lại camera với định dạng MJPEG (fix xin sai format)
                    if blank_streak >= _MAX_CONSECUTIVE_BLANK_BEFORE_REINIT and not reinit_done:
                        reinit_done = True
                        logger.warning("🔄 Thử mở lại Camera (FOURCC=MJPG) để lấy lại tín hiệu...")
                        self._cap.release()
                        self._cap = self._open_camera(self._camera_index, try_mjpg=True)
                        if self._cap is None:
                            logger.error(
                                "❌ Không mở lại được Camera — webcam có thể đang bị ứng dụng "
                                "khác chiếm giữ hoặc bị Windows chặn quyền camera."
                            )
                            self.is_streaming = False
                            break
                        blank_streak = 0
                    await asyncio.sleep(0.1)
                    continue

                # Frame hợp lệ — reset streak và gửi đi
                blank_streak = 0

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
