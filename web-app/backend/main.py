"""
===============================================================================
FILE: web-app/backend/main.py
PURPOSE: File chạy chính (Entrypoint) của ứng dụng Web Backend (FastAPI).
ARCHITECTURE ROLE: 
  - Khởi tạo FastAPI application và cấu hình Middleware CORS.
  - Quản lý Vòng đời ứng dụng (Lifespan): Khởi tạo CSDL & kết nối Gateway.
  - Tập hợp tất cả các API Routers (auth, machines, modules, audit_log).
===============================================================================
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import cấu hình và CSDL
from core.config import settings
from init_db import init_db
from core.gateway_client import gateway_client

# Import các API Routers
from routers import auth, machines, modules, audit_log, ws

# Thiết lập ghi Log hệ thống
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
)
logger = logging.getLogger("MainApp")


# =========================================================================
# ⚙️ 1. QUẢN LÝ VÒNG ĐỜI ỨNG DỤNG (LIFESPAN MANAGEMENT)
# =========================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hàm quản lý việc Bật / Tắt ứng dụng:
    - code TRƯỚC yield: Tự động chạy khi Server Backend vừa bật lên.
    - code SAU yield: Tự động chạy khi Server Backend chuẩn bị tắt.
    """
    logger.info("🚀 [STARTUP] Đang khởi động Backend Service...")
    
    # Bước A: Khởi tạo CSDL & cấy tài khoản Admin mặc định
    try:
        init_db()
        logger.info("✅ [STARTUP] CSDL SQLite đã sẵn sàng!")
    except Exception as e:
        logger.error(f"❌ [STARTUP] Lỗi khởi tạo CSDL: {e}")

    # Bước B: Mở kết nối WebSocket Client sang Gateway Server
    try:
        await gateway_client.start()
        logger.info("✅ [STARTUP] Đã kết nối thành công sang Gateway Server!")
    except Exception as e:
        logger.warning(f"⚠️ [STARTUP] Chưa thể kết nối Gateway ngay lúc này: {e}")

    yield  # 🟢 Ứng dụng Backend chạy và nhận Request tại đây

    # Bước C: Ngắt kết nối dọn dẹp tài nguyên khi tắt Server
    logger.info("🛑 [SHUTDOWN] Đang đóng ứng dụng Backend...")
    await gateway_client.stop()
    logger.info("👋 [SHUTDOWN] Đã giải phóng hoàn toàn tài nguyên!")


# =========================================================================
# 🏗️ 2. KHỞI TẠO FASTAPI APP & CẤU HÌNH CORS
# =========================================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Hệ thống Quản lý và Điều khiển Máy trạm từ xa - Đồ án An toàn Thông tin",
    lifespan=lifespan
)

# Cấu hình CORS cho phép React Frontend kết nối tới
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế sản xuất có thể đổi thành URL của Frontend
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả HTTP Methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],
)


# =========================================================================
# 🔌 3. TẬP HỢP CÁC ROUTERS (INCLUDE API ENDPOINTS)
# =========================================================================
# Tất cả các API sẽ có tiền tố /api/v1 (Ví dụ: /api/v1/auth/login, /api/v1/machines/)
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(machines.router, prefix=API_PREFIX)
app.include_router(modules.router, prefix=API_PREFIX)
app.include_router(audit_log.router, prefix=API_PREFIX)

# WebSocket Endpoint (KHÔNG có prefix - bắt buộc đúng đường dẫn /ws)
app.include_router(ws.router)


# =========================================================================
# 🩺 4. HEALTH CHECK ENDPOINT (KIỂM TRA SỨC KHỎE SERVER)
# =========================================================================
@app.get("/", tags=["Health Check"])
def root_check():
    """
    API gốc kiểm tra xem Backend Server có đang sống hay không.
    """
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs"  # Đường dẫn tới trang Swagger UI tự động của FastAPI
    }


# =========================================================================
# ▶️ 5. ĐIỂM THI HÀNH CHƯƠNG TRÌNH (PROGRAM EXECUTION)
# Cho phép chạy server bằng lệnh đơn giản: python main.py
# =========================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)