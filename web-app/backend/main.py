import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

# ĐƯỜNG DẪN IMPORT PHẢI CHÍNH XÁC:
# Nếu file gateway_client.py nằm trong folder 'core', bạn phải import từ 'core.gateway_client'
from core.gateway_client import GatewayClient 
from core import handlers
from routers import auth

# ... setup app ...
app = FastAPI()
app.include_router(auth.router)

# 1. Khởi tạo instance
client = GatewayClient("ws://localhost:8765")

# ... (phần setup_handlers và lifespan giống code cũ) ...

# 2. Hàm đăng ký các sự kiện
def setup_handlers():
    client.on("applications_list_response", handlers.handle_application_list)
    client.on("process_list_response", handlers.handle_process_list)
    client.on("screenshot_response", handlers.handle_screenshot_data)
    client.on("permission_request", handlers.handle_permission_request)

# 3. Sử dụng lifespan để quản lý vòng đời ứng dụng (Thay cho @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    setup_handlers()
    # Khởi chạy kết nối Gateway trong background
    gateway_task = asyncio.create_task(client.connect())
    
    yield # Server bắt đầu chạy
    
    # --- Shutdown ---
    # Hủy task kết nối khi tắt server
    gateway_task.cancel()

app = FastAPI(lifespan=lifespan)

# 4. API Endpoints
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
    # Chạy server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)