# web-app/backend/routers/modules.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import json

from db.database import get_db
from db.models import AuditLog, Machine, User
from core.gateway_client import gateway_client
from routers.auth import get_current_user

router = APIRouter(prefix="/modules", tags=["Modules Control"])

@router.post("/{machine_id}/command")
async def send_module_command(
    machine_id: str, 
    request: Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Xác định ai đang ra lệnh
):
    """
    API đa năng điều khiển 8 chức năng cốt lõi.
    Nhận Payload JSON từ ReactJS, chuyển tiếp sang Gateway và ghi Audit Log.
    """
    body = await request.json()
    action = body.get("action") # VD: 'webcam.start', 'power.shutdown', 'process.kill'
    payload = body.get("payload", {})
    
    # 1. Kiểm tra máy đích có tồn tại trong CSDL không
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Không tìm thấy máy trạm này trong hệ thống")
    
    # 2. Gửi lệnh qua Gateway bằng WebSocket
    result = await gateway_client.send_command(machine_id, action, payload)
    
    # 3. Ghi nhận Audit Log (Vết bảo mật)
    log_status = "Success" if result.get("success") else "Failed"
    
    audit_record = AuditLog(
        admin_id=current_user.id,
        machine_id=machine_id,
        action=action,
        status=log_status,
        details=json.dumps(payload)
    )
    db.add(audit_record)
    db.commit()
    
    # 4. Trả kết quả về cho Frontend React
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return {"message": "Đã chuyển lệnh tới Gateway thành công", "result": result}