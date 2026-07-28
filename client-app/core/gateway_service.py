# client-app/core/gateway_service.py
import json
import logging
import asyncio
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

    def run(self):
        """Hàm thực thi luồng chính (Event Loop của Asyncio)."""
        asyncio.run(self._main_loop())

    async def _main_loop(self):
        """Vòng lặp kết nối và duy trì WebSocket."""
        while self.running:
            try:
                logger.info(f"Dang ket noi toi Gateway tai {config.GATEWAY_WS_URL}...")
                async with websockets.connect(config.GATEWAY_WS_URL) as ws:
                    self.websocket = ws
                    self.connection_changed.emit(True)
                    logger.info("Ket noi Gateway thanh cong!")

                    # 1. Gửi gói tin Đăng ký thông tin Máy trạm (Register)
                    await self._register_machine()

                    # 2. Chạy đồng thời 2 công việc: Lắng nghe tin nhắn & Gửi Heartbeat
                    await asyncio.gather(
                        self._listen_messages(),
                        self._send_heartbeat()
                    )

            except (websockets.exceptions.ConnectionClosedError, OSError) as e:
                logger.warning(f"Mat ket noi Gateway: {e}. Thu lai sau {config.RECONNECT_DELAY}s...")
                self.connection_changed.emit(False)
                self.websocket = None
                await asyncio.sleep(config.RECONNECT_DELAY)
            except Exception as e:
                logger.error(f"Loi khong xac dinh trong ket noi WebSocket: {e}")
                self.connection_changed.emit(False)
                await asyncio.sleep(config.RECONNECT_DELAY)

    async def _register_machine(self):
        """Đăng ký thông tin Agent với Gateway."""
        register_pkt = {
            "type": "system.auth",
            "source": config.MACHINE_ID,
            "payload": {
                "machineSecret": config.MACHINE_SECRET_KEY,
                "hostname": config.HOSTNAME,
                "ip_address": config.IP_ADDRESS
            }
        }
        await self.websocket.send(json.dumps(register_pkt))
        logger.info(f"Đã gửi gói tin đăng ký Agent: {config.HOSTNAME} ({config.MACHINE_ID})")

    async def _send_heartbeat(self):
        """Gửi nhịp tim (Heartbeat) định kỳ để Gateway duy trì trạng thái Online."""
        while self.running and self.websocket:
            try:
                heartbeat_pkt = {
                    "type": "system.heartbeat",
                    "source": config.MACHINE_ID,
                    "payload": {}
                }
                await self.websocket.send(json.dumps(heartbeat_pkt))
                await asyncio.sleep(config.HEARTBEAT_INTERVAL)
            except Exception:
                break # Thoát nếu kết nối hỏng để vòng lặp ngoài reconnect

    async def _listen_messages(self):
        """Lắng nghe các lệnh điều khiển gửi từ Gateway."""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                logger.info(f"Nhan goi tin tu Gateway: {data.get('type')}")
                
                # Bắn tín hiệu sang UI / Module Controller xử lý
                self.command_received.emit(data)
                
            except json.JSONDecodeError:
                logger.error("Nhan du lieu khong dung dinh dang JSON")

    async def send_response(self, response_data: dict):
        """Hàm hỗ trợ các Module gửi phản hồi (kết quả thực thi) ngược về Gateway."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(response_data))
            except Exception as e:
                logger.error(f"Khong the gui ket qua ve Gateway: {e}")

    def stop(self):
        """Dừng luồng kết nối an toàn."""
        self.running = False
        self.quit()