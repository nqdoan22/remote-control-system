"""
main.py — Gateway entry point.

Khởi động WebSocket server với hai endpoint riêng biệt:
  - /client  : Client App kết nối vào
  - /webapp  : Web App kết nối vào

Theo system_architecture.md: Gateway là điểm kết nối duy nhất,
không xử lý Business Logic.
"""

import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol

import config
from core.command_tracker import CommandTracker
from core.connection_manager import ConnectionManager
from core.heartbeat_manager import start_heartbeat
from core.permission_manager import PermissionManager
from handlers.client_handler import handle_client
from handlers.webapp_handler import handle_webapp

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gateway")

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

manager = ConnectionManager()
manager.permission_manager = PermissionManager()
manager.command_tracker = CommandTracker()

# ---------------------------------------------------------------------------
# Router — phân biệt /client và /webapp theo path
# ---------------------------------------------------------------------------

async def router(websocket: WebSocketServerProtocol):
    """
    Nhận kết nối WebSocket và điều hướng đến đúng handler
    dựa trên request path.
    """
    path = websocket.path

    if path == "/client":
        logger.info("New Client App connection from %s", websocket.remote_address)
        await handle_client(websocket, manager)

    elif path == "/webapp":
        logger.info("New Web App connection from %s", websocket.remote_address)
        await handle_webapp(websocket, manager)

    else:
        logger.warning(
            "Rejected unknown path '%s' from %s", path, websocket.remote_address
        )
        await websocket.close(code=4004, reason="Unknown path")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    logger.info(
        "Gateway starting on ws://%s:%d", config.GATEWAY_HOST, config.GATEWAY_PORT
    )
    logger.info(
        "Registered machines: %d",
        len(config.REGISTERED_MACHINES),
    )

    async with websockets.serve(
        router,
        config.GATEWAY_HOST,
        config.GATEWAY_PORT,
        max_size=config.MAX_WS_MESSAGE_SIZE,
    ):
        # Khởi động heartbeat monitor cùng lúc với server
        heartbeat_task = start_heartbeat(manager)
        logger.info("Gateway is ready.")

        try:
            await asyncio.Future()  # chạy mãi mãi
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    try:
        # Chạy Event Loop chính của Asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[EXIT] Đã dừng chương trình bằng bàn phím (Ctrl+C).")