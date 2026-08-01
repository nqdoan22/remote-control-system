"""
handlers/webapp_handler.py — Xử lý kết nối từ Web App.

Flow theo security_design.md:
  1. Web App kết nối WebSocket tới /webapp
  2. Message đầu tiên PHẢI là auth.webapp
  3. Gateway validate JWT token bằng JWT_SECRET
  4. Nếu hợp lệ → gửi response success, chuyển sang receive loop
  5. Nếu không hợp lệ → gửi error AUTHENTICATION_FAILED, đóng kết nối
"""

import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol

from core.auth_manager import validate_webapp
from core.connection_manager import ConnectionManager
from handlers.message_router import route_from_webapp
from models.message import (
    make_response,
    make_error,
    get_type,
    get_payload,
    get_message_id,
    validate_message,
)

logger = logging.getLogger("gateway.webapp_handler")

# Giây — thời gian chờ message auth.webapp đầu tiên
AUTH_TIMEOUT = 10


async def handle_webapp(websocket: WebSocketServerProtocol, manager: ConnectionManager):
    """Entry point cho kết nối từ Web App."""
    remote = websocket.remote_address
    authenticated = False
    admin_user: str | None = None

    try:
        # ------------------------------------------------------------------
        # Bước 1: Chờ message auth.webapp đầu tiên
        # ------------------------------------------------------------------
        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=AUTH_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("Web App %s did not send auth.webapp within %ds", remote, AUTH_TIMEOUT)
            await _send(websocket, make_error(
                "AUTHENTICATION_FAILED",
                "Authentication timeout. Send auth.webapp as first message.",
            ))
            await websocket.close(code=4001, reason="Authentication timeout")
            return

        # ------------------------------------------------------------------
        # Bước 2: Parse và validate message format
        # ------------------------------------------------------------------
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Web App %s sent invalid JSON", remote)
            await _send(websocket, make_error("AUTHENTICATION_FAILED", "Invalid JSON"))
            await websocket.close(code=4001, reason="Invalid JSON")
            return

        ok, reason = validate_message(message)
        if not ok:
            logger.warning("Web App %s sent malformed message: %s", remote, reason)
            await _send(websocket, make_error("AUTHENTICATION_FAILED", reason))
            await websocket.close(code=4001, reason="Malformed message")
            return

        msg_type = get_type(message)
        if msg_type != "auth.webapp":
            logger.warning(
                "Web App %s sent '%s' before auth.webapp", remote, msg_type
            )
            await _send(websocket, make_error(
                "AUTHENTICATION_FAILED",
                f"Expected auth.webapp as first message, got '{msg_type}'",
            ))
            await websocket.close(code=4001, reason="Expected auth.webapp")
            return

        # ------------------------------------------------------------------
        # Bước 3: Validate JWT token
        # ------------------------------------------------------------------
        payload = get_payload(message)
        token = payload.get("token", "")

        auth_ok, auth_reason, jwt_payload = validate_webapp(token)

        if not auth_ok:
            logger.warning("Web App %s authentication failed: %s", remote, auth_reason)
            await _send(
                websocket,
                make_error(
                    "AUTHENTICATION_FAILED",
                    auth_reason,
                    original_message_id=get_message_id(message),
                ),
            )
            await websocket.close(code=4001, reason="Authentication failed")
            return

        # ------------------------------------------------------------------
        # Bước 4: Xác thực thành công
        # ------------------------------------------------------------------
        authenticated = True
        admin_user = jwt_payload.get("sub", "unknown")

        logger.info("Web App authenticated: admin='%s' from %s", admin_user, remote)

        await _send(
            websocket,
            make_response(
                success=True,
                data={},
                destination="webapp",
            ),
        )

        # Đăng ký vào ConnectionManager
        await manager.register_webapp(websocket)

        # ------------------------------------------------------------------
        # Bước 5: Receive loop — xử lý các message tiếp theo
        # ------------------------------------------------------------------
        async for raw in websocket:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from Web App (admin='%s')", admin_user)
                continue

            ok, reason = validate_message(message)
            if not ok:
                logger.warning("Malformed message from Web App: %s", reason)
                continue

            msg_type = get_type(message)
            logger.debug("Received '%s' from Web App (admin='%s')", msg_type, admin_user)

            await route_from_webapp(
                message,
                manager,
                manager.permission_manager,
                admin_user or "unknown",
                manager.command_tracker,
            )

    except websockets.exceptions.ConnectionClosed as exc:
        logger.info(
            "Web App (admin='%s', %s) disconnected: %s",
            admin_user or "unauthenticated", remote, exc,
        )

    finally:
        if authenticated:
            await manager.unregister_webapp()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _send(websocket: WebSocketServerProtocol, message: dict):
    """Gửi message JSON, bỏ qua nếu kết nối đã đóng."""
    try:
        await websocket.send(json.dumps(message))
    except websockets.exceptions.ConnectionClosed:
        pass
