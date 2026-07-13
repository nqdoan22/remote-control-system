# web-app/backend/routers/auth.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# 🚪 Thay vì dùng app = FastAPI(), ở phòng riêng ta dùng APIRouter
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Khuôn mẫu dữ liệu đầu vào (Đầu bếp quy định thực đơn)
class LoginRequest(BaseModel):
    username: str
    password: str

# Ô cửa nhận đơn Đăng nhập (Lúc này đường dẫn chỉ cần là "/" vì đã có prefix "/api/auth" ở trên)
@router.post("/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "admin123":
        return {
            "status": "success",
            "token": "real-jwt-token-from-backend-123456",
            "user": {
                "username": data.username,
                "role": "root_admin"
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác!"
        )