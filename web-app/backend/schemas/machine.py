# web-app/backend/schemas/machine.py
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

# ==========================================
# SCHEMAS CHO QUẢN LÝ MÁY CLIENT (MACHINES)
# ==========================================

class MachineBase(BaseModel):
    """
    Thông tin cơ bản định danh một máy Client.
    """
    machine_id: str = Field(..., description="Mã định danh duy nhất của máy Client (UUID)")
    hostname: str = Field(..., description="Tên máy tính (VD: DESKTOP-ABC)")
    ip_address: str = Field(..., description="Địa chỉ IP LAN của máy Client")

class MachineCreate(MachineBase):
    """
    Schema dùng khi một máy Client kết nối lần đầu tiên tới hệ thống.
    """
    pass

class MachineUpdate(BaseModel):
    """
    Schema dùng để cập nhật trạng thái Heartbeat của máy.
    Chỉ cập nhật status và last_seen.
    """
    status: Optional[str] = Field(None, description="Trạng thái: online, offline")
    last_seen: Optional[datetime] = Field(None, description="Thời điểm cuối cùng nhận được ping")

class MachineResponse(MachineBase):
    """
    Schema trả về cho Frontend React để render danh sách máy.
    """
    status: str
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)