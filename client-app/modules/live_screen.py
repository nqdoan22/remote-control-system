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
import ctypes
import io
import logging
import os
import threading
import time
from ctypes import wintypes
from typing import Callable, List, Optional, Tuple

import mss
import psutil
from PIL import Image, ImageDraw

from config import settings

logger = logging.getLogger("LiveScreenModule")

# Thời gian tối đa (giây) chờ worker thread thoát khi stop_stream()
_STOP_JOIN_TIMEOUT = 2.0

# Chu kỳ (giây) quét lại danh sách cửa sổ cần che (chống đệ quy feedback loop)
_RECTS_REFRESH_INTERVAL = 0.5

# Danh sách tên tiến trình trình duyệt Web — dùng khi Admin xem CHÍNH máy này
# (self-view): che toàn bộ cửa sổ trình duyệt để cắt vòng lặp feedback loop
# BẤT KỂ đang mở trang web nào (không phụ thuộc tiêu đề cửa sổ).
_BROWSER_PROCESS_NAMES: frozenset[str] = frozenset({
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "opera.exe",
    "brave.exe",
    "vivaldi.exe",
    "chromium.exe",
    "iexplore.exe",
})


def _iter_window_info() -> List[Tuple[str, int, Optional["wintypes.RECT"]]]:
    """
    Liệt kê các cửa sổ top-level đang hiển thị trên màn hình.

    Returns:
        List[(title, pid, rect)] — rect là wintypes.RECT (toạ độ màn hình ảo)
        hoặc None nếu không lấy được toạ độ.
    """
    results: List[Tuple[str, int, Optional["wintypes.RECT"]]] = []
    try:
        user32 = ctypes.windll.user32
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080

        def _callback(hwnd, lparam) -> bool:
            # Bỏ qua cửa sổ ẩn / đang thu nhỏ (không nằm trên màn hình hiển thị)
            if not user32.IsWindowVisible(hwnd):
                return True
            if user32.IsIconic(hwnd):
                return True
            # Bỏ qua ToolWindow (tooltip, system tray…)
            if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
                return True

            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            title = ""
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value or ""

            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                rect = None

            results.append((title, pid.value, rect))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        callback = WNDENUMPROC(_callback)
        user32.EnumWindows(callback, 0)
    except Exception as e:
        logger.debug(f"Không thể quét cửa sổ để chống đệ quy Live Screen: {e}")
    return results


def _enum_title_rects(keyword: str, exclude_pid: Optional[int] = None) -> List[Tuple[int, int, int, int]]:
    """
    Tìm cửa sổ có TIÊU ĐỀ chứa `keyword` (VD: "Remote Control System" — cửa sổ
    trình duyệt Web App). Đây là lớp phòng thủ luôn bật; nó chỉ khớp đúng cửa sổ
    Web App nên không ảnh hưởng tới người dùng máy khác.

    Returns:
        List[(left, top, right, bottom)] — toạ độ màn hình ảo.
    """
    rects: List[Tuple[int, int, int, int]] = []
    for title, pid, rect in _iter_window_info():
        if exclude_pid is not None and pid == exclude_pid:
            continue
        if rect is None:
            continue
        if keyword and keyword.lower() in title.lower():
            rects.append((rect.left, rect.top, rect.right, rect.bottom))
    return rects


def _enum_browser_rects(exclude_pid: Optional[int] = None) -> List[Tuple[int, int, int, int]]:
    """
    Tìm mọi cửa sổ thuộc về tiến trình TRÌNH DUYỆT (chrome/msedge/firefox/...).
    Dùng khi Admin đang xem chính máy này: che toàn bộ trình duyệt để cắt vòng
    lặp feedback loop dù trình duyệt đang mở trang web / tab bất kỳ.

    Returns:
        List[(left, top, right, bottom)] — toạ độ màn hình ảo.
    """
    rects: List[Tuple[int, int, int, int]] = []
    for _, pid, rect in _iter_window_info():
        if exclude_pid is not None and pid == exclude_pid:
            continue
        if rect is None or not pid:
            continue
        try:
            proc_name = psutil.Process(pid).name().lower()
        except Exception:
            proc_name = ""
        if proc_name in _BROWSER_PROCESS_NAMES:
            rects.append((rect.left, rect.top, rect.right, rect.bottom))
    return rects


