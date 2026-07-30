"""
===============================================================================
FILE: web-app/backend/db/models.py
PURPOSE: Định nghĩa cấu trúc các Bảng (Tables/Models) trong CSDL bằng SQLAlchemy.
ARCHITECTURE ROLE: 
  - Khởi tạo 3 bảng chính: User (Tài khoản), Machine (Máy Agent), AuditLog (Nhật ký).
  - Ánh xạ các thuộc tính Python thành các cột tương ứng trong CSDL SQLite.
===============================================================================
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from db.database import Base


class User(Base):
    """
    BẢNG 1: QUẢN LÝ TÀI KHOẢN ADMIN (users)
    Lưu trữ thông tin tài khoản đăng nhập hệ thống Web Admin.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False) # Tên đăng nhập (VD: admin)
    hashed_password = Column(String(255), nullable=False)                 # Mật khẩu đã băm Bcrypt
    role = Column(String(20), default="admin", nullable=False)            # Quyền hạn: admin / operator
    is_active = Column(Boolean, default=True)                              # Trạng thái tài khoản (Active/Disabled)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Machine(Base):
    """
    BẢNG 2: SỔ GHI CHÚ MÁY AGENT (machines)
    Lưu trữ danh sách, thông tin cấu hình và trạng thái của các máy Client/Agent.
    """
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(String(100), unique=True, index=True, nullable=False) # Mã định danh duy nhất của Agent
    hostname = Column(String(100), nullable=True)                              # Tên máy (VD: DESKTOP-LAB01)
    ip_address = Column(String(45), nullable=True)                             # Địa chỉ IP của máy Agent
    os_info = Column(String(100), nullable=True)                              # Hệ điều hành (VD: Windows 11 Pro)
    status = Column(String(20), default="offline")                             # Trạng thái: online / offline
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))   # Lần cuối cùng điểm danh
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    """
    BẢNG 3: NHẬT KÝ THAO TÁC HỆ THỐNG (audit_logs)
    Ghi lại mọi lệnh điều khiển do Admin ra lệnh xuống các máy Agent.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    operator_username = Column(String(50), nullable=False) # Ai đã làm? (Username của Admin)
    action = Column(String(100), nullable=False)            # Làm gì? (VD: machine.lock, file.upload, webcam.stream)
    target_machine_id = Column(String(100), nullable=True) # Làm trên máy nào? (machine_id)
    status = Column(String(20), nullable=False)            # Kết quả? (success / failed / pending)
    details = Column(Text, nullable=True)                  # Chi tiết phản hồi hoặc lý do lỗi
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True) # Thời gian thực hiện