"""
===============================================================================
FILE: client-app/modules/applications.py
PURPOSE: Quản lý các Ứng dụng có giao diện (GUI Applications) đang mở trên Windows.
ARCHITECTURE ROLE:
  - Module thực thi trực tiếp (Direct Execution) - Tương tác cấp OS.
  - Lọc bỏ các tiến trình hệ thống ngầm, chỉ lấy các cửa sổ UI hiển thị cho người dùng.
  - Hỗ trợ xem danh sách Cửa sổ, Khởi chạy ứng dụng mới và Đóng ứng dụng.
===============================================================================
"""

import ctypes
from ctypes import wintypes
import logging
import subprocess
from typing import List, Dict, Any, Optional
import psutil

logger = logging.getLogger("ApplicationModule")

# Import các hàm Windows API từ thư viện ctypes tích hợp sẵn của Python
user32 = ctypes.windll.user32

# Định nghĩa kiểu dữ liệu Callback cho EnumWindows API
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

# WM_CLOSE: thông điệp Windows tương đương với việc người dùng bấm nút X trên
# cửa sổ — yêu cầu cửa sổ tự đóng một cách êm ái, KHÔNG giết cả tiến trình.
WM_CLOSE = 0x0010


def _get_window_title(hwnd: int) -> str:
    """Hàm bổ trợ lấy Tiêu đề (Title) của một Handle Cửa sổ (HWND)."""
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _get_window_pid(hwnd: int) -> int:
    """Hàm bổ trợ lấy Process ID (PID) sở hữu Handle Cửa sổ (HWND)."""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def list_applications() -> List[Dict[str, Any]]:
    """
    Quét và trả về danh sách các Ứng dụng đang hiển thị cửa sổ giao diện trên màn hình.
    
    Returns:
        List[Dict[str, Any]]: Danh sách ứng dụng GUI. Cấu trúc mỗi item:
        {
            "pid": int,
            "app_name": str,
            "window_title": str,
            "hwnd": int
        }
    """
    applications: List[Dict[str, Any]] = []

    def enum_windows_callback(hwnd: int, lparam: int) -> bool:
        # 1. Kiểm tra cửa sổ có đang Bật hiển thị (Visible) hay không
        if not user32.IsWindowVisible(hwnd):
            return True

        # 2. Kiểm tra cửa sổ có tiêu đề (Title) hợp lệ hay không
        title = _get_window_title(hwnd)
        if not title.strip():
            return True

        # 3. Lọc bỏ các cửa sổ ẩn đặc biệt của Windows (Tool Windows, System overlays)
        # Style WS_EX_TOOLWINDOW thường dùng cho tooltip/system tray icon
        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        if ex_style & WS_EX_TOOLWINDOW:
            return True

        # 4. Lấy thông tin Tiến trình (PID & App Name) từ HWND
        pid = _get_window_pid(hwnd)
        app_name = "Unknown"
        try:
            proc = psutil.Process(pid)
            app_name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        applications.append({
            "pid": pid,
            "app_name": app_name,
            "window_title": title,
            "hwnd": hwnd
        })
        return True

    try:
        # Duyệt qua toàn bộ danh sách cửa sổ của Windows OS
        callback = WNDENUMPROC(enum_windows_callback)
        user32.EnumWindows(callback, 0)
        logger.info(f"💻 Đã tìm thấy {len(applications)} ứng dụng GUI đang hoạt động.")
    except Exception as e:
        logger.error(f"❌ Lỗi khi duyệt danh sách ứng dụng GUI: {str(e)}")

    return applications


def launch_application(app_command: str) -> Dict[str, Any]:
    """
    Khởi chạy một ứng dụng mới trên máy Client.
    
    Args:
        app_command (str): Tên lệnh (VD: 'calc.exe', 'notepad.exe') 
                           hoặc Đường dẫn tuyệt đối (VD: 'C:\\Program Files\\...\\chrome.exe').
                           
    Returns:
        Dict[str, Any]: Kết quả khởi chạy {"success": bool, "message": str, "pid": Optional[int]}
    """
    try:
        # Popen mở tiến trình độc lập không làm treo/block Client App
        proc = subprocess.Popen(app_command, shell=True)
        logger.info(f"🚀 Đã phát lệnh khởi chạy ứng dụng: '{app_command}' (PID dự kiến: {proc.pid})")
        
        return {
            "success": True,
            "message": f"Đã khởi chạy thành công lệnh '{app_command}'.",
            "pid": proc.pid
        }
    except Exception as e:
        err_msg = f"Không thể mở ứng dụng '{app_command}': {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {
            "success": False,
            "message": err_msg,
            "pid": None
        }


