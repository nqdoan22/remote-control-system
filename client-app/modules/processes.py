"""
===============================================================================
FILE: client-app/modules/processes.py
PURPOSE: Quản lý và tương tác với các Tiến trình (Processes) đang chạy trên OS.
ARCHITECTURE ROLE:
  - Module thực thi trực tiếp (Direct Execution) - Không yêu cầu User Consent.
  - Sử dụng thư viện `psutil` để thu thập thông tin hệ thống an toàn.
  - Trả về dữ liệu dạng List/Dict chuẩn để Gateway dễ dàng serialize sang JSON.
===============================================================================
"""

import logging
from typing import List, Dict, Any, Optional
import psutil

logger = logging.getLogger("ProcessModule")


def list_processes() -> List[Dict[str, Any]]:
    """
    Lấy danh sách toàn bộ các tiến trình (Processes) đang hoạt động trên máy tính.
    
    Returns:
        List[Dict[str, Any]]: Danh sách các dictionary chứa thông tin chi tiết từng tiến trình.
        Cấu trúc mỗi dict:
        {
            "pid": int,
            "name": str,
            "username": str,
            "cpu_percent": float,
            "memory_percent": float,
            "memory_mb": float,
            "status": str
        }
    """
    process_list: List[Dict[str, Any]] = []

    # psutil.process_iter lấy thông tin tối ưu bằng cách chỉ quét các field yêu cầu
    for proc in psutil.process_iter([
        'pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status'
    ]):
        try:
            pinfo = proc.info
            
            # Làm tròn các chỉ số phần trăm để dữ liệu JSON gọn nhẹ hơn
            cpu_usage = round(pinfo.get('cpu_percent') or 0.0, 1)
            mem_usage = round(pinfo.get('memory_percent') or 0.0, 1)

            # Tính dung lượng RAM thực tế (MB) từ RSS để Frontend Processes.jsx
            # hiển thị cột "RAM Usage (MB)" (Frontend đọc field `memory_mb`).
            try:
                mem_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
            except Exception:
                mem_mb = 0.0
            
            process_list.append({
                "pid": pinfo['pid'],
                "name": pinfo['name'] or "Unknown",
                "username": pinfo.get('username') or "N/A",
                "cpu_percent": cpu_usage,
                "memory_percent": mem_usage,
                "memory_mb": mem_mb,
                "status": pinfo.get('status') or "unknown"
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Bỏ qua các tiến trình hệ thống bị khóa quyền hoặc đã tự kết thúc trong lúc quét
            continue
        except Exception as e:
            logger.error(f"Lỗi khi đọc thông tin tiến trình PID {proc.pid}: {str(e)}")
            continue

    logger.info(f"📊 Đã quét thành công {len(process_list)} tiến trình đang chạy.")
    return process_list


def kill_process(pid: int) -> Dict[str, Any]:
    """
    Tắt một tiến trình dựa trên Process ID (PID).
    
    Args:
        pid (int): Mã PID của tiến trình cần dừng.
        
    Returns:
        Dict[str, Any]: Kết quả thực thi {"success": bool, "message": str}
    """
    try:
        if not psutil.pid_exists(pid):
            return {
                "success": False,
                "message": f"Không tìm thấy tiến trình với PID = {pid}."
            }

        proc = psutil.Process(pid)
        proc_name = proc.name()
        
        # Thử kết thúc êm đẹp bằng terminate(), nếu không phản hồi mới dùng kill()
        proc.terminate()
        
        # Chờ tối đa 2 giây để tiến trình đóng hẳn
        _, alive = psutil.wait_procs([proc], timeout=2.0)
        
        if alive:
            # Bắt buộc dừng nếu tiến trình cứng đầu
            proc.kill()

        logger.info(f"🛑 Đã dừng thành công tiến trình: {proc_name} (PID: {pid})")
        return {
            "success": True,
            "message": f"Đã tắt thành công tiến trình '{proc_name}' (PID: {pid})."
        }

    except psutil.AccessDenied:
        err_msg = f"Từ chối truy cập! Không đủ quyền System/Admin để tắt PID {pid}."
        logger.warning(f"⚠️ {err_msg}")
        return {"success": False, "message": err_msg}

    except psutil.NoSuchProcess:
        return {
            "success": True,
            "message": f"Tiến trình PID {pid} đã tự kết thúc trước đó."
        }

    except Exception as e:
        err_msg = f"Lỗi không xác định khi tắt PID {pid}: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {"success": False, "message": err_msg}


# =============================================================================
# BLOCK TEST ĐỘC LẬP (Chạy trực tiếp file này để kiểm tra logic)
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- TEST MODULE PROCESSES ---")
    
    # 1. Test Lấy danh sách
    procs = list_processes()
    print(f"\nTop 5 tiến trình đầu tiên (Tổng số: {len(procs)}):")
    for p in procs[:5]:
        print(f" - PID: {p['pid']:<6} | Name: {p['name']:<25} | CPU: {p['cpu_percent']}% | RAM: {p['memory_percent']}%")
        
    # 2. Test thử Kill tiến trình không tồn tại
    test_kill = kill_process(999999)
    print(f"\nTest kill PID giả lập: {test_kill}")