from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# --- Các mã lỗi tiêu chuẩn (JSON-RPC 2.0 Error Codes) ---
class RPCErrorCode:
    PARSE_ERROR = -32700        # Frame không đúng định dạng JSON
    INVALID_REQUEST = -32600    # Frame JSON không hợp lệ theo chuẩn RPC
    METHOD_NOT_FOUND = -32601   # Không tìm thấy handler cho method
    INVALID_PARAMS = -32602     # Tham số truyền vào không hợp lệ
    INTERNAL_ERROR = -32603     # Lỗi xử lý bên trong server
    UNAUTHORIZED = -32001       # Lỗi xác thực / phân quyền (Custom)


# --- Cấu trúc chi tiết của lỗi ---
class RPCError(BaseModel):
    code: int = Field(..., description="Mã lỗi RPC")
    message: str = Field(..., description="Mô tả lỗi ngắn gọn")
    data: Optional[Any] = Field(None, description="Dữ liệu bổ sung hoặc thông tin debug")


# --- Cấu trúc cơ sở (Base Frame) ---
class RPCBase(BaseModel):
    jsonrpc: str = Field("2.0", description="Phiên bản giao thức RPC (mặc định 2.0)")


# 1. Frame Yêu cầu từ Client (RPC Request)
class RPCRequest(RPCBase):
    id: Union[int, str] = Field(
        ..., description="ID định danh duy nhất cho mỗi yêu cầu để khớp với response"
    )
    method: str = Field(..., description="Tên hàm/method cần gọi trên server")
    params: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default_factory=dict, description="Tham số truyền vào hàm"
    )


# 2. Frame Thông báo / Sự kiện 1 chiều (Notification / Event)
# Không có field `id` vì không cần phản hồi lại
class RPCNotification(RPCBase):
    method: str = Field(..., description="Tên sự kiện hoặc thông báo")
    params: Optional[Union[Dict[str, Any], List[Any]]] = Field(
        default_factory=dict, description="Dữ liệu đi kèm sự kiện"
    )


# 3. Frame Phản hồi Thành công từ Server (Success Response)
class RPCSuccessResponse(RPCBase):
    id: Union[int, str] = Field(..., description="ID tương ứng với RPCRequest")
    result: Any = Field(..., description="Kết quả trả về sau khi xử lý")


# 4. Frame Phản hồi Lỗi từ Server (Error Response)
class RPCErrorResponse(RPCBase):
    id: Optional[Union[int, str]] = Field(
        None, description="ID tương ứng với RPCRequest (nếu lấy được ID từ request lỗi)"
    )
    error: RPCError = Field(..., description="Chi tiết lỗi")


# --- Union Type hỗ trợ parse linh hoạt các loại Frame ---
RPCMessage = Union[RPCRequest, RPCNotification, RPCSuccessResponse, RPCErrorResponse]