def _mask_window_rects(img: "Image.Image", monitor_rect: dict, window_rects: List[Tuple[int, int, int, int]]) -> None:
    """
    Vẽ đè (tô đen) các vùng cửa sổ trình duyệt lên frame đã chụp để cắt đứt
    vòng lặp feedback (đệ quy).

    `window_rects` đang ở toạ độ màn hình ảo; `monitor_rect` (mss.monitors[i])
    chứa left/top của monitor đang chụp để đổi sang toạ độ pixel của ảnh.
    """
    if not window_rects:
        return
    mon_left = int(monitor_rect.get("left", 0))
    mon_top = int(monitor_rect.get("top", 0))
    draw = ImageDraw.Draw(img)
    for (l, t, r, b) in window_rects:
        x0 = max(0, min(img.width, l - mon_left))
        y0 = max(0, min(img.height, t - mon_top))
        x1 = max(0, min(img.width, r - mon_left))
        y1 = max(0, min(img.height, b - mon_top))
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], fill=(13, 13, 18))


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
        mask_browser_windows: bool = False,
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
            mask_browser_windows: True khi Admin đang xem CHÍNH máy này (self-view)
                 → che toàn bộ cửa sổ trình duyệt (theo tên tiến trình) để cắt vòng
                 lặp feedback loop dù trình duyệt đang mở trang web/tab bất kỳ.
        """
        if self.is_streaming:
            logger.warning("⚠️ Luồng Live Screen cũ vẫn đang chạy — tự động dừng rồi khởi động lại.")
            self.stop_stream()

        effective_fps = fps or settings.SCREEN_FPS
        logger.info(
            f"📹 [LIVE SCREEN] Khởi chạy luồng stream màn hình "
            f"(FPS: {effective_fps}, mask_browsers={mask_browser_windows})..."
        )

        self.is_streaming = True
        self._stop_event = threading.Event()
        self._worker = threading.Thread(
            target=self._capture_loop,
            args=(send_frame_callback, monitor_index, effective_fps, self._stop_event, mask_browser_windows),
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
        mask_browser_windows: bool = False,
    ):
        """
        Vòng lặp chụp và gửi khung hình theo FPS — chạy trên worker thread.

        Dùng stop_event.wait() thay vì time.sleep() để lệnh stop có thể đánh
        thức worker thoát ngay lập tức (không phải chờ hết chu kỳ ngủ).
        """
        frame_delay = 1.0 / max(1, fps)

        # Chống đệ quy (feedback loop) khi Admin xem chính máy này: luôn che các
        # cửa sổ Web App (khớp tiêu đề); nếu self-view thì che LUÔN mọi cửa sổ
        # trình duyệt theo tên tiến trình — dù đang mở trang web/tab bất kỳ.
        exclude_own_ui = bool(settings.LIVE_SCREEN_EXCLUDE_OWN_UI)
        ui_keyword = str(settings.LIVE_SCREEN_UI_TITLE_KEYWORD)
        excluded_rects: List[Tuple[int, int, int, int]] = []
        last_rects_refresh = 0.0

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

                    # 3. Che cửa sổ Web App / trình duyệt (cắt vòng lặp đệ quy)
                    if exclude_own_ui:
                        now = time.monotonic()
                        if now - last_rects_refresh >= _RECTS_REFRESH_INTERVAL:
                            rects = _enum_title_rects(ui_keyword, exclude_pid=os.getpid())
                            if mask_browser_windows:
                                rects.extend(_enum_browser_rects(exclude_pid=os.getpid()))
                            excluded_rects = rects
                            last_rects_refresh = now
                        _mask_window_rects(img, selected_monitor, excluded_rects)

                    # 4. Nén JPEG vào bộ nhớ đệm RAM
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=settings.JPEG_QUALITY, optimize=True)
                    buffer.seek(0)

                    # 5. Mã hóa Base64 và gọi Callback gửi dữ liệu
                    base64_frame = base64.b64encode(buffer.getvalue()).decode("utf-8")

                    if callable(send_frame_callback):
                        send_frame_callback(base64_frame, img.width, img.height)

                    # 6. Nếu đang có lệnh dừng thì thoát ngay, không ngủ thêm
                    if stop_event.is_set():
                        break

                    # 7. Tính toán thời gian ngủ để duy trì FPS ổn định
                    elapsed = time.monotonic() - start_time
                    sleep_time = max(0.0, frame_delay - elapsed)
                    if sleep_time > 0:
                        stop_event.wait(sleep_time)

        except Exception as e:
            logger.error(f"❌ Lỗi trong vòng lặp Live Screen Stream: {e}")
            self.is_streaming = False


# Tạo instance singleton cho module live_screen
screen_streamer = LiveScreenStreamer()