def _close_window_gracefully(hwnd: int) -> bool:
    """
    Gửi thông điệp WM_CLOSE tới ĐÚNG MỘT cửa sổ (theo HWND) để yêu cầu nó tự đóng.

    Quan trọng: WM_CLOSE tương đương bấm nút X — chỉ đóng cửa sổ đó, KHÔNG giết
    tiến trình. Điều này rất cần thiết cho các app đa cửa sổ dùng chung MỘT
    process (Chrome/Edge/Firefox...): nếu dùng terminate() toàn bộ tiến trình,
    mọi cửa sổ/tab của app đó đều bị đóng cùng lúc.

    Returns:
        bool: True nếu đã gửi WM_CLOSE thành công, False nếu cửa sổ không còn tồn tại.
    """
    if not user32.IsWindow(hwnd):
        return False
    # PostMessage (bất đồng bộ, không chờ) để không block luồng của Client App
    return bool(user32.PostMessageW(hwnd, WM_CLOSE, 0, 0))


def close_application(pid: int, hwnd: Optional[int] = None) -> Dict[str, Any]:
    """
    Tắt một cửa sổ ứng dụng (ưu tiên theo HWND) hoặc cả tiến trình (theo PID).

    Args:
        pid (int): Process ID của ứng dụng cần đóng.
        hwnd (Optional[int]): Handle cửa sổ CỤ THỂ cần đóng (từ application.list).
            - Nếu có hwnd: chỉ gửi WM_CLOSE tới đúng cửa sổ đó -> chỉ đóng 1 cửa sổ,
              an toàn với Chrome/Edge đang mở nhiều cửa sổ chung 1 process.
            - Nếu None: giữ hành vi cũ, terminate() cả tiến trình (đóng hết mọi
              cửa sổ thuộc tiến trình đó).

    Returns:
        Dict[str, Any]: Kết quả xử lý {"success": bool, "message": str}
    """
    try:
        # Trường hợp 1: Có hwnd -> đóng ĐÚNG cửa sổ đó (không đụng tới cửa sổ khác).
        if hwnd is not None:
            if _close_window_gracefully(hwnd):
                logger.info(f"🛑 Đã gửi WM_CLOSE tới cửa sổ hwnd={hwnd} của PID {pid}.")
                return {
                    "success": True,
                    "message": f"Đã gửi yêu cầu đóng cửa sổ (hwnd={hwnd})."
                }
            # Cửa sổ đã không còn tồn tại -> coi như đã đóng (idempotent).
            return {
                "success": True,
                "message": f"Cửa sổ hwnd={hwnd} đã được đóng trước đó."
            }

        # Trường hợp 2: Không có hwnd -> đóng cả tiến trình theo PID (hành vi cũ).
        if not psutil.pid_exists(pid):
            return {
                "success": False,
                "message": f"Không tìm thấy ứng dụng với PID = {pid}."
            }

        proc = psutil.Process(pid)
        app_name = proc.name()

        # Đóng êm bằng terminate() trước
        proc.terminate()
        _, alive = psutil.wait_procs([proc], timeout=2.0)

        # Nếu chưa đóng thì ép đóng bằng kill()
        if alive:
            proc.kill()

        logger.info(f"🛑 Đã đóng thành công ứng dụng: {app_name} (PID: {pid})")
        return {
            "success": True,
            "message": f"Đã đóng ứng dụng '{app_name}' (PID: {pid})."
        }
    except psutil.AccessDenied:
        err_msg = f"Không đủ quyền Administrator để đóng PID {pid}."
        logger.warning(f"⚠️ {err_msg}")
        return {"success": False, "message": err_msg}
    except Exception as e:
        err_msg = f"Lỗi khi đóng ứng dụng PID {pid}: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}


# =============================================================================
# BLOCK TEST ĐỘC LẬP (Chạy trực tiếp file này để kiểm tra)
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- TEST MODULE APPLICATIONS ---")

    # 1. Quét danh sách Ứng dụng GUI
    apps = list_applications()
    print(f"\nDanh sách cửa sổ ứng dụng đang mở ({len(apps)} ứng dụng):")
    for a in apps:
        print(f" - PID: {a['pid']:<6} | Executable: {a['app_name']:<20} | Title: {a['window_title']}")

    # 2. Test mở Notepad
    print("\nĐang thử mở Notepad...")
    res = launch_application("notepad.exe")
    print(f"Kết quả: {res}")