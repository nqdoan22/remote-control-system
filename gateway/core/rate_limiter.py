"""
core/rate_limiter.py — Giới hạn số lần xác thực sai liên tiếp theo địa chỉ IP.

Theo security_design.md, machineSecret là cơ chế chống giả mạo Client App.
Trước đây không có giới hạn số lần thử, cho phép brute-force machineSecret
không giới hạn tốc độ. Module này khóa tạm thời một IP sau khi vượt quá số
lần thất bại cho phép trong một cửa sổ thời gian.
"""

import time

import config


class AuthRateLimiter:
    """Theo dõi số lần auth thất bại liên tiếp theo key (thường là IP)."""

    def __init__(self, max_attempts: int, lockout_seconds: float):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        # key -> danh sách timestamp các lần thất bại gần đây
        self._failures: dict[str, list[float]] = {}

    def is_locked_out(self, key: str) -> bool:
        now = time.time()
        attempts = [t for t in self._failures.get(key, []) if now - t < self.lockout_seconds]
        self._failures[key] = attempts
        return len(attempts) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        now = time.time()
        self._failures.setdefault(key, []).append(now)

    def record_success(self, key: str) -> None:
        self._failures.pop(key, None)


# Singleton dùng chung cho toàn bộ Gateway — auth rate limiting là mối quan tâm
# stateless ở tầng kết nối, giống cách config.py cung cấp hằng số dùng chung.
client_auth_limiter = AuthRateLimiter(
    max_attempts=config.AUTH_MAX_ATTEMPTS,
    lockout_seconds=config.AUTH_LOCKOUT_SECONDS,
)
