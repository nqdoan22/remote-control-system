"""
===============================================================================
FILE: web-app/backend/schemas/machine.py
PURPOSE: Định nghĩa các Pydantic Schemas phục vụ kiểm tra (Validation), nén/giải
         mã dữ liệu (Serialization/Deserialization) cho đối tượng Machine.
ARCHITECTURE ROLE: 
  - Đóng vai trò lớp Chuyển đổi & Kiểm soát Dữ liệu (Data Contract Layer) giữa
    REST API Backend (FastAPI), Cơ sở dữ liệu (SQLite via SQLAlchemy), 
    Gateway WebSocket và Frontend (ReactJS).
===============================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class MachineStatus(str, Enum):
    """
    Enum quy định các trạng thái kết nối có thể có của một máy Client (Agent).
    
    Attributes:
        ONLINE (str): Agent đang kết nối và duy trì Heartbeat tới Gateway.
        OFFLINE (str): Agent ngắt kết nối hoặc rớt Heartbeat quá 15 giây.
        BUSY (str): Agent đang thực hiện các tác vụ độc quyền (Streaming, File Syncing).
    """
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class MachineBase(BaseModel):
    """
    Schema cơ sở (Base Schema) chứa các thuộc tính cốt lõi bắt buộc phải có 
    để định danh một máy Client trong hệ thống.
    """
    machine_id: str = Field(
        ..., 
        min_length=3,
        max_length=64,
        description="ID định danh duy nhất của máy Client (VD: client-app-01).",
        example="client-app-01"
    )
    hostname: str = Field(
        ..., 
        min_length=1,
        max_length=128,
        description="Tên máy tính (Hostname) khai báo trong hệ điều hành Windows.",
        example="DESKTOP-ADMIN-01"
    )
    ip_address: str = Field(
        ..., 
        description="Địa chỉ IP IPv4 của máy Client trong mạng LAN.",
        example="192.168.1.100"
    )

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, value: str) -> str:
        """
        Hàm kiểm tra (Validator) cấu trúc định dạng địa chỉ IPv4 hợp lệ.
        
        Args:
            value (str): Chuỗi địa chỉ IP truyền từ Client/Gateway.
            
        Returns:
            str: Chuỗi IP hợp lệ nếu vượt qua kiểm tra.
            
        Raises:
            ValueError: Nếu địa chỉ IP không tuân theo quy chuẩn IPv4 (0.0.0.0 -> 255.255.255.255).
        """
        ip_regex = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d)$"
        if not re.match(ip_regex, value):
            raise ValueError(f"Địa chỉ IP '{value}' không đúng định dạng IPv4 hợp lệ.")
        return value


class MachineCreate(MachineBase):
    """
    Schema sử dụng khi khởi tạo/đăng ký một máy Client mới vào Cơ sở dữ liệu SQLite.
    Kế thừa toàn bộ thuộc tính từ MachineBase.
    """
    secret_hash: Optional[str] = Field(
        None, 
        description="Chuỗi mã hóa Secret Key của Client dùng để xác thực kết nối ban đầu với Gateway."
    )


class MachineUpdate(BaseModel):
    """
    Schema sử dụng cho tác vụ Cập nhật (PATCH / PUT) thông tin máy tính.
    Thường được gọi khi Gateway gửi thông điệp Heartbeat cập nhật trạng thái thời gian thực.
    Tất cả các trường đều là Optional để hỗ trợ cập nhật từng phần (Partial Update).
    """
    hostname: Optional[str] = Field(
        None, 
        description="Cập nhật tên máy nếu người dùng đổi tên Hostname."
    )
    ip_address: Optional[str] = Field(
        None, 
        description="Cập nhật địa chỉ IP nếu máy Client thay đổi IP LAN."
    )
    status: Optional[MachineStatus] = Field(
        None, 
        description="Cập nhật trạng thái kết nối mới (online/offline/busy)."
    )
    last_seen: Optional[datetime] = Field(
        None, 
        description="Thời điểm nhận tín hiệu Heartbeat gần nhất từ máy Client."
    )
    cpu_usage: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0, 
        description="Mức độ tiêu thụ CPU hiện tại (%) từ 0.0 đến 100.0."
    )
    ram_usage: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0, 
        description="Mức độ tiêu thụ RAM hiện tại (%) từ 0.0 đến 100.0."
    )

    @field_validator("ip_address")
    @classmethod
    def validate_optional_ip(cls, value: Optional[str]) -> Optional[str]:
        """Validator kiểm tra định dạng IP nếu thuộc tính ip_address được truyền vào."""
        if value is None:
            return value
        ip_regex = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d)$"
        if not re.match(ip_regex, value):
            raise ValueError(f"Địa chỉ IP cập nhật '{value}' không tuân theo định dạng IPv4.")
        return value


class MachineResponse(MachineBase):
    """
    Schema chuẩn hóa dữ liệu trả về cho Client/Frontend (ReactJS API Response).
    Bao gồm thông tin cơ bản của máy, trạng thái kết nối và các thông số tài nguyên thời gian thực.
    """
    status: MachineStatus = Field(
        MachineStatus.OFFLINE, 
        description="Trạng thái kết nối hiện tại của máy."
    )
    last_seen: Optional[datetime] = Field(
        None, 
        description="Thời điểm cuối cùng máy gửi Heartbeat về hệ thống."
    )
    cpu_usage: float = Field(
        0.0, 
        description="Tỉ lệ phần trăm CPU đang sử dụng."
    )
    ram_usage: float = Field(
        0.0, 
        description="Tỉ lệ phần trăm RAM đang sử dụng."
    )
    created_at: datetime = Field(
        ..., 
        description="Thời điểm máy được ghi nhận lần đầu vào CSDL."
    )

    # Cấu hình Pydantic v2 tương thích trực tiếp với SQLAlchemy ORM Models
    model_config = ConfigDict(from_attributes=True)


class MachineListResponse(BaseModel):
    """
    Schema bọc (Wrapper Schema) cho phản hồi danh sách nhiều máy tính.
    Giúp Frontend dễ dàng phân trang và hiển thị tổng số lượng máy trên Dashboard.
    """
    total: int = Field(
        ..., 
        ge=0, 
        description="Tổng số lượng máy tính có trong hệ thống."
    )
    machines: List[MachineResponse] = Field(
        ..., 
        description="Danh sách chi tiết các máy tính kèm thông số trạng thái."
    )