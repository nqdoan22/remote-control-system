# client-app/modules/applications.py
import subprocess
import psutil
import logging
import os

logger = logging.getLogger("Module-Applications")

class ApplicationManager:
    """Module quản lý việc khởi chạy hoặc đóng các ứng dụng cụ thể."""
    
    @staticmethod
    def list_apps() -> dict:
        """Liệt kê các ứng dụng có cửa sổ giao diện đang chạy."""
        apps = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    p = psutil.Process(proc.info['pid'])
                    window_title = ""
                    try:
                        window_title = p.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    apps.append({
                        "name": proc.info['name'],
                        "pid": proc.info['pid'],
                        "cpuUsage": proc.info['cpu_percent'] or 0,
                        "mainWindowTitle": window_title
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            logger.info(f"Lấy thành công danh sách {len(apps)} ứng dụng.")
            return {"success": True, "applications": apps}
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách ứng dụng: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def start_app(app_path: str) -> dict:
        """Khởi chạy một ứng dụng (ví dụ: 'calc.exe', 'notepad.exe', hoặc đường dẫn tuyệt đối)."""
        try:
            subprocess.Popen(app_path, shell=True)
            logger.info(f"Đã mở ứng dụng: {app_path}")
            return {"success": True, "message": f"Đã khởi chạy {app_path}"}
        except Exception as e:
            logger.error(f"Lỗi khi mở ứng dụng {app_path}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def stop_app(pid: int) -> dict:
        """Đóng ứng dụng dựa trên PID."""
        try:
            proc = psutil.Process(pid)
            proc.kill()
            logger.info(f"Đã đóng tiến trình PID {pid}.")
            return {"success": True, "message": f"Đã đóng tiến trình {pid}"}
        except psutil.NoSuchProcess:
            return {"success": False, "error": "Tiến trình không tồn tại hoặc đã bị đóng."}
        except psutil.AccessDenied:
            return {"success": False, "error": "Từ chối truy cập. Cần quyền Administrator."}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Khởi tạo instance dùng chung
app_manager = ApplicationManager()