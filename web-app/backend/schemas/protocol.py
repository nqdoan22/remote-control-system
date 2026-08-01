# web-app/backend/schemas/protocol.py
"""
File định nghĩa Schema chuẩn hóa cho giao thức WebSocket Envelope.
Khớp 100% với tài liệu API Contract & Communication Protocol.
"""

import time
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class WSMessage(BaseModel):
    """
    Vỏ bọc tin nhắn chuẩn (Message Envelope) cho tất cả giao tiếp WebSocket.
    """
    messageId: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Mã định danh duy nhất của message để map Request với Response"
    )
    type: str = Field(
        ..., 
        description="Loại thao tác/lệnh (VD: process.list, screen.live.start, response, error)"
    )
    timestamp: int = Field(
        default_factory=lambda: int(time.time()),
        description="Thời điểm gửi (Unix Epoch Time)"
    )
    source: str = Field(
        ..., 
        description="ID thành phần gửi (VD: webapp, gateway, client-app-01)"
    )
    destination: str = Field(
        ..., 
        description="ID thành phần nhận (VD: gateway, client-app-01, webapp)"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Dữ liệu chi tiết chứa tham số lệnh hoặc kết quả trả về"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "messageId": "550e8400-e29b-41d4-a716-446655440000",
                "type": "process.list",
                "timestamp": 1710000000,
                "source": "webapp",
                "destination": "client-app-01",
                "payload": {}
            }
        }


class WSErrorPayload(BaseModel):
    """
    Payload chuẩn khi phản hồi lỗi (type = 'error').
    """
    code: str = Field(..., description="Mã lỗi chuẩn (VD: USER_REJECTED, CONSENT_TIMEOUT)")
    message: str = Field(..., description="Mô tả chi tiết nguyên nhân lỗi")
    originalMessageId: Optional[str] = Field(
        default=None, 
        description="ID của request gốc gây ra lỗi"
    )


class WSPermissionRequestPayload(BaseModel):
    """
    Payload xin quyền End User cho các chức năng nhạy cảm (type = 'permission.request').
    """
    permissionId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feature: str = Field(..., description="Tên chức năng (VD: screen.live, webcam, keylogger)")
    requestedBy: str = Field(..., description="Admin gửi yêu cầu")
    originalMessageId: str = Field(..., description="ID lệnh gốc từ Admin")


class WSPermissionResponsePayload(BaseModel):
    """
    Payload phản hồi kết quả xin quyền từ Client (type = 'permission.response').
    """
    permissionId: str
    granted: bool = Field(..., description="True nếu User bấm Accept, False nếu Reject/Timeout")