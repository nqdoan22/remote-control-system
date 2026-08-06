"""
===============================================================================
FILE: client-app/modules/screenshot.py
PURPOSE: Chụp ảnh màn hình máy tính Client, nén JPEG và mã hóa Base64.
ARCHITECTURE ROLE:
  - Direct Execution Module - Trả về dữ liệu ảnh tĩnh dạng Base64.
  - Sử dụng `mss` tối ưu hiệu năng + `Pillow` nén chất lượng theo config.py.
  - Xử lý hoàn toàn trên RAM (BytesIO), không ghi file tạm xuống ổ cứng.
  - LOẠI BỎ UI OVERLAY CỦA CHÍNH AGENT khỏi ảnh chụp: cửa sổ Popup xin quyền
    (permission_popup.py) và đèn báo đỏ (red_indicator.py) là các cửa sổ
    Always-on-Top nổi trên màn hình Client. Nếu chúng vẫn còn hiển thị tại thời
    điểm chụp (VD: race giữa lúc Popup vừa đóng và lúc chụp, hoặc đèn báo đỏ
    đang bật cố định khi feature nhạy cảm đang chạy), `mss` sẽ chụp luôn chúng
    vào ảnh → ảnh gửi về Web Admin bị lẫn "màn hình cảnh báo". Giải pháp: liệt
    kê các cửa sổ overlay của chính tiến trình này rồi tô đè chúng khỏi ảnh
    (kỹ thuật giống live_screen.py che cửa sổ trình duyệt chống feedback loop).
===============================================================================
"""

import base64
import ctypes
import io
import logging
import os
import time
from ctypes import wintypes
from typing import Dict, Any, List, Optional, Tuple
import mss
from PIL import Image, ImageDraw

# Import cấu hình để lấy thông số JPEG_QUALITY
from config import settings

logger = logging.getLogger("ScreenshotModule")

# Từ khóa tiêu đề cửa sổ Main Dashboard của Agent. Dashboard là cửa sổ chính
# HỢP LỆ nên KHÔNG bị che trong ảnh chụp — chỉ che các overlay cảnh báo.
_MAIN_WINDOW_TITLE_KEYWORD = "Remote Administration Agent"

# Từ khóa nhận diện cửa sổ Popup xin quyền (permission_popup.py) — cửa sổ cảnh
# báo "CẢNH BÁO BẢO MẬT & QUYỀN RIÊNG TƯ" không được lọt vào ảnh chụp.
_WARNING_TITLE_KEYWORDS = ("YÊU CẦU XIN QUYỀN", "CẢNH BÁO")

# SetWindowDisplayAffinity / WDA_EXCLUDEFROMCAPTURE — đánh dấu cửa sổ ở CẤP ĐỘ
# HỆ ĐIỀU HÀNH là không bao giờ bị capture (BitBlt / DWM / PrintWindow) chụp lại.
# Cửa sổ vẫn hiển thị bình thường với End User, nhưng trong mọi ảnh chụp màn hình
# nó sẽ bị thay bằng vùng đen. Chỉ hỗ trợ từ Windows 10 build 19041+.
_WDA_EXCLUDEFROMCAPTURE = 0x00000011
_capture_excluded_hwnds: set = set()


def exclude_window_from_capture(hwnd: int) -> bool:
    """
    Giải pháp DỨT ĐIỂM chống "popup/đèn báo bị chụp lẫn": dùng Win32 API
    SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE) để hệ điều hành tự loại
    cửa sổ ra khỏi mọi ảnh chụp màn hình — KHÔNG phụ thuộc timing, ghost frame
    của DWM hay animation fade khi đóng cửa sổ (nguyên nhân khiến popup xuất
    hiện "mờ nhạt" trong ảnh chụp trên máy remote dù đã ẩn/che).

    Áp dụng cho: PermissionPopupDialog (popup xin quyền) và RedIndicatorWidget
    (đèn báo đỏ) ngay khi cửa sổ được show().

    Returns:
        True nếu hệ điều hành chấp nhận (Windows 10 19041+), False trên Windows
        cũ (lúc đó các lớp phòng thủ ẩn/che/đợi vẫn đảm bảo an toàn).
    """
    if not hwnd:
        return False
    try:
        ok = bool(ctypes.windll.user32.SetWindowDisplayAffinity(
            int(hwnd), _WDA_EXCLUDEFROMCAPTURE
        ))
        if ok:
            _capture_excluded_hwnds.add(int(hwnd))
        return ok
    except Exception as e:
        logger.debug(f"SetWindowDisplayAffinity thất bại: {e}")
        return False


