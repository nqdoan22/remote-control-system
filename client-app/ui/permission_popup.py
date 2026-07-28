# client-app/ui/permission_popup.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                             QPushButton, QHBoxLayout, QProgressBar)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

class PermissionPopup(QDialog):
    """
    Cửa sổ Dialog hiển thị yêu cầu cấp quyền thực thi từ Admin.
    Sử dụng PyQt6 để vẽ giao diện trực quan.
    """
    def __init__(self, action_name: str, parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self.time_left = 15  # Đếm ngược 15 giây
        
        self.init_ui()
        
        # Thiết lập Timer đếm ngược mỗi 1 giây (1000 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def init_ui(self):
        """Vẽ các thành phần giao diện (Nút bấm, chữ, thanh tiến trình)"""
        self.setWindowTitle("Yeu cau quyen truy cap")
        self.setFixedSize(350, 150)
        # Ép cửa sổ luôn nổi trên cùng để người dùng không bỏ lỡ
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout()

        # Thông báo chính
        lbl_msg = QLabel(f"Quản trị viên đang yêu cầu thực thi lệnh:\n<b>{self.action_name}</b>")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setFont(QFont("Arial", 10))
        layout.addWidget(lbl_msg)

        # Thanh tiến trình thể hiện thời gian đếm ngược (0 - 15)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(15)
        self.progress_bar.setValue(self.time_left)
        layout.addWidget(self.progress_bar)

        # Cụm nút bấm Accept / Reject
        btn_layout = QHBoxLayout()
        
        self.btn_accept = QPushButton("Cho phép (Accept)")
        self.btn_accept.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.btn_accept.clicked.connect(self.accept_action)
        
        self.btn_reject = QPushButton("Từ chối (Reject)")
        self.btn_reject.setStyleSheet("background-color: #F44336; color: white; font-weight: bold; padding: 5px;")
        self.btn_reject.clicked.connect(self.reject_action)

        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_reject)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def update_timer(self):
        """Hàm gọi mỗi giây để giảm thời gian đếm ngược."""
        self.time_left -= 1
        self.progress_bar.setValue(self.time_left)
        
        # Nếu hết giờ mà chưa bấm gì -> Tự động kích hoạt hành động Từ chối
        if self.time_left <= 0:
            self.timer.stop()
            self.reject() # Trả về False (QDialog.DialogCode.Rejected)

    def accept_action(self):
        """Người dùng bấm nút Cho phép"""
        self.timer.stop()
        self.accept() # Trả về True (QDialog.DialogCode.Accepted)

    def reject_action(self):
        """Người dùng bấm nút Từ chối"""
        self.timer.stop()
        self.reject() # Trả về False