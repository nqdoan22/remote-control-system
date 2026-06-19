import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# ĐƯỜNG DẪN IMPORT PHẢI CHÍNH XÁC:
from core.gateway_client import GatewayClient 
from core import handlers
from routers import auth

# 1. Khởi tạo Gateway Client instance
client = GatewayClient("ws://localhost:8765")

# 2. Hàm đăng ký các sự kiện xử lý từ Gateway gửi về
def setup_handlers():
    client.on("applications_list_response", handlers.handle_application_list)
    client.on("process_list_response", handlers.handle_process_list)
    client.on("screenshot_response", handlers.handle_screenshot_data)
    client.on("permission_request", handlers.handle_permission_request)

# 3. Sử dụng lifespan để quản lý vòng đời ứng dụng (Thay cho @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # # --- Startup (Chạy khi server bật) ---
    # setup_handlers()
    # # Khởi chạy kết nối Gateway trong background
    # gateway_task = asyncio.create_task(client.connect())
    
    yield # Server bắt đầu nhận request từ người dùng
    
    # --- Shutdown (Chạy khi tắt server) ---
    # gateway_task.cancel()
    # try:
    #     await gateway_task
    # except asyncio.CancelledError:
    #     pass

# 4. Khởi tạo ứng dụng FastAPI DUY NHẤT và gắn lifespan vào
app = FastAPI(title="Remote Control System API", lifespan=lifespan)

# 5. CẤU HÌNH CORS (Sửa lỗi chặn Đăng nhập từ Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép TẤT CẢ các origin truy cập, không bao giờ lo bị chặn CORS nữa
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 6. Đăng ký các Router chức năng
app.include_router(auth.router)

# 7. API Endpoints
@app.post("/control/{machine_id}")
async def control_machine(machine_id: str, command: dict):
    """
    Endpoint để Frontend gửi lệnh điều khiển xuống Agent.
    Command format: {"module": "...", "action": "...", "payload": {...}}
    """
    await client.send_command(
        machine_id=machine_id,
        module=command.get("module"),
        action=command.get("action"),
        payload=command.get("payload", {})
    )
    return {"status": "sent", "machine_id": machine_id}

@app.get("/health")
async def health_check():
    """Kiểm tra trạng thái kết nối."""
    return {
        "status": "online", 
        "gateway_connected": client.websocket is not None and client.websocket.open
    }

if __name__ == "__main__":
    import uvicorn
    # Ép uvicorn chạy chính xác trên IP số 127.0.0.1 để khớp với Frontend
    uvicorn.run(app, host="127.0.0.1", port=8000)