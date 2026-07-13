# web-app/backend/routers/modules.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# 🚪 Tạo phòng riêng quản lý lệnh điều khiển của đầy đủ 8 module
router = APIRouter(prefix="/api/modules", tags=["Modules Control"])

# --- 📦 KHUÔN MẪU DỮ LIỆU ĐẦU VÀO (REQUEST BODY) ---
class KillProcessRequest(BaseModel):
    machine_id: str
    pid: int
    process_name: str

class PowerRequest(BaseModel):
    machine_id: str
    action: str

class FileActionRequest(BaseModel):
    machine_id: str
    path: str
    action: str # "download", "upload", "delete", "view"


# --- ⚙️ 1. MODULE PROCESSES (TIẾN TRÌNH) ---
@router.post("/kill-process")
def kill_process(data: KillProcessRequest):
    return {
        "status": "success",
        "message": f"Đã phát lệnh dừng tiến trình {data.process_name} (PID: {data.pid}) trên máy {data.machine_id}."
    }


# --- 🔌 2. MODULE POWER CONTROL (NGUỒN MÁY) ---
@router.post("/power")
def power_control(data: PowerRequest):
    if data.action not in ["shutdown", "restart"]:
        raise HTTPException(status_code=400, detail="Hành động nguồn không hợp lệ!")
    return {
        "status": "success",
        "message": f"Đã phát lệnh {data.action.upper()} tới thiết bị {data.machine_id}."
    }


# --- 📁 3. MODULE FILE EXPLORER (QUẢN LÝ FILE) ---
@router.post("/files")
def file_control(data: FileActionRequest):
    return {
        "status": "success",
        "message": f"Đã thực hiện hành động [{data.action.upper()}] tại đường dẫn '{data.path}' của máy {data.machine_id}."
    }


# --- 📺 4. MODULE LIVE SCREEN (YÊU CẦU CHỤP MÀN HÌNH CHỦ ĐỘNG) ---
@router.get("/screen/{machine_id}")
def trigger_screen_capture(machine_id: str):
    # Trả về một link ảnh mới sau khi ra lệnh chụp
    return {
        "status": "success",
        "machine_id": machine_id,
        "screenshot_url": f"https://via.placeholder.com/800x450.png?text=Screen+Captured+From+{machine_id}"
    }


# --- ⌨️ 5. MODULE KEYLOGGER (LẤY NHẬT KÝ PHÍM BẤM) ---
@router.get("/keylogger/{machine_id}")
def get_keylogger_logs(machine_id: str):
    return {
        "status": "success",
        "machine_id": machine_id,
        "logs": f"--- Nhật ký từ máy {machine_id} ---\n[User gõ]: gmail.com\n[User gõ]: matkhauhuywiet\n[Hệ thống]: Mở Word"
    }


# --- 📦 6. MODULE APPLICATIONS (DANH SÁCH PHẦN MỀM) ---
@router.get("/applications/{machine_id}")
def get_installed_applications(machine_id: str):
    return {
        "status": "success",
        "machine_id": machine_id,
        "apps": [
            {"name": "Google Chrome", "Developer": "Google LLC", "Version": "120.0"},
            {"name": "Python 3.10", "Developer": "Python Software Foundation", "Version": "3.10.5"},
            {"name": "AnyDesk", "Developer": "AnyDesk Software GmbH", "Version": "7.1.13"}
        ]
    }


# --- 📷 7. MODULE WEBCAM (YÊU CẦU BẬT CỦA WEBCAM) ---
@router.get("/webcam/{machine_id}/toggle")
def toggle_webcam(machine_id: str, active: bool):
    status_str = "MỞ" if active else "TẮT"
    return {
        "status": "success",
        "message": f"Đã gửi yêu cầu {status_str} Webcam trên máy {machine_id}."
    }


# --- 🎙️ 8. MODULE AUDIO MONITOR (GIÁM SÁT ÂM THANH) ---
@router.get("/audio/{machine_id}/toggle")
def toggle_audio_monitor(machine_id: str, active: bool):
    status_str = "BẬT CHẾ ĐỘ GHI ÂM" if active else "TẮT GHI ÂM"
    return {
        "status": "success",
        "message": f"Đã gửi lệnh {status_str} gửi về hệ thống từ máy {machine_id}."
    }