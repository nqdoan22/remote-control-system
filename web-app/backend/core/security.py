"""
===============================================================================
FILE: web-app/backend/core/security.py
PURPOSE: Cung cấp các công cụ xử lý Mã hóa Bảo mật (Security & Cryptography)
         cho hệ thống Web App Backend.
ARCHITECTURE ROLE: 
  - Đóng vai trò là "Công cụ bảo mật" tầng Core, xử lý 2 tác vụ quan trọng:
    1. Băm mật khẩu (Password Hashing) bằng thuật toán Bcrypt trước khi lưu 
       vào Cơ sở dữ liệu SQLite.
    2. Cấp phát, ký số (Sign) và Giải mã (Decode) JWT Access Token phục vụ 
       Xác thực & Phân quyền cho Admin.
===============================================================================
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import settings
from db.database import get_db
from db.models import User
from schemas.auth import TokenPayload

# Setup ngữ cảnh mã hóa mật khẩu sử dụng Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme: trích xuất Bearer Token từ Header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# =============================================================================
# 1. NHÓM HÀM XỬ LÝ MẬT KHẨU (PASSWORD HASHING)
# =============================================================================

def get_password_hash(password: str) -> str:
    """
    Băm mật khẩu văn bản thuần (Plaintext Password) thành chuỗi băm an toàn Bcrypt.
    
    Args:
        password (str): Mật khẩu chữ thường do Admin nhập.
        
    Returns:
        str: Chuỗi băm Bcrypt đã được Salt (để lưu vào DB).
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    So sánh mật khẩu văn bản thuần từ form Đăng nhập với chuỗi băm trong DB.
    
    Args:
        plain_password (str): Mật khẩu nhập từ Form đăng nhập.
        hashed_password (str): Mật khẩu đã băm lưu trong CSDL.
        
    Returns:
        bool: True nếu mật khẩu chính xác, False nếu sai.
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# 2. NHÓM HÀM XỬ LÝ JWT TOKEN (JSON WEB TOKEN)
# =============================================================================

def create_access_token(
    subject: Union[str, Any], 
    role: str = "admin", 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo và ký số một JWT Access Token ("Tấm vé VIP") trả về cho Frontend.
    
    Args:
        subject (Union[str, Any]): Định danh tài khoản (Username của Admin).
        role (str): Quyền hạn của tài khoản (Mặc định là 'admin').
        expires_delta (Optional[timedelta]): Thời gian hết hạn tùy chỉnh. 
                                            Nếu None sẽ dùng cấu hình trong config.py.
                                            
    Returns:
        str: Chuỗi JWT Access Token đã mã hóa mã HS256.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Payload chứa thông tin đính kèm bên trong Token
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role
    }
    
    # Mã hóa chuỗi JWT bằng SECRET_KEY và thuật toán ALGORITHM
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """
    Giải mã và xác thực tính hợp lệ của JWT Access Token gửi từ Frontend.
    
    Args:
        token (str): Chuỗi Bearer Token đính kèm trong Header request.
        
    Returns:
        Optional[TokenPayload]: Đối tượng TokenPayload (chứa username, role) 
                                if Token hợp lệ, ngược lại trả về None.
    """
    try:
        # Giải mã và kiểm tra Chữ ký (Signature) + Hạn sử dụng (Expiration)
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role", "admin")
        
        if username is None:
            return None
            
        return TokenPayload(sub=username, role=role)
        
    except JWTError:
        # Trả về None nếu Token bị sửa đổi, hết hạn hoặc sai định dạng
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency FastAPI dùng để bảo vệ các endpoint yêu cầu xác thực.
    Giải mã JWT Token, tìm User trong DB, trả về User hoặc báo lỗi 401.
    """
    token_data = decode_access_token(token)
    if token_data is None or token_data.sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == token_data.sub).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng từ Token!",
        )
    return user