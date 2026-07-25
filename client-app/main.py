# client-app/main.py
import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import AgentMainWindow
from core.gateway_service import GatewayServiceThread

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [AGENT] - %(levelname)s - %(message)s")
logger = logging.getLogger("Main")

def handle_incoming_command(command_data: dict):
    """
    Hàm xử lý lệnh điều khiển tạm thời. 
    Sau này sẽ kết nối trực tiếp với các module trong thư mục modules/.
    """
    cmd_type = command_data.get("type")
    logger.info(f"🛠️ Đang xử lý lệnh nhận được: {cmd_type}")
    # TODO: Tích hợp logic xử lý 8 module ở đây (Gọi Process, Webcam, Power...)

def main():
    # 1. Khởi tạo Application PyQt6
    app = QApplication(sys.argv)

    # 2. Khởi tạo cửa sổ chính
    main_window = AgentMainWindow()
    main_window.show()

    # 3. Khởi tạo luồng mạng (Gateway Service)
    gateway_thread = GatewayServiceThread()
    
    # Kết nối tín hiệu (Signals) từ luồng mạng sang UI và logic xử lý
    gateway_thread.connection_changed.connect(main_window.update_connection_status)
    gateway_thread.command_received.connect(handle_incoming_command)
    
    # Bắt đầu chạy luồng mạng
    gateway_thread.start()

    # 4. Chạy vòng lặp sự kiện của PyQt6 (Giữ ứng dụng không bị tắt)
    exit_code = app.exec()

    # 5. Dọn dẹp tài nguyên khi tắt app
    gateway_thread.stop()
    gateway_thread.wait()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()