# web-app/backend/core/security.py
import bcrypt
import jwt
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Any
from core.config import settings

logger = logging.getLogger("Security")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu người dùng nhập vào (plain-text) 
    có khớp với chuỗi hash trong CSDL hay không bằng bcrypt.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Lỗi kiểm tra mật khẩu: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Băm mật khẩu người dùng bằng bcrypt trước khi lưu vào CSDL.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo mã JWT (JSON Web Token) cấp cho Admin sau khi đăng nhập thành công.
    Token này sẽ chứa username và thời gian hết hạn (expiration time).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(subject),  # Thường là username
        "exp": expire,        # Thời điểm hết hạn
        "iat": datetime.now(timezone.utc) # Thời điểm khởi tạo
    }
    
    # Ký JWT bằng SECRET_KEY và thuật toán mã hóa HS256 từ config
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt