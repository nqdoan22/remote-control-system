# web-app/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager  # 🌟 Thêm thư viện quản lý vòng đời ứng dụng

# 📦 IMPORT CÁC PHÒNG CHỨC NĂNG TỪ THƯ MỤC ROUTERS
from routers import auth, machines, modules 

# 🔌 IMPORT ANH ĐIỀU PHỐI ĐƯỜNG DÂY NÓNG WEBSOCKET
from core.gateway_client import gateway_client

# =====================================================================
# ⚙️ QUẢN LÝ VÒNG ĐỜI ỨNG DỤNG (LIFESPAN)
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🛫 [HÀNH ĐỘNG 1]: Khi server Backend vừa nổ máy bật lên
    print("🚀 Backend đang khởi động... Tiến hành kết nối tới Gateway WebSocket...")
    await gateway_client.connect()  # Kích hoạt anh điều phối nhấc máy gọi điện giữ liên lạc ngầm
    
    yield  # 🟢 Hệ thống chạy bình thường tại đây, đợi người dùng thao tác
    
    # 🛬 [HÀNH ĐỘNG 2]: Khi bạn bấm Ctrl + C để tắt Server Backend
    print("🛑 Backend đang tắt... Ngắt kết nối an toàn.")
    if gateway_client.websocket:
        await gateway_client.websocket.close()

# Khởi tạo tổng đài Backend FastAPI kèm theo cấu hình vòng đời lifespan
app = FastAPI(
    title="Hệ thống Điều khiển từ xa API", 
    description="Backend trung gian xử lý dữ liệu và điều hướng lệnh xuống Agent LAN",
    version="1.0.0",
    lifespan=lifespan  # 🌟 Khai báo lifespan vào đây
)

# 🔌 CẤU HÌNH CORS (Mở cửa cho Frontend React kết nối sang mà không bị trình duyệt chặn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 ĐẤU NỐI ĐỊNH TUYẾN: Kích hoạt các phòng chức năng hoạt động
app.include_router(auth.router)
app.include_router(machines.router)
app.include_router(modules.router)

# Cổng kiểm tra nhanh trạng thái hoạt động của Server
@app.get("/")
def root():
    return {
        "status": "active",
        "message": "Hệ thống Backend đang hoạt động ổn định và ĐÃ KẾT NỐI với Gateway WebSocket!"
    }

# Lệnh nổi lửa kích hoạt Server Python chạy ở Port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)