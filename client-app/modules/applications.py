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


def close_application(pid: int) -> Dict[str, Any]:
    """
    Tắt một Ứng dụng giao diện dựa vào PID.
    
    Args:
        pid (int): Process ID của ứng dụng cần đóng.
        
    Returns:
        Dict[str, Any]: Kết quả xử lý {"success": bool, "message": str}
    """
    try:
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