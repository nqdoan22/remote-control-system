"""
config.py — Tải cấu hình từ .env và định nghĩa các hằng số hệ thống.

Mọi thành phần trong Gateway import settings từ đây,
không đọc biến môi trường trực tiếp.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

GATEWAY_HOST: str = os.getenv("GATEWAY_HOST", "0.0.0.0")
GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8765"))

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM: str = "HS256"

# Danh sách machines được phép kết nối: { machineId: machineSecret }
# Đọc từ REGISTERED_MACHINES="id1:secret1,id2:secret2"
def _parse_registered_machines() -> dict[str, str]:
    raw = os.getenv("REGISTERED_MACHINES", "")
    machines: dict[str, str] = {}
    if not raw.strip():
        return machines
    for entry in raw.split(","):
        entry = entry.strip()
        if ":" in entry:
            machine_id, secret = entry.split(":", 1)
            machines[machine_id.strip()] = secret.strip()
    return machines

REGISTERED_MACHINES: dict[str, str] = _parse_registered_machines()

# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

# Giây — Client App gửi heartbeat mỗi 15s (định nghĩa ở Client App)
HEARTBEAT_INTERVAL: int = 15

# Giây — Nếu không nhận heartbeat trong 45s → đánh dấu Offline
HEARTBEAT_TIMEOUT: int = int(os.getenv("HEARTBEAT_TIMEOUT", "45"))

# Giây — Khoảng thời gian background task kiểm tra heartbeat
HEARTBEAT_CHECK_INTERVAL: int = 5

# ---------------------------------------------------------------------------
# Command Timeout
# ---------------------------------------------------------------------------

# Giây — Nếu Client App không phản hồi (response/error) cho một command trong
# khoảng thời gian này → Gateway trả lỗi TIMEOUT cho Web App.
COMMAND_TIMEOUT: int = int(os.getenv("COMMAND_TIMEOUT", "15"))

# ---------------------------------------------------------------------------
# Auth Rate Limiting
# ---------------------------------------------------------------------------

# Số lần auth.client sai liên tiếp tối đa từ cùng một IP trước khi bị khóa tạm thời.
AUTH_MAX_ATTEMPTS: int = int(os.getenv("AUTH_MAX_ATTEMPTS", "5"))

# Giây — Thời gian khóa sau khi vượt quá AUTH_MAX_ATTEMPTS.
AUTH_LOCKOUT_SECONDS: float = float(os.getenv("AUTH_LOCKOUT_SECONDS", "60"))

# ---------------------------------------------------------------------------
# Permission Confirmation
# ---------------------------------------------------------------------------

# Giây — Nếu End User không phản hồi trong 30s → PERMISSION_TIMEOUT
PERMISSION_TIMEOUT: int = int(os.getenv("PERMISSION_TIMEOUT", "30"))

# Danh sách message types yêu cầu permission confirmation
# Source of truth: docs/api_contract.md — Sensitive Feature List
SENSITIVE_MESSAGE_TYPES: frozenset[str] = frozenset({
    "screen.screenshot",
    "screen.live.start",
    "webcam.start",
    "input_audit.start",
    "power.lock",
    "power.restart",
    "power.shutdown",
    "power.sleep",
})
