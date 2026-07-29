# client-app/config.py
import os
import socket
import uuid

class ClientConfig:
    """
    Cấu hình hệ thống cho Client Agent.
    """
    # ------------------------------------------------------------------
    # 1. KẾT NỐI GATEWAY
    # ------------------------------------------------------------------
    GATEWAY_WS_URL: str = os.getenv("GATEWAY_WS_URL", "ws://localhost:8765")
    
    # Secret Key xác thực với Gateway (Khớp với GATEWAY và BACKEND)
    MACHINE_SECRET_KEY: str = os.getenv("MACHINE_SECRET_KEY", "d8e8fca2dc0f896fd7cb4cb0031ba249")

    # ------------------------------------------------------------------
    # 2. ĐỊNH DANH MÁY TRẠM (CLIENT IDENTIFIER)
    # ------------------------------------------------------------------
    # Lấy tên máy tính hiện tại (VD: DESKTOP-LAB1)
    HOSTNAME: str = socket.gethostname()
    
    # Lấy IP LAN nội bộ
    try:
        IP_ADDRESS: str = socket.gethostbyname(HOSTNAME)
    except Exception:
        IP_ADDRESS: str = "127.0.0.1"

    # Tạo UUID định danh cố định dựa trên địa chỉ MAC của máy
    MACHINE_ID: str = f"mac-{uuid.getnode()}"

    # ------------------------------------------------------------------
    # 3. CẤU HÌNH BẢO AN & RECONNECT
    # ------------------------------------------------------------------
    HEARTBEAT_INTERVAL: int = 5  # Gửi Heartbeat định kỳ mỗi 5 giây
    RECONNECT_DELAY: int = 5     # Thử kết nối lại sau 5 giây nếu mất mạng
    
    # Thư mục Sandbox lưu trữ/thao tác file an toàn
    SANDBOX_DIR: str = os.path.join(os.path.expanduser("~"), "AgentSandbox")

config = ClientConfig()

# Tự động tạo thư mục Sandbox nếu chưa có
if not os.path.exists(config.SANDBOX_DIR):
    os.makedirs(config.SANDBOX_DIR, exist_ok=True)