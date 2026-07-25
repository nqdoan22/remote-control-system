# web-app/backend/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.database import Base

def get_utc_now():
    """Hàm phụ trợ lấy thời gian UTC hiện tại chuẩn định dạng."""
    return datetime.now(timezone.utc)

class User(Base):
    """
    Bảng 'users': Lưu thông tin tài khoản Admin đăng nhập hệ thống.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False) # Mật khẩu đã được băm Bcrypt
    role = Column(String(20), default="Admin", nullable=False)
    created_at = Column(DateTime, default=get_utc_now)

    # Quan hệ 1-N: Một Admin có thể thực hiện nhiều thao tác ghi log
    audit_logs = relationship("AuditLog", back_populates="admin")


class Machine(Base):
    """
    Bảng 'machines': Danh sách các máy tính Client (Agent) bị điều khiển.
    """
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    machine_id = Column(String(100), unique=True, index=True, nullable=False) # UUID định danh Agent
    hostname = Column(String(100), nullable=False)                          # Tên máy (VD: DESKTOP-LAB1)
    ip_address = Column(String(45), nullable=False)                           # IP LAN
    status = Column(String(20), default="offline", nullable=False)             # 'online' hoặc 'offline'
    last_seen = Column(DateTime, default=get_utc_now)                         # Thời điểm ping gần nhất
    created_at = Column(DateTime, default=get_utc_now)

    # Quan hệ 1-N: Một máy trạm có thể có nhiều lịch sử tác động
    audit_logs = relationship("AuditLog", back_populates="machine")


class AuditLog(Base):
    """
    Bảng 'audit_logs': Nhật ký thao tác hệ thống - CỰC KỲ QUAN TRỌNG CHO BẢO MẬT.
    Lưu vết ai đã điều khiển máy nào, chức năng gì, và kết quả ra sao.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    machine_id = Column(String(100), ForeignKey("machines.machine_id"), nullable=False)
    
    action = Column(String(100), nullable=False)  # VD: 'webcam.start', 'process.kill', 'keylogger.start'
    status = Column(String(50), nullable=False)   # VD: 'Success', 'User_Denied', 'Timeout', 'Failed'
    details = Column(Text, nullable=True)          # Lưu JSON string tham số (VD: {"pid": 4120})
    
    timestamp = Column(DateTime, default=get_utc_now, index=True)

    # Khai báo mối quan hệ để ORM SQLAlchemy có thể Join bảng dễ dàng
    admin = relationship("User", back_populates="audit_logs")
    machine = relationship("Machine", back_populates="audit_logs")