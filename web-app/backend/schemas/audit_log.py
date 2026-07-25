# web-app/backend/schemas/audit_log.py
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any, Dict

# ==========================================
# SCHEMAS CHO NHẬT KÝ HỆ THỐNG (AUDIT LOGS)
# ==========================================

class AuditLogBase(BaseModel):
    """
    Thông tin cốt lõi của một bản ghi lịch sử thao tác.
    """
    admin_id: int = Field(..., description="ID của Admin thực hiện lệnh")
    machine_id: str = Field(..., description="Máy Client bị điều khiển")
    action: str = Field(..., description="Hành động (VD: 'webcam.start', 'process.kill', 'file.upload')")
    
    # Trạng thái theo thiết kế hệ thống (Success, Failed, User_Denied, Timeout)
    status: str = Field(..., description="Kết quả của lệnh (VD: 'Success', 'User_Denied', 'Timeout')")
    
    # details chứa tham số lệnh, ví dụ: {"pid": 1234} hoặc {"path": "C:\\AgentSandbox"}
    # Có thể là một chuỗi JSON hoặc một Dictionary (Tùy thuộc vào Database)
    details: Optional[str] = Field(None, description="Chi tiết tham số của lệnh dưới dạng chuỗi JSON")

class AuditLogCreate(AuditLogBase):
    """
    Schema sử dụng khi Backend bắt đầu ghi nhận log vào DB.
    """
    pass

class AuditLogResponse(AuditLogBase):
    """
    Schema trả về cho Frontend để hiển thị trong bảng Nhật ký hệ thống.
    Bao gồm cả ID tự tăng và Thời gian chính xác.
    """
    id: int
    timestamp: datetime = Field(..., description="Thời gian ghi nhận log")

    model_config = ConfigDict(from_attributes=True)