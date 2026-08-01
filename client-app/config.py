"""
===============================================================================
FILE: client-app/config.py
PURPOSE: Quản lý toàn bộ cấu hình hệ thống, thông tin định danh Agent, 
         tham số kết nối Gateway và các chính sách bảo mật Sandbox/Privacy.
ARCHITECTURE ROLE:
  - Đóng vai trò Single Source of Truth (SSOT) cho Client App (Agent).
  - Khởi tạo thông tin định danh máy tính (Hostname, IP) khớp với MachineSchema.
  - Cung cấp hằng số cho Giao thức Envelope (WSMessage) và Luồng xin quyền.
===============================================================================
"""

import os
import socket
import platform
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


def get_local_ip() -> str:
    """
    Hàm bổ trợ tự động dò tìm địa chỉ IP LAN (IPv4) thực tế của máy Client.
    Giúp tránh lấy nhầm IP Loopback (127.0.0.1) hoặc IP của card mạng ảo (Docker/VMware).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Không cần kết nối thật, chỉ mượn bảng routing của OS để tìm IP xuất mạng LAN
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class ClientSettings(BaseSettings):
    """
    Class quản lý toàn bộ Cấu hình của Client App (Agent).
    Hỗ trợ đọc tự động từ biến môi trường (.env) hoặc dùng giá trị mặc định.
    """

    # =========================================================================
    # 1. GATEWAY & NETWORK CONFIG (Cấu hình kết nối Gateway WebSocket)
    # =========================================================================
    GATEWAY_WS_URL: str = Field(
        default="ws://127.0.0.1:8765/ws/client",
        description="Đường dẫn WebSocket Endpoint của Gateway server."
    )
    RECONNECT_INTERVAL_SECONDS: int = Field(
        default=5,
        description="Khoảng thời gian (giây) chờ thử kết nối lại khi rớt mạng WebSocket."
    )
    HEARTBEAT_INTERVAL_SECONDS: int = Field(
        default=5,
        description="Chu kỳ (giây) gửi tín hiệu Heartbeat điểm danh tới Gateway."
    )

    # =========================================================================
    # 2. AGENT IDENTITY (Định danh máy Client - Khớp với machine.py Schema)
    # =========================================================================
    CLIENT_ID: str = Field(
        default_factory=lambda: f"client-{socket.gethostname().lower()}",
        description="Mã định danh duy nhất (machine_id) của Agent trong hệ thống."
    )
    CLIENT_SECRET: str = Field(
        default="DEFAULT_SECRET_KEY_123",
        description="Mật khẩu bí mật để xác thực khi đăng ký với Gateway/Backend. Phải khớp với AGENT_SECRET_KEY của Gateway."
    )
    HOSTNAME: str = Field(
        default_factory=socket.gethostname,
        description="Tên máy tính khai báo trong hệ điều hành Windows."
    )
    IP_ADDRESS: str = Field(
        default_factory=get_local_ip,
        description="Địa chỉ IPv4 LAN của máy Client."
    )
    OS_INFO: str = Field(
        default_factory=lambda: f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
        description="Thông tin chi tiết về hệ điều hành đang chạy."
    )

    # =========================================================================
    # 3. PRIVACY & SECURITY POLICIES (Chính sách Bảo mật & Quyền riêng tư)
    # =========================================================================
    PERMISSION_TIMEOUT_SECONDS: int = Field(
        default=15,
        description="Thời gian tối đa (giây) đếm ngược chờ End User bấm Accept trên Popup."
    )
    SANDBOX_DIR: Path = Field(
        default=Path("C:/AgentSandbox"),
        description="Thư mục cô lập an toàn cho phép thao tác File Manager."
    )
    RED_INDICATOR_ENABLED: bool = Field(
        default=True,
        description="Kích hoạt đèn báo đỏ nhấp nháy góc màn hình khi bật Webcam."
    )

    # =========================================================================
    # 4. STREAMING & MODULE PERFORMANCE (Cấu hình hiệu năng truyền dữ liệu)
    # =========================================================================
    SCREEN_FPS: int = Field(
        default=10,
        description="Tốc độ khung hình (FPS) tối đa khi Live Screen Stream."
    )
    WEBCAM_FPS: int = Field(
        default=15,
        description="Tốc độ khung hình (FPS) tối đa khi Webcam Stream."
    )
    JPEG_QUALITY: int = Field(
        default=60,
        description="Mức chất lượng nén ảnh JPEG (1-100) để tối ưu băng thông mạng LAN."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Khởi tạo đối tượng config duy nhất cho toàn bộ Client App dùng chung
settings = ClientSettings()

# Tự động tạo thư mục Sandbox nếu chưa tồn tại trên ổ đĩa
os.makedirs(settings.SANDBOX_DIR, exist_ok=True)