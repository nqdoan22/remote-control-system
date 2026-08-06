"""
===============================================================================
FILE: web-app/backend/schemas/audit_log.py
PURPOSE: Định nghĩa các Pydantic Schemas cho hệ thống Nhật ký hệ thống (Audit Log).
ARCHITECTURE ROLE: 
  - Đóng vai trò Data Contract quản lý việc ghi nhận mọi thao tác của Admin 
    (VD: mở webcam, khóa máy, gửi lệnh) và truy xuất lịch sử để hiển thị trên 
    trang Audit Log của Frontend.
===============================================================================
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AuditAction(str, Enum):
    """
    Enum quy định danh mục các hành động (Event Actions) có thể diễn ra trong hệ thống.
    Giúp chuẩn hóa dữ liệu, tránh việc ghi nhầm tên hành động vào Database.
    """
    LOGIN = "login"                     # Admin đăng nhập
    LOGOUT = "logout"                   # Admin đăng xuất
    LOCK_MACHINE = "lock_machine"       # Gửi lệnh khóa máy Client
    UNLOCK_MACHINE = "unlock_machine"   # Gửi lệnh mở khóa máy Client
    START_STREAM = "start_stream"       # Bắt đầu xem màn hình / Webcam
    STOP_STREAM = "stop_stream"         # Dừng xem màn hình / Webcam
    EXECUTE_COMMAND = "execute_command" # Chạy lệnh Shell / Terminal trên máy Client
    KILL_PROCESS = "kill_process"       # Tắt một ứng dụng đang chạy trên Client


class AuditLogBase(BaseModel):
    """
    [PATTERN - BASE SCHEMA]
    Chứa các thuộc tính cơ bản nhất của một dòng Nhật ký (Audit Log).
    """
    action: AuditAction = Field(
        ..., 
        description="Loại hành động được thực hiện (lấy từ AuditAction Enum).",
        example=AuditAction.LOCK_MACHINE
    )
    target_machine_id: Optional[str] = Field(
        None, 
        description="ID của máy Client chịu tác động (Có thể None nếu là hành động Login/Logout).",
        example="client-app-01"
    )
    details: Optional[str] = Field(
        None, 
        description="Mô tả chi tiết bổ sung (VD: 'Khóa máy do phát hiện vi phạm').",
        example="Khóa màn hình máy client-app-01 thành công."
    )


class AuditLogCreate(AuditLogBase):
    """
    [PATTERN - CREATE SCHEMA]
    Sử dụng khi EVENT HÀNH ĐỘNG DIỄN RA: Backend gọi Schema này để đóng gói dữ liệu
    và chuẩn bị ghi một dòng nhật ký mới vào Cơ sở dữ liệu.
    """
    admin_username: str = Field(
        ..., 
        description="Tên tài khoản Admin thực hiện hành động này.",
        example="admin_nguyen"
    )
    ip_address: Optional[str] = Field(
        None, 
        description="Địa chỉ IP của Admin tại thời điểm thực hiện thao tác.",
        example="192.168.1.50"
    )


class AuditLogResponse(AuditLogBase):
    """
    [PATTERN - RESPONSE SCHEMA]
    Sử dụng khi EVENT XEM LỊCH SỬ DIỄN RA: Trả dữ liệu từ CSDL ra màn hình 
    Audit Log trên Frontend ReactJS.

    LƯU Ý: Các trường phải khớp 1-1 với cột trong ORM Model AuditLog
    (db/models.py) để ConfigDict(from_attributes=True) đọc được:
    - operator_username (cột) <-> admin_username (cũ - KHÔNG tồn tại trong model)
    - timestamp (cột)      <-> created_at (cũ - KHÔNG tồn tại trong model)
    - action được lưu dưới dạng message type chuẩn theo api_contract.md
      (VD: "application.list", "power.lock") nên khai báo là str thay vì enum.
    """
    id: int = Field(
        ..., 
        description="ID tự tăng (Primary Key) của dòng nhật ký trong CSDL."
    )
    operator_username: str = Field(
        ..., 
        description="Tên Admin đã thực hiện thao tác."
    )
    action: str = Field(
        ...,
        description="Loại hành động (message type chuẩn theo api_contract.md)."
    )
    status: str = Field(
        ...,
        description="Kết quả thực hiện lệnh: success / failed / pending."
    )
    timestamp: datetime = Field(
        ..., 
        description="Thời điểm chính xác nhật ký được ghi nhận."
    )

    # SQLite KHÔNG lưu múi giờ (timezone) -> khi đọc từ DB, datetime bị trả về dạng
    # NAIVE (không có tzinfo), dù lúc GHI code dùng datetime.now(timezone.utc).
    # Nếu không gắn lại tzinfo, JSON trả về sẽ không có hậu tố 'Z'/+00:00, khiến
    # JS 'new Date(...)' hiểu nhầm là giờ local (Ví dụ: giờ UTC 14:51 sẽ hiện 14:51
    # thay vì 21:51 giờ Việt Nam). Validator này đảm bảo luôn đánh dấu là UTC.
    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    # Đọc trực tiếp từ SQLAlchemy ORM Model
    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """
    [PATTERN - LIST RESPONSE SCHEMA]
    Sử dụng để bọc danh sách nhật ký, hỗ trợ phân trang (Pagination) trên giao diện.
    """
    total: int = Field(
        ..., 
        ge=0, 
        description="Tổng số lượng dòng nhật ký tìm thấy."
    )
    logs: List[AuditLogResponse] = Field(
        ..., 
        description="Danh sách các bản ghi nhật ký chi tiết."
    )