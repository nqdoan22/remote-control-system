# client-app/ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class AgentMainWindow(QMainWindow):
    """Cửa sổ giao diện chính của Agent."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Client Agent - Remote Control System")
        self.setFixedSize(400, 200)

        # Widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tiêu đề Đồ án
        self.lbl_title = QLabel("HỆ THỐNG ĐIỀU KHIỂN TỪ XA\n(Đồ án Mạng Máy Tính - HCMUS)")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_title)

        # Label hiển thị trạng thái
        self.lbl_status = QLabel("Trạng thái: Đang khởi động...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setFont(QFont("Arial", 11))
        self.lbl_status.setStyleSheet("color: orange;")
        layout.addWidget(self.lbl_status)

        # Ghi chú minh bạch
        lbl_note = QLabel("Ứng dụng này đang chạy ngầm để nhận lệnh điều khiển.")
        lbl_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_note.setFont(QFont("Arial", 9, italic=True))
        layout.addWidget(lbl_note)

        central_widget.setLayout(layout)

    def update_connection_status(self, is_connected: bool):
        """Hàm được gọi bởi GatewayServiceThread khi trạng thái mạng thay đổi."""
        if is_connected:
            self.lbl_status.setText("🟢 Trạng thái: ĐÃ KẾT NỐI (Online)")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.lbl_status.setText("🔴 Trạng thái: MẤT KẾT NỐI (Offline)")
            self.lbl_status.setStyleSheet("color: red; font-weight: bold;")