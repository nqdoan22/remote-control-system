# web-app/backend/core/config.py
import os
from typing import List

class Settings:
    """
    Lớp quản lý tất cả các thông số cấu hình của Backend FastAPI.
    Được thiết kế để đọc từ biến môi trường (Environment Variables)
    hoặc sử dụng các giá trị mặc định an toàn.
    """
    # ------------------------------------------------------------------
    # 1. CẤU HÌNH BẢO MẬT JWT (JSON Web Token cho Admin)
    # ------------------------------------------------------------------
    # SECRET_KEY dùng để ký JWT Token. Trong thực tế production, key này phải đủ dài và bí mật.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b64a2f8c0d9e1a3f5b7c8d9e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b")
    ALGORITHM: str = "HS256" # Thuật toán mã hóa JWT chuẩn
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # Token có hiệu lực trong 24 giờ

    # ------------------------------------------------------------------
    # 2. CẤU HÌNH CƠ SỞ DỮ LIỆU (SQLite)
    # ------------------------------------------------------------------
    # File cơ sở dữ liệu sql_app.db sẽ được tự động tạo tại thư mục root của backend
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    # ------------------------------------------------------------------
    # 3. CẤU HÌNH KẾT NỐI SANG GATEWAY WEBSOCKET
    # ------------------------------------------------------------------
    # FastAPI Backend đóng vai trò là Web App client kết nối tới Gateway
    GATEWAY_WS_URL: str = os.getenv("GATEWAY_WS_URL", "ws://localhost:8765")
    
    # Machine Secret Key dùng để xác thực quyền gửi lệnh giữa các thành phần
    # Khớp hoàn toàn với AGENT_SECRET_KEY trong Gateway
    AGENT_SECRET_KEY: str = os.getenv("AGENT_SECRET_KEY", "d8e8fca2dc0f896fd7cb4cb0031ba249")

    # ------------------------------------------------------------------
    # 4. CẤU HÌNH PHÂN QUYỀN TRUY CẬP (CORS)
    # ------------------------------------------------------------------
    # Cho phép Frontend React (mặc định chạy port 5173 / 3000) gọi API sang Backend
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

# Khởi tạo một đối tượng Settings duy nhất dùng trong toàn bộ app
settings = Settings()