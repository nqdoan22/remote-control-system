# client-app/modules/applications.py
import subprocess
import psutil
import logging
import os

logger = logging.getLogger("Module-Applications")

class ApplicationManager:
    """Module quản lý việc khởi chạy hoặc đóng các ứng dụng cụ thể."""
    
    @staticmethod
    def start_app(app_path: str) -> dict:
        """Khởi chạy một ứng dụng (ví dụ: 'calc.exe', 'notepad.exe', hoặc đường dẫn tuyệt đối)."""
        try:
            # Sử dụng subprocess để gọi app mà không làm treo luồng chính của Python
            subprocess.Popen(app_path, shell=True)
            logger.info(f"Đã mở ứng dụng: {app_path}")
            return {"success": True, "message": f"Đã khởi chạy {app_path}"}
        except Exception as e:
            logger.error(f"Lỗi khi mở ứng dụng {app_path}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def stop_app(app_name: str) -> dict:
        """Đóng tất cả các tiến trình có tên trùng khớp với app_name."""
        terminated_count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                    try:
                        psutil.Process(proc.info['pid']).kill()
                        terminated_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            if terminated_count > 0:
                logger.info(f"Đã đóng {terminated_count} tiến trình của {app_name}")
                return {"success": True, "message": f"Đã đóng {terminated_count} ứng dụng {app_name}"}
            else:
                return {"success": False, "error": f"Không tìm thấy ứng dụng nào tên {app_name} đang chạy"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Khởi tạo instance dùng chung
app_manager = ApplicationManager()