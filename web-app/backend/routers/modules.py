"""
===============================================================================
FILE: web-app/backend/routers/modules.py
PURPOSE: API Router quản lý và điều khiển 8 Module chức năng tới các máy Agent.
ARCHITECTURE ROLE:
  - Đóng vai trò là "Bộ điều khiển trung tâm" (Command Dispatcher).
  - Tiếp nhận yêu cầu điều khiển từ Web Frontend (Admin).
  - Ghi nhật ký thao tác (AuditLog) vào CSDL để phục vụ kiểm toán an toàn thông tin.
  - Đóng gói lệnh thành message type CHÍNH XÁC theo docs/api_contract.md rồi gửi
    tới Agent thông qua WebSocket Gateway (core/gateway_client.py).
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
from core.config import settings

logger = logging.getLogger("ModulesRouter")
router = APIRouter(prefix="/modules", tags=["Module Controls"])


# =========================================================================
# 📌 KHAI BÁO CÁC PYDANTIC SCHEMAS CHO DỮ LIỆU ĐẦU VÀO (REQUEST BODIES)
# Field "action" chỉ là chi tiết REST nội bộ - mỗi action được map 1-1 sang
# đúng message type của Gateway (xem các bảng _*_ACTION_TYPE bên dưới),
# KHÔNG gửi "action" thẳng ra Gateway.
# =========================================================================

class AppControlRequest(BaseModel):
    machine_id: str = Field(..., description="Mã định danh của máy Agent")
    action: str = Field(..., description="Hành động: 'list', 'start', 'stop'")
    path: Optional[str] = Field(None, description="Đường dẫn file .exe cần chạy (dùng cho 'start')")
    pid: Optional[int] = Field(None, description="PID ứng dụng cần dừng (dùng cho 'stop')")


class ProcessControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'list', 'kill'")
    pid: Optional[int] = Field(None, description="Mã PID của tiến trình cần hạ (kill)")


class ScreenshotRequest(BaseModel):
    machine_id: str = Field(...)


class LiveScreenRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'start' hoặc 'stop'")
    fps: Optional[int] = Field(10, description="Số frame/giây (mặc định 10, tối đa 30)")


class KeyloggerControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'start' hoặc 'stop'")


class FileActionRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'list' hoặc 'download'")
    path: Optional[str] = Field("", description="Đường dẫn con (tương đối) bên trong Sandbox; để trống = thư mục gốc")


class WebcamControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Hành động: 'start' hoặc 'stop'")
    fps: Optional[int] = Field(10, description="Số frame/giây (mặc định 10)")


class PowerControlRequest(BaseModel):
    machine_id: str = Field(...)
    action: str = Field(..., description="Lệnh nguồn: 'lock', 'restart', 'shutdown', 'sleep', 'abort'")
    delay_seconds: Optional[int] = Field(0, description="Độ trễ trước khi thực hiện (giây), dùng cho restart/shutdown")


# =========================================================================
# 🗺️ BẢNG MAP action (REST) -> message type CHUẨN theo api_contract.md
# =========================================================================

_APP_ACTION_TYPE = {"list": "application.list", "start": "application.start", "stop": "application.stop"}
_PROCESS_ACTION_TYPE = {"list": "process.list", "kill": "process.kill"}
_LIVESCREEN_ACTION_TYPE = {"start": "screen.live.start", "stop": "screen.live.stop"}
_KEYLOGGER_ACTION_TYPE = {"start": "keylogger.start", "stop": "keylogger.stop"}
_FILE_ACTION_TYPE = {"list": "file.list", "download": "file.download"}
_WEBCAM_ACTION_TYPE = {"start": "webcam.start", "stop": "webcam.stop"}
_POWER_ACTION_TYPE = {
    "lock": "power.lock",
    "restart": "power.restart",
    "shutdown": "power.shutdown",
    "sleep": "power.sleep",
    "abort": "power.abort",  # Hủy lệnh tắt/khởi động lại đang đếm ngược (không cần Consent)
}


def _resolve_type(action_map: Dict[str, str], action: str) -> str:
    """Map action REST -> message type chuẩn. 400 nếu action không hợp lệ/không thuộc giao thức."""
    msg_type = action_map.get(action)
    if msg_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hành động '{action}' không hợp lệ. Các giá trị cho phép: {list(action_map.keys())}",
        )
    return msg_type


# =========================================================================
# 🛠 HÀM BỔ TRỢ: GHI AUDIT LOG VÀ BẮN LỆNH QUA GATEWAY
# =========================================================================

async def dispatch_command_and_log(
    db: Session,
    operator: User,
    machine_id: str,
    action_type: str,
    payload: Dict[str, Any],
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Hàm dùng chung hỗ trợ:
    1. Kiểm tra máy Agent có tồn tại và đang Online hay không.
    2. Ghi AuditLog vào CSDL (Trạng thái ban đầu: PENDING).
    3. Đẩy lệnh sang Gateway WebSocket Client để gửi tới Agent.

    action_type PHẢI là message type chuẩn theo docs/api_contract.md
    (VD: "application.list", "screen.live.start", "power.lock"...).
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
    # (gateway_client.send_command tự đặt payload.destinationMachineId theo
    # Command Routing Convention - xem api_contract.md)
    try:
        response = await gateway_client.send_command(
            target_machine_id=machine_id,
            command_type=action_type,
            payload=payload,
            timeout=timeout,
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
    Quản lý ứng dụng: application.list / application.start / application.stop.
    """
    msg_type = _resolve_type(_APP_ACTION_TYPE, req.action)
    if req.action == "start":
        payload = {"path": req.path}
    elif req.action == "stop":
        payload = {"pid": req.pid}
    else:
        payload = {}
    return await dispatch_command_and_log(db, current_user, req.machine_id, msg_type, payload)


