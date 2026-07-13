# web-app/backend/core/security.py
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# 🔑 CẤU HÌNH BẢO MẬT (Thực tế nên đọc từ core/config.py)
SECRET_KEY = "S1uP3r_S3cr3t_K3y_F0r_N3tw0rk_Pr0j3ct" # Chuỗi bí mật để ký mã hóa token
ALGORITHM = "HS256"                                # Thuật toán mã hóa băm
ACCESS_TOKEN_EXPIRE_MINUTES = 60                   # Token có hiệu lực trong 60 phút

# Công cụ mã hóa/kiểm tra mật khẩu (Sử dụng thuật toán bcrypt chống crack)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Định nghĩa ô cửa lấy Token từ Header của HTTP Request gửi lên (Dạng: Bearer <Token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Khuôn mẫu chứa dữ liệu bên trong Token sau khi giải mã
class TokenData(BaseModel):
    username: str | None = None

# =====================================================================
# 🛠️ CÁC HÀM XỬ LÝ MẬT KHẨU & TOKEN
# =====================================================================

def hash_password(password: str) -> str:
    """Mã hóa một mật khẩu thô thành chuỗi băm bảo mật trước khi lưu."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu người dùng nhập vào có khớp với mật khẩu đã băm không."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Tạo ra một chiếc vé thông hành JWT Token thời hạn 60 phút khi đăng nhập đúng."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Ký tên xác thực và tạo chuỗi Token dạng mã hóa
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# =====================================================================
# 🔐 HÀM BẢO VỆ ENDPOINT (DEPENDENCY) - Ổ KHÓA CHÍNH
# =====================================================================
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Hàm gác cổng. Bất kỳ router nào muốn bảo mật chỉ cần gọi hàm này làm tham số.
    Nó sẽ tự bốc Token từ Frontend gửi lên, kiểm tra tính hợp lệ và thời hạn.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Vé thông hành (Token) không hợp lệ hoặc đã hết hạn! Vui lòng đăng nhập lại.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Giải mã Token bằng SECRET_KEY của hệ thống
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
        
    return token_data