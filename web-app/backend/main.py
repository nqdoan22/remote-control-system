# web-app/backend/main.py
import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.gateway_client import gateway_client
from routers import auth, machines, modules

# Cấu hình log ra file admin.log
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [BACKEND] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "admin.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: kết nối tới Gateway
    try:
        await gateway_client.connect()
        logging.getLogger("Main").info("Đã kết nối Gateway từ lifespan")
    except Exception as e:
        logging.getLogger("Main").warning(f"Gateway chưa sẵn sàng khi khởi động: {e}")
    yield
    # Shutdown: ngắt kết nối Gateway
    await gateway_client.disconnect()

app = FastAPI(
    title="Remote Control System - Backend API",
    description="Backend điều khiển 8 module qua Gateway WebSocket",
    version="1.0.0",
    lifespan=lifespan
)

# Cấu hình CORS để Frontend ReactJS có thể gọi API mà không bị lỗi block trình duyệt
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các Routers
app.include_router(auth.router)
app.include_router(machines.router)
app.include_router(modules.router)

@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "service": "FastAPI Backend",
        "message": "Hệ thống Backend đang hoạt động ổn định"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)