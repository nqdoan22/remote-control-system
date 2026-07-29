# client-app/core/gateway_service.py
import json
import logging
import asyncio
import time
import uuid
import websockets
from PyQt6.QtCore import QThread, pyqtSignal
from config import config

logger = logging.getLogger("GatewayService")

class GatewayServiceThread(QThread):
    """
    Luồng (Thread) chạy ngầm xử lý giao tiếp WebSocket với Gateway Server.
    Sử dụng PyQt Signal để truyền dữ liệu an toàn về cho UI Main Thread.
    """
    # Các tín hiệu gửi dữ liệu ra ngoài cho UI/Modules xử lý
    command_received = pyqtSignal(dict)      # Phát khi nhận lệnh từ Admin
    connection_changed = pyqtSignal(bool)    # Phát khi trạng thái kết nối đổi (True/False)

    def __init__(self):
        super().__init__()
        self.running = True
        self.websocket = None
        self.loop = None  # event loop của thread này

    def run(self):
        """Hàm thực thi luồng chính (Event Loop của Asyncio)."""
        asyncio.run(self._main_loop())

    async def _main_loop(self):
        """Vòng lặp kết nối và duy trì WebSocket."""
        self.loop = asyncio.get_running_loop()
        while self.running:
            try:
                logger.info(f"🔌 Đang kết nối tới Gateway tại {config.GATEWAY_WS_URL}...")
                async with websockets.connect(config.GATEWAY_WS_URL) as ws:
                    self.websocket = ws
                    self.connection_changed.emit(True)
                    logger.info("✅ Kết nối Gateway thành công!")

                    # 1. Gửi gói tin Đăng ký thông tin Máy trạm (Register)
                    await self._register_machine()

                    # 2. Chạy đồng thời 2 công việc: Lắng nghe tin nhắn & Gửi Heartbeat
                    await asyncio.gather(
                        self._listen_messages(),
                        self._send_heartbeat()
                    )

            except (websockets.exceptions.ConnectionClosedError, OSError) as e:
                logger.warning(f"⚠️ Mất kết nối Gateway: {e}. Thử lại sau {config.RECONNECT_DELAY}s...")
                self.connection_changed.emit(False)
                self.websocket = None
                await asyncio.sleep(config.RECONNECT_DELAY)
            except Exception as e:
                logger.error(f"❌ Lỗi không xác định trong kết nối WebSocket: {e}")
                self.connection_changed.emit(False)
                await asyncio.sleep(config.RECONNECT_DELAY)

    async def _register_machine(self):
        """Đăng ký thông tin Agent với Gateway."""
        register_pkt = {
            "messageId": str(uuid.uuid4()),
            "type": "system.register",
            "timestamp": int(time.time()),
            "source": config.MACHINE_ID,
            "destination": "gateway",
            "payload": {
                "secret": config.MACHINE_SECRET_KEY,
                "hostname": config.HOSTNAME,
                "ip_address": config.IP_ADDRESS
            }
        }
        await self.websocket.send(json.dumps(register_pkt))
        logger.info(f"📋 Đã gửi gói tin đăng ký Agent: {config.HOSTNAME} ({config.MACHINE_ID})")

    async def _send_heartbeat(self):
        """Gửi nhịp tim (Heartbeat) định kỳ để Gateway duy trì trạng thái Online."""
        while self.running and self.websocket:
            try:
                import psutil
                cpu_usage = psutil.cpu_percent(interval=0.1)
            except Exception:
                cpu_usage = 0.0
            try:
                heartbeat_pkt = {
                    "messageId": str(uuid.uuid4()),
                    "type": "system.heartbeat",
                    "timestamp": int(time.time()),
                    "source": config.MACHINE_ID,
                    "destination": "gateway",
                    "payload": {
                        "status": "online",
                        "cpu_usage": cpu_usage
                    }
                }
                await self.websocket.send(json.dumps(heartbeat_pkt))
                await asyncio.sleep(config.HEARTBEAT_INTERVAL)
            except Exception:
                break

    async def _listen_messages(self):
        """Lắng nghe các lệnh điều khiển gửi từ Gateway."""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                logger.info(f"📩 Nhận gói tin từ Gateway: {data.get('type')}")
                
                # Bắn tín hiệu sang UI / Module Controller xử lý
                self.command_received.emit(data)
                
            except json.JSONDecodeError:
                logger.error("❌ Nhận dữ liệu không đúng định dạng JSON")

    async def send_response(self, response_data: dict):
        """Hàm hỗ trợ các Module gửi phản hồi (kết quả thực thi) ngược về Gateway.
        Dùng run_coroutine_threadsafe để gửi đúng event loop của GatewayServiceThread."""
        if self.websocket and self.loop:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.websocket.send(json.dumps(response_data)),
                    self.loop
                )
                await asyncio.wrap_future(future)
            except Exception as e:
                logger.error(f"❌ Không thể gửi kết quả về Gateway: {e}")

    def stop(self):
        """Dừng luồng kết nối an toàn."""
        self.running = False
        self.quit()