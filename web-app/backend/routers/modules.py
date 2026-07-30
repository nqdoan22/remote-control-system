"""
===============================================================================
FILE: web-app/backend/routers/modules.py
PURPOSE: API Router quản lý và điều khiển 8 Module chức năng tới các máy Agent.
ARCHITECTURE ROLE:
  - Đóng vai trò là "Bộ điều khiển trung tâm" (Command Dispatcher).
  - Tiếp nhận yêu cầu điều khiển từ Web Frontend (Admin).
  - Ghi nhật ký thao tác (AuditLog) vào CSDL để phục vụ kiểm toán an toàn thông tin.
  - Đóng gói lệnh thành tin nhắn chuẩn và gửi tới Agent thông qua WebSocket Gateway.
===============================================================================
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User, AuditLog, Machine
from core.security import get_current_user
from core.gateway_client import gateway_client

logger = logging.getLogger("ModulesRouter")
router = APIRouter(prefix="/modules", tags=["Module Controls"])


# =========================================================================
# 📌 KHAI BÁO CÁC PYDANTIC SCHEMAS CHO DỮ LIỆU ĐẦU VÀO (REQUEST BODIES)
# =========================================================================

class AppControlRequest(BaseModel):
    machine_id: str = Field(..., description="Mã định danh của máy Agent")
    action: str = Field(..., description="Hành động: 'list', 'start', 'stop'")
    app_name: Optional[str] = Field(None, description="Tên ứng dụng cần chạy hoặc dừng")

class ProcessControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'list', 'kill'")
    pid: Optional[int] = Field(None, description="Mã PID của tiến trình cần hạ (kill)")

class ScreenshotRequest(BaseModel):
    machine_id: str = Field(...)

class LiveScreenRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'start' hoặc 'stop'")

class KeyloggerControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'start', 'stop', 'get_logs'")

class FileActionRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'list', 'delete', 'download'")
    file_path: Optional[str] = Field(None, description="Đường dẫn file/thư mục trong Sandbox")

class WebcamControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'start', 'stop', 'snapshot'")

class PowerControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Lệnh nguồn: 'lock', 'restart', 'shutdown', 'sleep'")


# =========================================================================
# 🛠 HÀM BỔ TRỢ: GHI AUDIT LOG VÀ BẮN LỆNH QUA GATEWAY
# =========================================================================

async def dispatch_command_and_log(
    db: Session,
    operator: User,
    machine_id: str,
    action_type: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hàm dùng chung hỗ trợ:
    1. Kiểm tra máy Agent có tồn tại và đang Online hay không.
    2. Ghi AuditLog vào CSDL (Trạng thái ban đầu: PENDING).
    3. Đẩy lệnh sang Gateway WebSocket Client để gửi tới Agent.
    """
    # 1. Kiểm tra sự tồn tại của máy Agent
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy máy Agent có ID: {machine_id}"
        )
    
    if machine.status != "online":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Máy Agent '{machine_id}' hiện đang Offline. Không thể thực hiện lệnh!"
        )

    # 2. Tạo bản ghi Nhật ký Thao tác (Audit Log)
    log_entry = AuditLog(
        operator_username=operator.username,
        action=action_type,
        target_machine_id=machine_id,
        status="pending",
        details=str(payload),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log_entry)
    db.commit()

    # 3. Gửi lệnh tới Gateway Server qua kết nối WebSocket Client
    try:
        response = await gateway_client.send_command(
            target_machine_id=machine_id,
            command_type=action_type,
            payload=payload
        )
        # Cập nhật trạng thái Audit Log thành công
        log_entry.status = "success"
        db.commit()
        return response
    except Exception as e:
        logger.error(f"❌ Lỗi truyền lệnh '{action_type}' tới Agent '{machine_id}': {e}")
        log_entry.status = "failed"
        log_entry.details = f"Lỗi: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi giao tiếp Gateway/Agent: {str(e)}"
        )


# =========================================================================
# 🚀 8 MODULE CONTROL ENDPOINTS
# =========================================================================

