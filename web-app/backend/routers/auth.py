"""
===============================================================================
FILE: web-app/backend/routers/auth.py
PURPOSE: API Router quản lý Xác thực người dùng (Authentication & Authorization).
ARCHITECTURE ROLE: 
  - Đóng vai trò là cổng tiếp nhận request Đăng nhập từ Frontend.
  - Phụ trách đối soát tài khoản với Database và cấp phát JWT Access Token.
===============================================================================
"""

import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import các công cụ kết nối DB và Model
from db.database import get_db
from db.models import User

# Import Schemas kiểm định dữ liệu đầu vào / đầu ra
from schemas.auth import Token, UserResponse, LoginRequest

# Import các hàm mã hóa & bảo mật đã viết ở core/security.py
from core.security import (
    verify_password, 
    create_access_token, 
    get_current_user
)
from core.config import settings

# Khởi tạo Logger và Router
logger = logging.getLogger("AuthRouter")
router = APIRouter(prefix="/auth", tags=["Authentication"])


# =========================================================================
# 🌟 API 1: XỬ LÝ ĐĂNG NHẬP (POST /api/v1/auth/login)
# =========================================================================
@router.post("/login", response_model=Token, summary="Đăng nhập hệ thống Admin")
def login(
    credentials: LoginRequest, 
    db: Session = Depends(get_db)
):
    """
    API xử lý Đăng nhập cho Admin:
    1. Nhận JSON {username, password} từ Frontend (login.jsx).
    2. Tìm kiếm username trong bảng 'users'.
    3. So sánh password nhập vào với hashed_password trong CSDL.
    4. Trả về JWT Access Token nếu hợp lệ, ngược lại trả về lỗi 401.
    """
    # 1. Tìm tài khoản trong Database
    user = db.query(User).filter(User.username == credentials.username).first()

    # 2. Kiểm tra xem tài khoản có tồn tại và mật khẩu có đúng không
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"⚠️ Đăng nhập thất bại cho username: '{credentials.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Kiểm tra tài khoản có bị khóa (is_active = False) không
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản này đã bị vô hiệu hóa!"
        )

    # 4. Tính toán thời gian hết hạn của Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 5. Tạo JWT Access Token chứa thông tin username và role
    access_token = create_access_token(
        subject=user.username,
        role=user.role,
        expires_delta=access_token_expires
    )

    logger.info(f"✅ User '{user.username}' đăng nhập thành công. Đã cấp Token!")

    # 6. Trả Token về cho Frontend
    return Token(
        access_token=access_token,
        token_type="bearer"
    )


# =========================================================================
# 🌟 API 2: LẤY THÔNG TIN ADMIN HIỆN TẠI (GET /api/v1/auth/me)
# =========================================================================
@router.get("/me", response_model=UserResponse, summary="Lấy thông tin Admin đang đăng nhập")
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    """
    API xác thực chiếc 'Thẻ ra vào' (JWT Token):
    Frontend gửi Token ở Header -> Backend giải mã -> Trả về thông tin Admin.
    Dùng khi Frontend (dashboard.jsx) cần tải lại thông tin Profile Admin.
    """
    return current_user