def _iter_overlay_ui_rects() -> List[Tuple[int, int, int, int]]:
    """
    Liệt kê toạ độ (màn hình ảo) của các cửa sổ UI overlay ĐANG HIỂN THỊ thuộc
    về CHÍNH tiến trình Client App mà KHÔNG phải là Main Dashboard:
      - PermissionPopupDialog (Popup xin quyền — tiêu đề chứa "YÊU CẦU XIN QUYỀN").
      - RedIndicatorWidget (đèn báo đỏ "WEBCAM / SCREEN IS ACTIVE" — Tool window).

    Returns:
        List[(left, top, right, bottom)] — toạ độ màn hình ảo (pixel vật lý).
    """
    rects: List[Tuple[int, int, int, int]] = []
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

            # Chỉ xử lý cửa sổ thuộc về CHÍNH Agent (pid hiện tại) — không bao
            # giờ đụng tới cửa sổ ứng dụng khác của End User.
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value != os.getpid():
                return True

            title = ""
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value or ""

            # Main Dashboard là cửa sổ chính hợp lệ -> không che
            if _MAIN_WINDOW_TITLE_KEYWORD in title:
                return True

            is_tool_window = bool(
                user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW
            )
            is_warning = any(
                keyword in title for keyword in _WARNING_TITLE_KEYWORDS
            )
            # Chỉ che overlay cảnh báo: đèn báo đỏ (Tool window của Agent) hoặc
            # cửa sổ Popup xin quyền (tiêu đề cảnh báo).
            if not (is_tool_window or is_warning):
                return True

            # OS-level: đánh dấu cửa sổ này là "không bao giờ bị capture" — bảo vệ
            # dứt điểm kể cả khi ẩn/che không kịp (ghost frame, fade animation).
            exclude_window_from_capture(hwnd)

            rect = wintypes.RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return True

            rects.append((rect.left, rect.top, rect.right, rect.bottom))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        callback = WNDENUMPROC(_callback)
        user32.EnumWindows(callback, 0)
    except Exception as e:
        logger.debug(f"Không thể quét cửa sổ overlay UI cho screenshot: {e}")
    return rects


def _temporarily_hide_overlays() -> Tuple[List[int], List[Tuple[int, int, int, int]]]:
    """
    Ẩn tạm mọi cửa sổ UI overlay của CHÍNH Agent (Popup xin quyền, đèn báo đỏ)
    ngay TRƯỚC khi chụp màn hình để chúng không bao giỏt vào ảnh.

    Dùng Win32 trực tiếp (EnumWindows + ShowWindow SW_HIDE) thay vì PyQt6
    QApplication.topLevelWidgets():
      - Không phụ thuộc Qt event-loop / thread affinity → luôn tìm được popup
        kể cả khi popup được tạo bởi module khác, dù ở embedded hoặc nested loop.
      - ShowWindow(SW_HIDE) là native, ngay lập tức, KHÔNG có animation fade
        (khác với QDialog.accept/close gây hiện tượng "mờ nhạt" ghost trên Win10).
      - Thread-safe (Win32 API gọi từ bất kỳ thread nào).

    Ghi nhớ cả HWND lẫn toạ độ để khôi phục + che ghost frame sau khi chụp.

    Returns:
        (hwnds_to_restore, overlay_rects) — HWND ẩn + toạ độ (trái, trên, phải,
        dưới) màn hình ảo của chúng (dùng để mask ghost trong ảnh chụp).
    """
    hwnds: List[int] = []
    rects: List[Tuple[int, int, int, int]] = []
    try:
        user32 = ctypes.windll.user32
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        SW_HIDE = 0

        def _callback(hwnd, lparam) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            if user32.IsIconic(hwnd):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value != os.getpid():
                return True
            title = ""
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value or ""
            # Main Dashboard -> cửa sổ chính hợp lệ, không ẩn
            if _MAIN_WINDOW_TITLE_KEYWORD in title:
                return True
            is_tool_window = bool(
                user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW
            )
            is_warning = any(
                keyword in title for keyword in _WARNING_TITLE_KEYWORDS
            )
            if not (is_tool_window or is_warning):
                return True

            # OS-level: đánh dấu cửa sổ "không bao giờ bị capture" (Win10 2004+)
            exclude_window_from_capture(hwnd)

            r = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(r)):
                rects.append((r.left, r.top, r.right, r.bottom))
                hwnds.append(int(hwnd))
                # Ẩn ngay trên HWND native (không animation) để popup biến mất
                # ngay trước khi grab — giảm tối đa khả năng bắt được ghost frame.
                user32.ShowWindow(hwnd, SW_HIDE)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(_callback), 0)
    except Exception as e:
        logger.debug(f"Không thể ẩn overlay UI (Win32) trước khi chụp: {e}")
    return hwnds, rects


