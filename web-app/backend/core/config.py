"""
===============================================================================
FILE: web-app/backend/core/config.py
PURPOSE: Quản lý cấu hình tập trung (Centralized Configuration Settings) cho 
         toàn bộ Backend FastAPI.
ARCHITECTURE ROLE: 
  - Tải và nạp các biến môi trường (Environment Variables) từ file .env hoặc
    sử dụng các giá trị mặc định chuẩn (Default Fallbacks).
  - Cung cấp các hằng số hạ tầng (IP Gateway, JWT Key, DB URL, CORS) cho các 
    thành phần khác như security.py, gateway_client.py, database.py và routers.
===============================================================================
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Class quản lý toàn bộ thiết lập cấu hình của dự án Web App Backend.
    Pydantic sẽ tự động đọc biến môi trường từ file .env nếu có.
    """

    # -------------------------------------------------------------------------
    # 1. THÔNG TIN CHUNG HỆ THỐNG (SYSTEM INFO)
    # -------------------------------------------------------------------------
    PROJECT_NAME: str = "Remote Control System Backend"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # -------------------------------------------------------------------------
    # 2. CẤU HÌNH BẢO MẬT & XÁC THỰC (JWT AUTHENTICATION)
    # Ref: schemas/auth.py
    # -------------------------------------------------------------------------
    # Khoá bí mật mã hóa JWT (NÊN THAY ĐỔI TRONG MÔI TRƯỜNG PRODUCTION)
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    # Thời hạn hiệu lực của JWT Token (Mặc định: 1440 phút = 24 giờ)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Tài khoản Admin mặc định khi khởi tạo Database lần đầu
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "AdminPass123!"

    # -------------------------------------------------------------------------
    # 3. CẤU HÌNH CƠ SỞ DỮ LIỆU (DATABASE CONFIG)
    # Ref: SQLite / SQLAlchemy
    # -------------------------------------------------------------------------
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # -------------------------------------------------------------------------
    # 4. CẤU HÌNH KẾT NỐI GATEWAY (GATEWAY WEBSOCKET CONFIG)
    # Ref: schemas/protocol.py (WSMessage)
    # -------------------------------------------------------------------------
    # Địa chỉ WebSocket của Gateway Server mà Backend sẽ kết nối tới
    # (phải kèm path '/webapp' — khớp route trong gateway/main.py, nếu không Gateway
    # sẽ đóng kết nối với close code 4004 "Unknown path")
    GATEWAY_WS_URL: str = "ws://localhost:8765/webapp"
    
    # Định danh duy nhất đại diện cho Web App Backend khi đóng gói WSMessage (source = "webapp")
    BACKEND_SOURCE_ID: str = "webapp"
    
    # Thời gian chờ (Timeout) phản hồi lệnh từ Gateway/Client Agent (giây)
    COMMAND_TIMEOUT_SECONDS: int = 15

    # Timeout riêng cho các lệnh thuộc Sensitive Feature List (screen.live.start,
    # webcam.start, keylogger.start, power.*). Theo api_contract.md, Gateway có thể
    # chờ Permission Confirmation từ End User tối đa PERMISSION_TIMEOUT = 30s trước
    # khi trả lời -> phải chờ lâu hơn con số đó để không timeout hụt phía Backend.
    SENSITIVE_COMMAND_TIMEOUT_SECONDS: int = 35

    # -------------------------------------------------------------------------
    # 5. CẤU HÌNH TÊN MIỀN CHO PHÉP TRUY CẬP (CORS ORIGINS)
    # Phục vụ kết nối REST API từ Frontend (ReactJS / Vite / NextJS)
    # -------------------------------------------------------------------------
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Cổng mặc định của Vite React
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # -------------------------------------------------------------------------
    # PYDANTIC CONFIGURATION
    # -------------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Khởi tạo một phiên bản singleton duy nhất để export sử dụng toàn ứng dụng
settings = Settings()