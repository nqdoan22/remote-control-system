# web-app/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import auth, machines, modules 
from core.gateway_client import gateway_client
from core.config import settings # Thêm dòng này để in log cho đẹp

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động Backend: Web App đóng vai trò là giao diện quản trị
    print(f"🚀 Backend đang khởi động... Kết nối tới Gateway tại {settings.GATEWAY_WS_URL}...")
    await gateway_client.connect()  
    
    yield  
    
    # Ép hủy Task lắng nghe ngầm để dọn dẹp RAM an toàn
    if hasattr(gateway_client, 'listen_task') and gateway_client.listen_task:
        gateway_client.listen_task.cancel()
        try:
            await gateway_client.listen_task
        except Exception:
            pass
            
    if gateway_client.websocket:
        await gateway_client.websocket.close()

# Backend bắt buộc sử dụng Python
app = FastAPI(
    title="Hệ thống Điều khiển từ xa API", 
    description="Backend trung gian xử lý, chỉ gửi Command xuống Gateway",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # ✅ Đã sửa: Cho phép mọi IP trong mạng LAN gọi API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(machines.router)
app.include_router(modules.router)

if __name__ == "__main__":
    import uvicorn
    # host="0.0.0.0" đã rất chuẩn để mở mạng LAN!
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)