def _restore_overlays(hwnds: List[int]) -> None:
    """Khôi phục lại các cửa sổ overlay đã ẩn bởi _temporarily_hide_overlays."""
    if not hwnds:
        return
    try:
        user32 = ctypes.windll.user32
        SW_SHOW = 5
        for hwnd in hwnds:
            try:
                user32.ShowWindow(int(hwnd), SW_SHOW)
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Không thể khôi phục overlay UI: {e}")


def _mask_overlay_windows(
    img: Image.Image,
    monitor_rect: dict,
    overlay_rects: Optional[List[Tuple[int, int, int, int]]] = None,
) -> None:
    """
    Tô đè (che) các cửa sổ UI overlay của chính Agent (Popup xin quyền, đèn
    báo đỏ) lên ảnh đã chụp để ảnh KHÔNG bao giờ chứa màn hình cảnh báo.

    `monitor_rect` (mss.monitors[i]) chứa left/top của monitor đang chụp để đổi
    toạ độ màn hình ảo sang toạ độ pixel của ảnh.

    QUAN TRỌNG: nên truyền `overlay_rects` được ghi nhận TRƯỚC khi ẩn overlay
    (trong take_screenshot). Vì sau khi ẩn window, `_iter_overlay_ui_rects()`
    không còn tìm thấy nó (IsWindowVisible=False) trong khi DWM trên Windows 10
    VẪN còn frame cũ (ghost) hiển thị popup trong ảnh chụp → nếu chỉ che theo
    rect "đang visible" lúc đó thì sẽ KHÔNG che được ghost.
    """
    if overlay_rects is None:
        overlay_rects = _iter_overlay_ui_rects()
    if not overlay_rects:
        return

    mon_left = int(monitor_rect.get("left", 0))
    mon_top = int(monitor_rect.get("top", 0))
    draw = ImageDraw.Draw(img)
    for (l, t, r, b) in overlay_rects:
        x0 = max(0, min(img.width, l - mon_left))
        y0 = max(0, min(img.height, t - mon_top))
        x1 = max(0, min(img.width, r - mon_left))
        y1 = max(0, min(img.height, b - mon_top))
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], fill=(13, 13, 18))


