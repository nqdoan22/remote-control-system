"""
core/heartbeat_manager.py — Phát hiện Client App mất kết nối đột ngột.

Vấn đề cần giải quyết:
  Khi Client App crash hoặc mạng đứt đột ngột (không gửi WebSocket close frame),
  Gateway không nhận được sự kiện disconnect. Machine vẫn được đánh dấu "online"
  dù thực tế đã mất kết nối.

Giải pháp:
  Background task chạy mỗi HEARTBEAT_CHECK_INTERVAL giây, kiểm tra lastSeen
  của từng machine. Nếu vượt quá HEARTBEAT_TIMEOUT → đánh dấu offline,
  xóa socket stale, notify Web App.

Thông số theo api_contract.md:
  HEARTBEAT_INTERVAL  = 15s  (Client App gửi)
  HEARTBEAT_TIMEOUT   = 45s  (Gateway timeout)
  CHECK_INTERVAL      = 5s   (tần suất quét)
"""

import asyncio
import logging

import config
from core.connection_manager import ConnectionManager

logger = logging.getLogger("gateway.heartbeat_manager")


async def heartbeat_loop(manager: ConnectionManager) -> None:
    """
    Background task — chạy suốt vòng đời của Gateway.

    Mỗi CHECK_INTERVAL giây:
      1. Gọi registry.mark_offline_if_stale() để tìm machine hết hạn.
      2. Với mỗi machine vừa bị đánh dấu offline:
         - Xóa socket stale khỏi _client_sockets (tránh gửi tiếp vào socket chết).
         - Notify Web App qua _notify_machine_status.
    """
    logger.info(
        "Heartbeat monitor started (timeout=%ds, check_interval=%ds)",
        config.HEARTBEAT_TIMEOUT,
        config.HEARTBEAT_CHECK_INTERVAL,
    )

    while True:
        await asyncio.sleep(config.HEARTBEAT_CHECK_INTERVAL)

        try:
            stale_ids = manager.registry.mark_offline_if_stale(
                timeout_seconds=config.HEARTBEAT_TIMEOUT
            )

            for machine_id in stale_ids:
                logger.warning(
                    "Machine '%s' timed out — marking offline", machine_id
                )

                # Xóa socket stale để tránh gửi message vào kết nối chết
                stale_ws = manager.remove_client_socket(machine_id)
                if stale_ws is not None:
                    try:
                        await stale_ws.close(code=4000, reason="Heartbeat timeout")
                    except Exception:
                        pass  # socket đã chết, bỏ qua

                # Notify Web App
                await manager._notify_machine_status(machine_id, "offline")

        except Exception as exc:
            # Không để exception dừng background task
            logger.error("Heartbeat loop error: %s", exc, exc_info=True)


def start_heartbeat(manager: ConnectionManager) -> asyncio.Task:
    """
    Khởi động heartbeat_loop như một asyncio Task.
    Trả về Task để main.py có thể cancel khi shutdown nếu cần.
    """
    task = asyncio.create_task(heartbeat_loop(manager), name="heartbeat_monitor")
    return task
