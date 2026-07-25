# web-app/backend/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers import auth, machines, modules

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Remote Control System - Backend API",
    description="Backend điều khiển 8 module qua Gateway WebSocket",
    version="1.0.0"
)

# Cấu hình CORS để Frontend ReactJS có thể gọi API mà không bị lỗi block trình duyệt
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"], # Cho phép GET, POST, PUT, DELETE...
    allow_headers=["*"], # Cho phép truyền mọi Header (bao gồm cả Authorization)
)

# Đăng ký các Routers
app.include_router(auth.router)
app.include_router(machines.router)
app.include_router(modules.router)

@app.get("/", tags=["Health Check"])
def root():
    """
    Endpoint kiểm tra trạng thái hoạt động của Backend Server.
    """
    return {
        "status": "online",
        "service": "FastAPI Backend",
        "message": "Hệ thống Backend đang hoạt động ổn định"
    }

if __name__ == "__main__":
    # Lệnh chạy server khi gọi trực tiếp file main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)