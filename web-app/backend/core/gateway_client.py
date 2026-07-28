# web-app/backend/core/gateway_client.py
import json
import logging
import asyncio
import uuid
import websockets
from typing import Dict, Any, Optional, Callable, Awaitable
from core.config import settings

logger = logging.getLogger("GatewayClient")

class GatewayClient:
    """
    Kết nối WebSocket bền vững tới Gateway.
    Duy trì một kết nối duy nhất trong suốt vòng đời của Backend.
    Hỗ trợ gửi lệnh và nhận phản hồi qua cơ chế pending requests.
    """
    def __init__(self):
        self.ws_url = settings.GATEWAY_WS_URL
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._pending: Dict[str, asyncio.Future] = {}
        self._message_handler: Optional[Callable[[Dict], Awaitable[None]]] = None
        self._connect_lock = asyncio.Lock()

    async def connect(self):
        """Kết nối tới Gateway và duy trì vòng lặp nhận tin."""
        async with self._connect_lock:
            if self.ws and not self.ws.closed:
                return
            try:
                self.ws = await websockets.connect(self.ws_url, ping_interval=20)
                await self._authenticate()
                self._running = True
                asyncio.create_task(self._listen_loop())
                logger.info("Đã kết nối và xác thực với Gateway")
            except Exception as e:
                logger.error(f"Không thể kết nối tới Gateway: {e}")
                self.ws = None
                raise

    async def _authenticate(self):
        auth = {
            "type": "system.auth",
            "source": "webapp",
            "payload": {"secret": settings.AGENT_SECRET_KEY}
        }
        await self.ws.send(json.dumps(auth))
        resp = await asyncio.wait_for(self.ws.recv(), timeout=10)
        data = json.loads(resp)
        if not data.get("payload", {}).get("success"):
            raise ConnectionError("Xác thực với Gateway thất bại")

    async def _listen_loop(self):
        while self._running and self.ws and not self.ws.closed:
            try:
                msg = await self.ws.recv()
                data = json.loads(msg)
                msg_id = data.get("messageId")
                if msg_id and msg_id in self._pending:
                    fut = self._pending.pop(msg_id)
                    if data.get("type") == "error":
                        fut.set_exception(Exception(data.get("payload", {}).get("message", "Unknown error")))
                    else:
                        fut.set_result(data.get("payload", {}))
                elif self._message_handler:
                    await self._message_handler(data)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Mất kết nối Gateway, sẽ thử lại...")
                break
            except Exception as e:
                logger.error(f"Lỗi trong vòng lặp nhận Gateway: {e}")
        self._running = False
        self.ws = None
        # Tự động reconnect sau 3 giây
        await asyncio.sleep(3)
        asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self):
        while not self._running:
            try:
                await self.connect()
                logger.info("Đã kết nối lại Gateway thành công")
            except Exception:
                logger.warning("Thử kết nối lại Gateway sau 3 giây...")
                await asyncio.sleep(3)

    async def send_command(self, machine_id: str, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if payload is None:
            payload = {}

        message_id = uuid.uuid4().hex
        command_packet = {
            "messageId": message_id,
            "type": action,
            "source": "webapp",
            "destination": machine_id,
            "payload": payload
        }

        if not self.ws or self.ws.closed:
            try:
                await self.connect()
            except Exception as e:
                return {"success": False, "error": f"Gateway connection error: {str(e)}"}

        fut = asyncio.get_event_loop().create_future()
        self._pending[message_id] = fut
        try:
            await self.ws.send(json.dumps(command_packet))
            result = await asyncio.wait_for(fut, timeout=30)
            return {"success": True, "data": result}
        except asyncio.TimeoutError:
            self._pending.pop(message_id, None)
            return {"success": False, "error": "Gateway timeout: không nhận được phản hồi"}
        except Exception as e:
            self._pending.pop(message_id, None)
            return {"success": False, "error": str(e)}

    def set_message_handler(self, handler: Callable[[Dict], Awaitable[None]]):
        self._message_handler = handler

    async def disconnect(self):
        self._running = False
        if self.ws and not self.ws.closed:
            await self.ws.close()

gateway_client = GatewayClient()