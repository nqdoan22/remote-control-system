# client-app/modules/processes.py
import psutil
import logging

logger = logging.getLogger("Module-Processes")

class ProcessManager:
    """Module quản lý các tiến trình đang chạy (Task Manager thu nhỏ)."""
    
    @staticmethod
    def list_processes() -> dict:
        """Lấy danh sách tất cả các tiến trình đang chạy kèm thông số CPU/RAM."""
        processes = []
        try:
            # Lặp qua tất cả các tiến trình
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    # Chuyển đổi bộ nhớ từ Byte sang Megabyte (MB)
                    memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_percent": proc.info['cpu_percent'],
                        "ram_mb": round(memory_mb, 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Bỏ qua các tiến trình hệ thống không cho phép truy cập
                    pass
            logger.info(f"Lấy thành công danh sách {len(processes)} tiến trình.")
            return {"success": True, "processes": processes}
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách tiến trình: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def kill_process(pid: int) -> dict:
        """Buộc dừng (Kill) một tiến trình dựa trên ID (PID)."""
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
process_manager = ProcessManager()