def take_screenshot(monitor_index: int = 0) -> Dict[str, Any]:
    """
    Chụp ảnh màn hình máy Client và nén thành chuỗi mã hóa Base64 JPEG.
    
    Args:
        monitor_index (int): 0 là chụp toàn bộ màn hình (gộp các màn), 
                             1, 2... là chụp màn hình đơn tương ứng.
                             
    Returns:
        Dict[str, Any]: {
            "success": bool,
            "image_base64": str (Chuỗi Base64 ảnh JPEG),
            "width": int,
            "height": int,
            "message": str
        }
    """
    # BƯỚC 1: Ẩn tất cả overlay UI của Agent (popup, đèn đỏ) TRƯỚC khi grab.
    # _temporarily_hide_overlays dùng Win32 EnumWindows + ShowWindow(SW_HIDE) để
    # tìm và ẩn native window ngay lập tức (không qua Qt event-loop → luôn
    # tìm thấy popup kể cả khi popup do module khác tạo / ở nested loop). Nó
    # đồng thời trả về (hwnd_list, overlay_rects) — toạ độ đã ghi nhận TRƯỚC
    # khi ẩn để che được ghost frame phía sau.
    hidden_hwnds, overlay_rects = _temporarily_hide_overlays()

    # Lớp phòng thủ 1: Ẩn tạm UI overlay của chính Agent (popup xin quyền, đèn
    # báo đỏ) trước khi grab để chúng không bị chụp lẫn — kể cả khi popup vừa
    # đóng vẫn còn trên màn hình tại đúng thời điểm chụp (vấn đề "delay").

    # Chờ DWM (Windows compositor) cập nhật màn hình sau khi ẩn overlay. Nếu grab
    # ngay, DWM vẫn còn frame cũ (ghost) → popup xuất hiện "mờ nhạt" trong ảnh.
    # CHỈ chờ khi thật sự có overlay để ảnh chụp bình thường không bị chậm.
    # Trên Windows 10 DWM xóa frame cũ chậm hơn Windows 11 nên cần thời gian dài.
    settle_ms = int(getattr(settings, "SCREENSHOT_OVERLAY_SETTLE_MS", 0))
    if settle_ms > 0 and (overlay_rects or hidden_hwnds):
        time.sleep(settle_ms / 1000.0)

    try:
        with mss.mss() as sct:
            # Kiểm tra chỉ số màn hình hợp lệ
            if monitor_index < 0 or monitor_index >= len(sct.monitors):
                monitor_index = 0  # Mặc định lấy monitor tổng nếu index vượt giới hạn

            monitor = sct.monitors[monitor_index]
            sct_img = sct.grab(monitor)

            # Chuyển đổi dữ liệu raw pixels từ mss sang Pillow Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # Lớp phòng thủ 2: che (tô đè) các cửa sổ UI overlay của CHÍNH Agent
            # khỏi ảnh đã chụp — dùng toạ độ ghi nhận TRƯỚC khi ẩn để bắt CẢ
            # ghost frame (DWM Windows 10 vẫn giữ frame cũ của popup đã ẩn).
            _mask_overlay_windows(img, monitor, overlay_rects)

            # Lưu ảnh vào bộ nhớ tạm RAM (BytesIO) với nén JPEG
            buffer = io.BytesIO()
            img.save(
                buffer, 
                format="JPEG", 
                quality=settings.JPEG_QUALITY, 
                optimize=True
            )
            buffer.seek(0)

            # Mã hóa Bytes sang dạng chuỗi Base64 ASCII
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            logger.info(
                f"📸 Đã chụp màn hình [{monitor_index}] ({img.width}x{img.height}) | "
                f"Chất lượng JPEG: {settings.JPEG_QUALITY}% | Dung lượng: {len(img_base64) // 1024} KB"
            )

            return {
                "success": True,
                "image_base64": img_base64,
                "width": img.width,
                "height": img.height,
                "message": "Chụp màn hình thành công."
            }

    except Exception as e:
        err_msg = f"Lỗi khi chụp màn hình: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {
            "success": False,
            "image_base64": "",
            "width": 0,
            "height": 0,
            "message": err_msg
        }
    finally:
        # Khôi phục lại các overlay UI đã ẩn tạm (popup, đèn báo đỏ...)
        _restore_overlays(hidden_hwnds)


# =============================================================================
# BLOCK TEST ĐỘC LẬP
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- TEST MODULE SCREENSHOT ---")
    
    result = take_screenshot(0)
    if result["success"]:
        print(f"✅ Thành công! Kích thước: {result['width']}x{result['height']}")
        print(f"Độ dài chuỗi Base64: {len(result['image_base64'])} chars")
        print(f"Ví dụ 50 ký tự đầu Base64: {result['image_base64'][:50]}...")
    else:
        print(f"❌ Thất bại: {result['message']}")