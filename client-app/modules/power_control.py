"""
===============================================================================
FILE: client-app/modules/power_control.py
PURPOSE: Điều khiển Trạng thái Nguồn điện & Hệ thống Windows (Lock, Shutdown, Restart, Sleep).
ARCHITECTURE ROLE:
  - Module tác động Hệ thống (System-Level Control).
  - BẮT BUỘC phải đi qua PermissionService (Popup Consent) trước khi thực thi.
  - Sử dụng Windows Native API (ctypes) và System Commands (subprocess).
===============================================================================
"""

import ctypes
import logging
import subprocess
from typing import Dict, Any

logger = logging.getLogger("PowerControlModule")


def lock_screen() -> Dict[str, Any]:
    """
    Khóa màn hình máy tính ngay lập tức (Tương đương Windows + L).
    
    Returns:
        Dict[str, Any]: {"success": bool, "message": str}
    """
    try:
        # Gọi Windows API User32
        result = ctypes.windll.user32.LockWorkStation()
        if result != 0:
            logger.info("🔒 Đã khóa màn hình máy tính thành công.")
            return {"success": True, "message": "Đã khóa màn hình Client."}
        else:
            err_msg = "Không thể gọi hàm LockWorkStation từ Windows API."
            logger.error(f"❌ {err_msg}")
            return {"success": False, "message": err_msg}

    except Exception as e:
        err_msg = f"Lỗi khi khóa màn hình: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}


def shutdown_system(delay_seconds: int = 0) -> Dict[str, Any]:
    """
    Tắt máy tính Client.
    
    Args:
        delay_seconds (int): Thời gian chờ (giây) trước khi tắt. Mặc định = 0 (tắt ngay).
        
    Returns:
        Dict[str, Any]: {"success": bool, "message": str}
    """
    try:
        cmd = f"shutdown /s /t {max(0, delay_seconds)} /f"
        subprocess.run(cmd, shell=True, check=True)
        
        msg = f"Lệnh tắt máy đã được phát hành (Thời gian chờ: {delay_seconds}s)."
        logger.info(f"🔌 {msg}")
        return {"success": True, "message": msg}

    except subprocess.CalledProcessError as e:
        err_msg = f"Không thể thực thi lệnh tắt máy: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}
    except Exception as e:
        err_msg = f"Lỗi không xác định khi tắt máy: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}


def restart_system(delay_seconds: int = 0) -> Dict[str, Any]:
    """
    Khởi động lại (Restart) máy tính Client.
    
    Args:
        delay_seconds (int): Thời gian chờ (giây) trước khi restart. Mặc định = 0.
        
    Returns:
        Dict[str, Any]: {"success": bool, "message": str}
    """
    try:
        cmd = f"shutdown /r /t {max(0, delay_seconds)} /f"
        subprocess.run(cmd, shell=True, check=True)
        
        msg = f"Lệnh khởi động lại máy đã được phát hành (Thời gian chờ: {delay_seconds}s)."
        logger.info(f"🔄 {msg}")
        return {"success": True, "message": msg}

    except subprocess.CalledProcessError as e:
        err_msg = f"Không thể thực thi lệnh khởi động lại: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}
    except Exception as e:
        err_msg = f"Lỗi không xác định khi khởi động lại: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}


def abort_shutdown() -> Dict[str, Any]:
    """
    Hủy lệnh tắt máy hoặc khởi động lại đang trong trạng thái đếm ngược.
    
    Returns:
        Dict[str, Any]: {"success": bool, "message": str}
    """
    try:
        subprocess.run("shutdown /a", shell=True, check=True)
        logger.info("🛑 Đã hủy lệnh tắt/khởi động lại máy thành công.")
        return {"success": True, "message": "Đã hủy tiến trình tắt/khởi động lại máy."}
    except subprocess.CalledProcessError:
        return {"success": False, "message": "Không có tiến trình tắt máy nào đang đếm ngược để hủy."}
    except Exception as e:
        return {"success": False, "message": f"Lỗi khi hủy lệnh: {str(e)}"}


def sleep_system() -> Dict[str, Any]:
    """
    Đưa máy tính vào chế độ Sleep (Tạm dừng).
    
    Returns:
        Dict[str, Any]: {"success": bool, "message": str}
    """
    try:
        # SetSuspendState(bHibernate=0, bForce=1, bWakeupEventsDisabled=0)
        # Tham số 0 đầu tiên đại diện cho Sleep (Thay vì 1 là Hibernate)
        result = ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        if result != 0:
            logger.info("🌙 Đã đưa máy tính vào chế độ Sleep.")
            return {"success": True, "message": "Đã chuyển Client sang chế độ Sleep."}
        else:
            # Nếu powrprof thất bại, dùng fallback qua rundll32
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return {"success": True, "message": "Đã phát lệnh Sleep qua rundll32."}

    except Exception as e:
        err_msg = f"Lỗi khi đưa máy vào chế độ Sleep: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}


# =============================================================================
# BLOCK TEST ĐỘC LẬP
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- TEST MODULE POWER CONTROL ---")
    print("⚠️ Chú ý: Các hàm Shutdown/Restart/Sleep sẽ thực sự tác động lên máy bạn!")
    
    # Bạn có thể bỏ comment dòng bên dưới để test thử khóa màn hình (An toàn tuyệt đối):
    # print("\n1. Test Khóa màn hình...")
    # res = lock_screen()
    # print(res)

    # Test hẹn giờ shutdown 60s rồi hủy ngay lập tức để kiểm tra logic
    print("\n2. Test hẹn giờ tắt máy sau 60s:")
    shutdown_res = shutdown_system(delay_seconds=60)
    print(shutdown_res)

    print("\n3. Thử hủy lệnh tắt máy ngay lập tức:")
    abort_res = abort_shutdown()
    print(abort_res)