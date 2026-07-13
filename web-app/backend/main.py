# web-app/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 📦 IMPORT CÁC PHÒNG CHỨC NĂNG TỪ THƯ MỤC ROUTERS
from routers import auth
from routers import machines
from routers import modules  # 🌟 Đảm bảo phòng quản lý 8 module đã được gọi vào đây

# Khởi tạo tổng đài Backend FastAPI
app = FastAPI(
    title="Hệ thống Điều khiển từ xa API", 
    description="Backend trung gian xử lý dữ liệu và điều hướng lệnh xuống Agent LAN",
    version="1.0.0"
)

# 🔌 CẤU HÌNH CORS (Mở cửa cho Frontend React kết nối sang mà không bị trình duyệt chặn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Địa chỉ mặc định của Frontend React
    allow_credentials=True,
    allow_methods=["*"],                      # Cho phép tất cả các hàm GET, POST, OPTIONS...
    allow_headers=["*"],                      # Cho phép tất cả các định dạng dữ liệu (Headers)
)

# 🔗 ĐẤU NỐI ĐỊNH TUYẾN: Kích hoạt các phòng chức năng hoạt động
app.include_router(auth.router)       # Kích hoạt ô cửa Đăng nhập / Đăng xuất (/api/auth)
app.include_router(machines.router)   # Kích hoạt ô cửa Danh sách máy ở Dashboard (/api/machines)
app.include_router(modules.router)    # Kích hoạt ô cửa Điều khiển của đầy đủ 8 module (/api/modules)

# Cổng kiểm tra nhanh trạng thái hoạt động của Server (Home Endpoint)
@app.get("/")
def root():
    return {
        "status": "active",
        "message": "Hệ thống Backend đang hoạt động ổn định. Sẵn sàng nhận lệnh từ Frontend!"
    }

# Lệnh nổi lửa kích hoạt Server Python chạy ở Port 8000
if __name__ == "__main__":
    import uvicorn
    # reload=True giúp server tự làm mới mỗi khi bạn bấm Ctrl + S lưu code
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)