# --- MODULE 2: PROCESS CONTROL ---
@router.post("/processes", summary="2. Liệt kê & Kill Tiến trình")
async def control_processes(
    req: ProcessControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Quản lý tiến trình: process.list / process.kill.
    """
    msg_type = _resolve_type(_PROCESS_ACTION_TYPE, req.action)
    payload = {"pid": req.pid} if req.action == "kill" else {}
    return await dispatch_command_and_log(db, current_user, req.machine_id, msg_type, payload)


# --- MODULE 3: SCREENSHOT ---
@router.post("/screenshot", summary="3. Chụp ảnh màn hình")
async def control_screenshot(
    req: ScreenshotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    screen.screenshot - Thuộc Sensitive Feature List (Consent). Gateway sẽ chặn
    lại và chờ Permission Confirmation từ End User trước khi forward xuống Client
    App -> dùng timeout dài như các lệnh nhạy cảm khác để không timeout hụt.
    """
    # screen.screenshot nằm trong Sensitive Feature List -> có thể chờ Permission Confirmation
    return await dispatch_command_and_log(
        db, current_user, req.machine_id, "screen.screenshot", {},
        timeout=settings.SENSITIVE_COMMAND_TIMEOUT_SECONDS,
    )


# --- MODULE 4: LIVE SCREEN ---
@router.post("/live-screen", summary="4. Xem màn hình trực tiếp (Cần User Accept)")
async def control_live_screen(
    req: LiveScreenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    screen.live.start / screen.live.stop.
    *Yêu cầu:* screen.live.start nằm trong Sensitive Feature List - Gateway sẽ tự
    chặn lại và chờ Permission Confirmation từ End-User trước khi forward.
    """
    msg_type = _resolve_type(_LIVESCREEN_ACTION_TYPE, req.action)
    payload = {"fps": req.fps or 10} if req.action == "start" else {}
    # screen.live.start nằm trong Sensitive Feature List -> Gateway có thể chờ Permission Confirmation
    timeout = settings.SENSITIVE_COMMAND_TIMEOUT_SECONDS if req.action == "start" else None
    return await dispatch_command_and_log(db, current_user, req.machine_id, msg_type, payload, timeout=timeout)


# --- MODULE 5: KEYLOGGER ---
@router.post("/keylogger", summary="5. Bắt phím Keylogger (Cần User Accept)")
async def control_keylogger(
    req: KeyloggerControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    keylogger.start / keylogger.stop.
    *Yêu cầu:* keylogger.start nằm trong Sensitive Feature List.
    """
    msg_type = _resolve_type(_KEYLOGGER_ACTION_TYPE, req.action)
    # keylogger.start nằm trong Sensitive Feature List -> có thể chờ Permission Confirmation
    timeout = settings.SENSITIVE_COMMAND_TIMEOUT_SECONDS if req.action == "start" else None
    return await dispatch_command_and_log(db, current_user, req.machine_id, msg_type, {}, timeout=timeout)


# --- MODULE 6: FILE TRANSFER & MANAGEMENT ---
@router.post("/file/action", summary="6a. Xem/Tải tệp trong Thư mục Sandbox")
async def control_file_action(
    req: FileActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    file.list / file.download. Chỉ thao tác trong sandbox folder (theo security_design.md).
    """
    msg_type = _resolve_type(_FILE_ACTION_TYPE, req.action)
    payload = {"path": req.path or ""}
    # file.download có thể chứa tới 50MB base64 (api_contract.md) -> cần timeout dài hơn mặc định
    file_timeout = 60 if req.action == "download" else None
    return await dispatch_command_and_log(db, current_user, req.machine_id, msg_type, payload, timeout=file_timeout)


@router.post("/file/upload", summary="6b. Tải tệp tin lên máy Agent (Upload)")
async def upload_file_to_agent(
    machine_id: str = Form(...),
    destination_path: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    file.upload - payload theo đúng api_contract.md:
    { destinationPath, filename, content (base64), sizeBytes }.
    """
    import base64

    content = await file.read()
    payload = {
        "destinationPath": destination_path,
        "filename": file.filename,
        "content": base64.b64encode(content).decode("ascii"),
        "sizeBytes": len(content),
    }
    return await dispatch_command_and_log(db, current_user, machine_id, "file.upload", payload, timeout=60)


# --- MODULE 7: WEBCAM CONTROL ---
@router.post("/webcam", summary="7. Xem Webcam (Cần User Accept & Chớp đỏ)")
async def control_webcam(
    req: WebcamControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    webcam.start / webcam.stop.
    *Yêu cầu:* webcam.start nằm trong Sensitive Feature List.
    """
    msg_type = _resolve_type(_WEBCAM_ACTION_TYPE, req.action)
    payload = {"fps": req.fps or 10} if req.action == "start" else {}
    # webcam.start nằm trong Sensitive Feature List -> có thể chờ Permission Confirmation
    timeout = settings.SENSITIVE_COMMAND_TIMEOUT_SECONDS if req.action == "start" else None
    return await dispatch_command_and_log(db, current_user, req.machine_id, msg_type, payload, timeout=timeout)


# --- MODULE 8: POWER CONTROL ---
@router.post("/power", summary="8. Điều khiển Nguồn (Lock, Restart, Shutdown, Sleep)")
async def control_power(
    req: PowerControlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    power.lock / power.restart / power.shutdown / power.sleep.
    *Yêu cầu:* Toàn bộ Power Control nằm trong Sensitive Feature List.
    """
    msg_type = _resolve_type(_POWER_ACTION_TYPE, req.action)
    payload = {"delaySeconds": req.delay_seconds or 0} if req.action in ("restart", "shutdown") else {}
    # lock/restart/shutdown/sleep nằm trong Sensitive Feature List -> Gateway chờ
    # Permission Confirmation nên cần timeout dài. Riêng 'abort' KHÔNG nhạy cảm
    # (được forward trực tiếp), phản hồi nhanh nên dùng timeout mặc định.
    timeout = None if req.action == "abort" else settings.SENSITIVE_COMMAND_TIMEOUT_SECONDS
    return await dispatch_command_and_log(
        db, current_user, req.machine_id, msg_type, payload,
        timeout=timeout,
    )