# --- MODULE 1: APPLICATION CONTROL ---
@router.post("/applications", summary="1. Xem & Quản lý Ứng dụng")
async def control_applications(
    req: AppControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Quản lý ứng dụng: Liệt kê danh sách ứng dụng, %CPU hoặc Start/Stop ứng dụng.
    """
    payload = {"action": req.action, "app_name": req.app_name}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "app.control", payload)


# --- MODULE 2: PROCESS CONTROL ---
@router.post("/processes", summary="2. Liệt kê & Kill Tiến trình")
async def control_processes(
    req: ProcessControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Quản lý tiến trình (psutil): Xem %CPU, %RAM và Tiêu diệt (Kill) Tiến trình theo PID.
    """
    payload = {"action": req.action, "pid": req.pid}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "process.control", payload)


# --- MODULE 3: SCREENSHOT ---
@router.post("/screenshot", summary="3. Chụp ảnh màn hình (Cần User Accept)")
async def control_screenshot(
    req: ScreenshotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chụp ảnh màn hình (Screenshot) và gửi về dạng JPEG base64.
    *Yêu cầu:* Phải có sự xác nhận Pop-up từ phía End-User trên Agent.
    """
    payload = {}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "screen.screenshot", payload)


# --- MODULE 4: LIVE SCREEN ---
@router.post("/live-screen", summary="4. Xem màn hình trực tiếp (Cần User Accept)")
async def control_live_screen(
    req: LiveScreenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xem trực tiếp (Live Stream) màn hình máy Agent.
    *Yêu cầu:* Phải có sự xác nhận Pop-up từ phía End-User trên Agent.
    """
    payload = {"action": req.action}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "screen.live", payload)


# --- MODULE 5: KEYLOGGER ---
@router.post("/keylogger", summary="5. Bắt phím Keylogger (Cần User Accept)")
async def control_keylogger(
    req: KeyloggerControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Theo dõi bàn phím gõ (pynput).
    *Yêu cầu:* Bắt buộc xin phép người dùng Agent trước khi kích hoạt.
    """
    payload = {"action": req.action}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "keylogger.control", payload)


# --- MODULE 6: FILE TRANSFER & MANAGEMENT ---
@router.post("/file/action", summary="6a. Quản lý Tệp tin trong Thư mục Sandbox")
async def control_file_action(
    req: FileActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xem danh sách, xóa hoặc yêu cầu tải file.
    *Ràng buộc an toàn:* Giới hạn chỉ truy cập trong thư mục Sandbox được cấp phép.
    """
    payload = {"action": req.action, "file_path": req.file_path}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "file.action", payload)


@router.post("/file/upload", summary="6b. Tải tệp tin lên máy Agent (Upload)")
async def upload_file_to_agent(
    machine_id: str = Form(...),
    target_dir: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload tệp tin từ Admin Web lên thư mục Sandbox của máy Agent.
    """
    content = await file.read()
    payload = {
        "action": "upload",
        "file_name": file.filename,
        "target_dir": target_dir,
        "file_bytes_len": len(content)
    }
    # Đóng gói và truyền dữ liệu
    return await dispatch_command_and_log(db, current_user, machine_id, "file.upload", payload)


# --- MODULE 7: WEBCAM CONTROL ---
@router.post("/webcam", summary="7. Xem Webcam (Cần User Accept & Chớp đỏ)")
async def control_webcam(
    req: WebcamControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mở Webcam xem ảnh/video.
    *An toàn & Riêng tư:* Phát tín hiệu yêu cầu Pop-up xác nhận và hiển thị chấm chớp đỏ cảnh báo trên máy Agent.
    """
    payload = {"action": req.action}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "webcam.control", payload)


# --- MODULE 8: POWER CONTROL ---
@router.post("/power", summary="8. Điều khiển Nguồn (Lock, Restart, Shutdown, Sleep)")
async def control_power(
    req: PowerControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Khóa màn hình, Khởi động lại, Tắt máy hoặc Chuyển sang chế độ Chờ (Sleep).
    *Yêu cầu:* Xin xác nhận từ người dùng để tránh mất dữ liệu đột ngột.
    """
    payload = {"action": req.action}
    return await dispatch_command_and_log(db, current_user, req.machine_id, "power.control", payload)