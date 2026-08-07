"""
models/message.py — Message format và helpers.

Định nghĩa cấu trúc message theo api_contract.md.
Mọi thành phần trong Gateway dùng module này để tạo và parse message,
không build dict thủ công.
"""

import uuid
import time
from typing import Any


# ---------------------------------------------------------------------------
# Helpers tạo message
# ---------------------------------------------------------------------------

def make_message(
    msg_type: str,
    payload: dict,
    source: str = "gateway",
    destination: str = "",
    message_id: str | None = None,
) -> dict:
    """Tạo một message chuẩn theo general message format."""
    return {
        "messageId": message_id or str(uuid.uuid4()),
        "type": msg_type,
        "timestamp": int(time.time()),
        "source": source,
        "destination": destination,
        "payload": payload,
    }


def make_response(
    success: bool,
    data: dict | None = None,
    destination: str = "",
    original_message_id: str | None = None,
) -> dict:
    """Tạo response thành công."""
    payload: dict[str, Any] = {
        "success": success,
        "data": data or {},
    }
    # Cho phép response mang originalMessageId để bên gửi (Backend Web App) có
    # thể khớp đúng request đang chờ — cần cho lệnh machine.list (reconcile).
    if original_message_id:
        payload["originalMessageId"] = original_message_id

    return make_message(
        msg_type="response",
        payload=payload,
        destination=destination,
    )


def make_error(
    code: str,
    message: str,
    destination: str = "",
    original_message_id: str | None = None,
) -> dict:
    """Tạo error response theo api_contract.md — Error Response format."""
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if original_message_id:
        payload["originalMessageId"] = original_message_id

    return make_message(
        msg_type="error",
        payload=payload,
        destination=destination,
    )


# ---------------------------------------------------------------------------
# Helpers parse message
# ---------------------------------------------------------------------------

def get_type(message: dict) -> str:
    """Lấy message type, trả về chuỗi rỗng nếu không có."""
    return message.get("type", "")


def get_payload(message: dict) -> dict:
    """Lấy payload, trả về dict rỗng nếu không có."""
    return message.get("payload", {})


def get_message_id(message: dict) -> str:
    """Lấy messageId, trả về chuỗi rỗng nếu không có."""
    return message.get("messageId", "")


def get_destination(message: dict) -> str:
    """Lấy destination, trả về chuỗi rỗng nếu không có."""
    return message.get("destination", "")


def get_source(message: dict) -> str:
    """Lấy source, trả về chuỗi rỗng nếu không có."""
    return message.get("source", "")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"messageId", "type", "timestamp", "source", "destination", "payload"}


def validate_message(message: dict) -> tuple[bool, str]:
    """
    Kiểm tra message có đủ các field bắt buộc không.

    Returns:
        (True, "") nếu hợp lệ.
        (False, reason) nếu không hợp lệ.
    """
    missing = REQUIRED_FIELDS - message.keys()
    if missing:
        return False, f"Missing required fields: {', '.join(sorted(missing))}"

    if not isinstance(message.get("payload"), dict):
        return False, "payload must be a JSON object"

    if not isinstance(message.get("type"), str) or not message["type"].strip():
        return False, "type must be a non-empty string"

    return True, ""
