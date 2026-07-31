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
        
        # TODO: Trong các bước tiếp theo, chúng ta sẽ kết nối GatewayService
        # và PermissionManager tại đây qua cơ chế Signal/Slot của PyQt6.
        
        # Chạy Event Loop chính của PyQt6
        sys.exit(self.app.exec())


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