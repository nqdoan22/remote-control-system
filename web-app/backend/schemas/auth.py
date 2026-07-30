"""
===============================================================================
FILE: web-app/backend/schemas/auth.py
PURPOSE: Định nghĩa các Pydantic Schemas phục vụ cho quá trình Xác thực 
         (Authentication) và Phân quyền (Authorization) của Admin.
ARCHITECTURE ROLE: 
  - Đóng vai trò Data Contract cho luồng Đăng nhập (Login), Cấp phát & Xác thực
    tấm vé JWT Token giữa Frontend (ReactJS) và Backend (FastAPI).
===============================================================================
"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Schema tiếp nhận dữ liệu từ Form đăng nhập mà Admin điền trên giao diện Web.
    """
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50, 
        description="Tên tài khoản đăng nhập của Admin.",
        example="admin"
    )
    password: str = Field(
        ..., 
        min_length=6, 
        description="Mật khẩu tài khoản (dạng văn bản thuần trước khi verify).",
        example="AdminPass123!"
    )


class Token(BaseModel):
    """
    Schema cấu trúc "Tấm vé" (JWT Token) trả về cho Frontend sau khi Admin 
    đăng nhập thành công.
    """
    access_token: str = Field(
        ..., 
        description="Chuỗi mã hóa JWT Access Token dùng cho các request API tiếp theo."
    )
    token_type: str = Field(
        "bearer", 
        description="Loại Token chuẩn OAuth2 (mặc định là 'bearer')."
    )


class TokenPayload(BaseModel):
    """
    Schema giải mã dữ liệu ẩn bên trong chuỗi JWT Token.
    Được Backend dùng để nhận biết: "Yêu cầu này là của Admin nào gửi tới?".
    """
    sub: Optional[str] = Field(
        None, 
        description="Subject (Thường là Username hoặc User ID của Admin)."
    )
    role: Optional[str] = Field(
        "admin", 
        description="Quyền hạn của tài khoản (VD: admin, operator)."
    )


class PasswordChangeRequest(BaseModel):
    """
    Schema dùng khi Admin thực hiện thao tác Đổi mật khẩu trên Dashboard.
    """
    old_password: str = Field(
        ..., 
        description="Mật khẩu cũ hiện tại để đối soát."
    )
    new_password: str = Field(
        ..., 
        min_length=6, 
        description="Mật khẩu mới muốn thay đổi."
    )