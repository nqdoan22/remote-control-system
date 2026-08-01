"""
===============================================================================
FILE: client-app/main.py
PURPOSE: File khởi chạy chính (Entry Point) cho ứng dụng Client App (Agent).
ARCHITECTURE ROLE:
  - Khởi tạo PyQt6 QApplication (Main GUI Thread).
  - Nạp thông tin cấu hình từ config.py.
  - Khởi chạy Worker Thread quản lý kết nối WebSocket với Gateway (Async/Network Thread).
  - Đóng vai trò cầu nối Signal/Slot điều hướng luồng Xin quyền (Permission Flow).
===============================================================================
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QObject

# Import cấu hình ứng dụng
from config import settings

# Import cửa sổ chính
from ui.main_window import MainWindow

# Import Service quản lý kết nối WebSocket tới Gateway
from core.gateway_service import GatewayService

# Import Bộ điều phối lệnh (Command Dispatcher)
# 👉 Thành phần này mới được thêm để THỰC SỰ xử lý các lệnh điều khiển từ WebAdmin
#    (VD: start_application) thay vì trước đây chỉ log mà không làm gì.
from core.command_dispatcher import CommandDispatcher

# Thiết lập ghi log hệ thống
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ClientAppMain")


class AgentApplication:
    """
    Class quản lý vòng đời và kết nối các thành phần của Agent.
    """
    def __init__(self):
        logger.info("=" * 60)
        logger.info("   KHỞI ĐỘNG REMOTE ADMINISTRATION AGENT (CLIENT APP)")
        logger.info("=" * 60)
        logger.info(f"Client ID   : {settings.CLIENT_ID}")
        logger.info(f"Hostname    : {settings.HOSTNAME}")
        logger.info(f"IP LAN      : {settings.IP_ADDRESS}")
        logger.info(f"OS Info     : {settings.OS_INFO}")
        logger.info(f"Gateway URL : {settings.GATEWAY_WS_URL}")
        logger.info(f"Sandbox Dir : {settings.SANDBOX_DIR}")
        logger.info("=" * 60)

        # 1. Khởi tạo PyQt6 Application
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Cho phép Agent chạy ngầm ở Khay hệ thống (System Tray)

    def run(self):
        """
        Khởi chạy vòng lặp sự kiện chính của PyQt6.
        """
        logger.info("Agent đang khởi chạy và lắng nghe sự kiện...")
        
        # Khởi tạo và hiển thị cửa sổ chính (luôn nổi trên cùng)
        self.main_window = MainWindow()
        self.main_window.show()

        # Khởi chạy GatewayService chạy trên một QThread riêng
        # để quản lý kết nối WebSocket với Gateway Server (Online/Offline).
        self.gateway_service = GatewayService()
        self.gateway_service.connected_signal.connect(
            lambda: self.main_window.update_connection_status(True)
        )
        self.gateway_service.disconnected_signal.connect(
            lambda: self.main_window.update_connection_status(False)
        )
        self.gateway_service.metrics_signal.connect(self.main_window.update_metrics)
        self.gateway_service.message_received_signal.connect(self._handle_gateway_message)
        self.gateway_service.start()

        # Khởi tạo Command Dispatcher để xử lý các lệnh điều khiển từ WebAdmin
        self.command_dispatcher = CommandDispatcher(self.gateway_service, self.main_window)

        # Chạy Event Loop chính của PyQt6
        exit_code = self.app.exec()

        # Dọn dẹp Thread mạng trước khi thoát ứng dụng
        self.gateway_service.stop()
        self.gateway_service.wait(3000)
        sys.exit(exit_code)

    def _handle_gateway_message(self, message: dict):
        """
        Xử lý các gói tin Gateway gửi tới:
          - Ghi log công khai cho End User theo dõi.
          - 👉 QUAN TRỌNG: Chuyển lệnh cho CommandDispatcher thực thi
            (trước đây chỉ log, nên lệnh "Khởi chạy App" bị nuốt lặng im).
        """
        msg_type = message.get("type", "unknown")
        logger.info(f"[GATEWAY MESSAGE] type='{msg_type}'")
        self.main_window.append_log(f"Nhận tin từ Gateway: {msg_type}")

        # Bàn giao cho CommandDispatcher phân loại & thực thi lệnh
        self.command_dispatcher.dispatch(message)


if __name__ == "__main__":
    try:
        agent = AgentApplication()
        agent.run()
    except KeyboardInterrupt:
        logger.info("Người dùng đóng ứng dụng bằng Ctrl+C.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Lỗi không xác định khi khởi chạy Agent: {e}", exc_info=True)
        sys.exit(1)