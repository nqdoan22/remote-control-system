import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt  # Sử dụng trực tiếp thay thế cho passlib
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# 1. Cấu hình bảo mật cơ bản
SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_FOR_LOCAL_LAN_123987")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 2  # Token có hiệu lực trong 2 tiếng

# Khai báo đường dẫn lấy token cho Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- Các hàm Utilities về Mật khẩu (Dùng trực tiếp thư viện bcrypt) ---
def hash_password(password: str) -> str:
    """Băm mật khẩu sử dụng bcrypt, tương thích hoàn toàn với Python mới."""
    # Đổi chuỗi mật khẩu (str) thành bytes
    password_bytes = password.encode('utf-8')
    # Tạo salt ngẫu nhiên
    salt = bcrypt.gensalt()
    # Băm mật khẩu và giải mã ngược lại thành dạng string để lưu trữ
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu thô và chuỗi hash có khớp nhau không."""
    try:
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False


# --- Các hàm Utilities về JWT Token (Giữ nguyên logic cũ) ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Tạo JWT Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Giải mã và kiểm tra tính hợp lệ của token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- Dependency Injection để bảo vệ các Router khác ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Inject kiểm tra quyền đăng nhập."""
    payload = verify_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thiếu thông tin định danh (sub)",
        )
    return {"username": username, "role": payload.get("role", "admin")}