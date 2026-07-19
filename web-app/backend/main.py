# web-app/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager  # 🌟 Thêm thư viện quản lý vòng đời ứng dụng

# 📦 IMPORT CÁC PHÒNG CHỨC NĂNG TỪ THƯ MỤC ROUTERS
from routers import auth, machines, modules 

# 🔌 IMPORT ANH ĐIỀU PHỐI ĐƯỜNG DÂY NÓNG WEBSOCKET
from core.gateway_client import gateway_client

# =====================================================================
# ⚙️ QUẢN LÝ VÒNG ĐỜI ỨNG DỤNG (LIFESPAN) - ĐỒNG BỘ GIẢI PHÓNG BỘ NHỚ
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🛫 [HÀNH ĐỘNG 1]: Khi server Backend vừa nổ máy bật lên
    print("🚀 Backend đang khởi động... Tiến hành kết nối tới Gateway WebSocket...")
    
    # Kích hoạt anh điều phối kết nối vật lý sang Gateway mạng LAN
    await gateway_client.connect()  
    
    yield  # 🟢 Hệ thống chạy bình thường tại đây, đợi người dùng thao tác
    
    # 🛬 [HÀNH ĐỘNG 2]: Khi bạn bấm Ctrl + C để tắt Server Backend
    print("🛑 Backend đang tắt... Tiến hành dọn dẹp tài nguyên hệ thống an toàn.")
    
    # 🛡️ BỔ SUNG ĐỒNG BỘ: Ép hủy Task lắng nghe ngầm (_listen_loop) để tránh rò rỉ RAM (Memory Leak)
    if hasattr(gateway_client, 'listen_task') and gateway_client.listen_task:
        print("🧹 Đang ép hủy (Cancel) luồng lắng nghe bất đồng bộ chạy ngầm của Gateway Client...")
        gateway_client.listen_task.cancel()
        try:
            # Chờ luồng nhận biết lệnh hủy hoàn tất
            await gateway_client.listen_task
        except Exception:
            # Bỏ qua ngoại lệ hủy Task thông thường của asyncio
            pass
            
    # Đóng kết nối Socket vật lý nếu ống dẫn còn mở
    if gateway_client.websocket:
        print("🔌 Đang ngắt kết nối đường truyền socket vật lý...")
        await gateway_client.websocket.close()
        print("✅ Đã giải phóng hoàn toàn tài nguyên kết nối.")

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
    # Chạy uvicorn server tại local IP, kích hoạt chế độ auto-reload khi sửa code
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)