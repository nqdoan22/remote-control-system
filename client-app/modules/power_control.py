# client-app/modules/power_control.py
import os
import logging
import platform

logger = logging.getLogger("Module-PowerControl")

class PowerControl:
    """Module điều khiển Nguồn (Tắt máy, Khởi động lại, Khóa màn hình, Ngủ)."""
    
    @staticmethod
    def execute(action: str) -> dict:
        """Thực thi lệnh điều khiển nguồn (Chỉ hỗ trợ tối ưu trên Windows)."""
        current_os = platform.system()
        if current_os != "Windows":
            return {"success": False, "error": f"Chức năng này chưa hỗ trợ hệ điều hành {current_os}"}

        try:
            if action == "shutdown":
                # Tắt máy ngay lập tức (0 giây)
                os.system("shutdown /s /t 0")
                message = "Đang tắt máy..."
            elif action == "restart":
                # Khởi động lại máy (0 giây)
                os.system("shutdown /r /t 0")
                message = "Đang khởi động lại..."
            elif action == "lock":
                # Khóa màn hình làm việc
                os.system("rundll32.exe user32.dll,LockWorkStation")
                message = "Đã khóa màn hình"
            elif action == "sleep":
                # Đưa máy vào chế độ ngủ (Hibernation/Sleep)
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                message = "Đang vào chế độ ngủ..."
            else:
                return {"success": False, "error": f"Lệnh nguồn không hợp lệ: {action}"}

            logger.info(f"Đã thực thi lệnh nguồn: {action}")
            return {"success": True, "message": message}
            
        except Exception as e:
            logger.error(f"Lỗi khi thực thi lệnh {action}: {e}")
            return {"success": False, "error": str(e)}

# Khởi tạo instance dùng chung
power_manager = PowerControl()