# web-app/backend/schemas/auth.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

# ==========================================
# SCHEMAS CHO XÁC THỰC (AUTHENTICATION)
# ==========================================

class Token(BaseModel):
    """
    Schema trả về khi Admin đăng nhập thành công.
    Chứa JWT Token để client (React/Gateway) sử dụng cho các request sau.
    """
    access_token: str
    token_type: str # Thường là "bearer"

class TokenData(BaseModel):
    """
    Schema dùng để giải mã và lưu trữ payload của JWT Token.
    """
    username: Optional[str] = None

class UserBase(BaseModel):
    """
    Thuộc tính cơ bản của một User (Admin).
    """
    username: str

class UserCreate(BaseModel):
    """
    Schema dùng khi tạo mới một Admin.
    Cần có password dạng plain-text (sẽ được hash trước khi lưu vào DB).
    """
    username: str
    password: str

class UserResponse(UserBase):
    """
    Schema trả về thông tin User cho Frontend (Tuyệt đối KHÔNG trả về password).
    """
    id: int
    role: str = "Admin" # Mặc định hệ thống chỉ có 1 role Admin

    # ConfigDict(from_attributes=True) thay thế cho orm_mode = True trong Pydantic V2
    # Giúp Pydantic có thể đọc dữ liệu trực tiếp từ SQLAlchemy ORM Model
    model_config = ConfigDict(from_attributes=True)