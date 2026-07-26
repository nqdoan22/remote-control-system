"""
core/auth_manager.py — Xác thực Client App và Web App.

Theo security_design.md:
  - Client App: validate machineId + machineSecret với REGISTERED_MACHINES
  - Web App: validate JWT token bằng JWT_SECRET (HS256)
"""

import logging
import jwt

import config

logger = logging.getLogger("gateway.auth_manager")


# ---------------------------------------------------------------------------
# Client App authentication
# ---------------------------------------------------------------------------

def validate_client(machine_id: str, machine_secret: str) -> tuple[bool, str]:
    """
    Kiểm tra machineId + machineSecret với danh sách đã đăng ký.

    Returns:
        (True, "")             — hợp lệ
        (False, error_reason)  — không hợp lệ
    """
    if not machine_id or not machine_secret:
        return False, "machineId and machineSecret are required"

    if not config.REGISTERED_MACHINES:
        logger.warning(
            "REGISTERED_MACHINES is empty — no client can authenticate. "
            "Check .env configuration."
        )
        return False, "No registered machines configured"

    expected_secret = config.REGISTERED_MACHINES.get(machine_id)
    if expected_secret is None:
        logger.warning("Auth failed: unknown machineId '%s'", machine_id)
        return False, "Unknown machineId"

    if expected_secret != machine_secret:
        logger.warning("Auth failed: wrong machineSecret for machineId '%s'", machine_id)
        return False, "Invalid machineSecret"

    return True, ""


# ---------------------------------------------------------------------------
# Web App authentication
# ---------------------------------------------------------------------------

def validate_webapp(token: str) -> tuple[bool, str, dict]:
    """
    Validate JWT token từ Web App.

    Returns:
        (True, "", payload)     — hợp lệ, payload chứa sub/iat/exp
        (False, reason, {})     — không hợp lệ
    """
    if not token:
        return False, "Token is required", {}

    if not config.JWT_SECRET:
        logger.error(
            "JWT_SECRET is not configured — Web App cannot authenticate. "
            "Check .env configuration."
        )
        return False, "JWT_SECRET not configured on server", {}

    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM],
        )
        return True, "", payload

    except jwt.ExpiredSignatureError:
        logger.warning("Auth failed: JWT token expired")
        return False, "Token expired", {}

    except jwt.InvalidTokenError as exc:
        logger.warning("Auth failed: invalid JWT token — %s", exc)
        return False, "Invalid token", {}
