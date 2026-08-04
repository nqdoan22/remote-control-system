"""
===============================================================================
FILE: client-app/ui/permission_popup.py
PURPOSE: Giao diện Cửa sổ Popup xin quyền End User (Privacy-First UI).
ARCHITECTURE ROLE:
  - Hiển thị trực tiếp trên Main GUI Thread đè lên trên mọi cửa sổ (Always-on-Top).
  - Đếm ngược 15 giây đếm thời gian thực.
  - Nhận tương tác (Accept / Reject / Timeout) và gửi kết quả về PermissionService.
===============================================================================
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger("PermissionPopup")

# Bảng dịch tên Feature sang Tiếng Việt hiển thị cho End User dễ hiểu.
# Khóa PHẢI khớp đúng giá trị "feature" mà gateway/core/permission_manager.py
# tính ra (msg_type bỏ hậu tố ".start" nếu có — xem docs/api_contract.md,
# Sensitive Feature List).
FEATURE_NAMES_VN = {
    "screen.screenshot": "Chụp ảnh màn hình (Screenshot)",
    "screen.live": "Xem màn hình thời gian thực (Live Screen)",
    "webcam": "Bật Camera / Webcam",
    "keylogger": "Ghi bàn phím (Keylogger)",
    "power.lock": "Khóa màn hình (Lock Screen)",
    "power.restart": "Khởi động lại máy (Restart)",
    "power.shutdown": "Tắt máy (Shutdown)",
    "power.sleep": "Đưa máy vào chế độ Sleep",
}


class PermissionPopupDialog(QDialog):
    """
    Cửa sổ Dialog Popup xin quyền Always-on-Top.
    """

    def __init__(
        self, 
        permission_id: str, 
        feature: str, 
        requested_by: str, 
        timeout_seconds: int, 
        permission_service, 
        parent=None
    ):
        super().__init__(parent)
        
        self.permission_id = permission_id
        self.feature = feature
        self.requested_by = requested_by
        self.time_left = timeout_seconds
        self.total_timeout = timeout_seconds
        self.permission_service = permission_service

        # Cấu hình cửa sổ Popup
        self._setup_window_flags()
        self._init_ui()
        self._start_timer()

    def _setup_window_flags(self):
        """Thiết lập thuộc tính cửa sổ đè lên trên cùng và chặn nút Đóng X mặc định."""
        # WindowStaysOnTopHint: Luôn hiển thị trên cùng
        # CustomizeWindowHint | WindowTitleHint: Ẩn nút Min/Max/Close tiêu chuẩn
        # Window (base type): đảm bảo Dialog là cửa sổ độc lập (không phụ thuộc
        # vào parent) nên hiển thị được ngay cả khi MainWindow bị thu vào System Tray.
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.CustomizeWindowHint | 
            Qt.WindowType.WindowTitleHint
        )
        self.setWindowTitle("⚠️ YÊU CẦU XIN QUYỀN HỆ THỐNG")
        self.setFixedSize(450, 260)

    def _init_ui(self):
        """Dựng bố cục giao diện PyQt6."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # 1. Tiêu đề cảnh báo
        title_label = QLabel("🛡️ CẢNH BÁO BẢO MẬT & QUYỀN RIÊNG TƯ")
        title_font = QFont("Arial", 11, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #d9534f;")
        main_layout.addWidget(title_label)

        # 2. Nội dung chi tiết yêu cầu
        feature_vn = FEATURE_NAMES_VN.get(self.feature, self.feature)
        info_text = (
            f"Quản trị viên <b>{self.requested_by}</b> đang yêu cầu quyền:<br>"
            f"<span style='color: #0275d8; font-size: 13px;'><b>👉 {feature_vn}</b></span><br><br>"
            f"Bạn có đồng ý cấp quyền thực thi tác vụ này không?"
        )
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 12px; color: #333333;")
        main_layout.addWidget(info_label)

        # 3. Thanh đếm ngược Progress Bar (15s -> 0s)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.total_timeout * 10) # 10 ticks per second
        self.progress_bar.setValue(self.total_timeout * 10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                height: 8px;
                background-color: #e6e6e6;
            }
            QProgressBar::chunk {
                background-color: #f0ad4e;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Label hiển thị giây còn lại
        self.timer_label = QLabel(f"Tự động TỪ CHỐI sau: <b>{self.time_left}</b> giây")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #777777; font-size: 11px;")
        main_layout.addWidget(self.timer_label)

        # 4. Hàng nút nhấn: ACCEPT (Xanh) vs REJECT (Đỏ)
        button_layout = QHBoxLayout()
        
        self.btn_accept = QPushButton("✅ ĐỒNG Ý (ACCEPT)")
        self.btn_accept.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_accept.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c; color: white; 
                font-weight: bold; border-radius: 4px; padding: 10px;
            }
            QPushButton:hover { background-color: #4cae4c; }
        """)
        self.btn_accept.clicked.connect(self._on_accept)

        self.btn_reject = QPushButton("❌ TỪ CHỐI (REJECT)")
        self.btn_reject.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reject.setStyleSheet("""
            QPushButton {
                background-color: #d9534f; color: white; 
                font-weight: bold; border-radius: 4px; padding: 10px;
            }
            QPushButton:hover { background-color: #c9302c; }
        """)
        self.btn_reject.clicked.connect(self._on_reject)

        button_layout.addWidget(self.btn_accept)
        button_layout.addWidget(self.btn_reject)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _start_timer(self):
        """Khởi động QTimer cập nhật thanh thời gian mỗi 100ms."""
        self.ticks_left = self.total_timeout * 10
        self.timer = QTimer(self)
        self.timer.setInterval(100) # 100ms
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.start()

    def _on_timer_tick(self):
        """Hàm đếm tick thời gian."""
        self.ticks_left -= 1
        self.progress_bar.setValue(self.ticks_left)
        
        seconds_remaining = (self.ticks_left // 10) + 1
        self.timer_label.setText(f"Tự động TỪ CHỐI sau: <b>{seconds_remaining}</b> giây")

        if self.ticks_left <= 0:
            self.timer.stop()
            logger.warning(f"Popup timeout 15s cho permission_id [{self.permission_id}] -> Tự động REJECT")
            self._resolve_and_close(granted=False)

    def _on_accept(self):
        """Xử lý khi End User chủ động bấm Đồng ý."""
        self.timer.stop()
        logger.info(f"User bấm ACCEPT cho permission_id [{self.permission_id}]")
        self._resolve_and_close(granted=True)

    def _on_reject(self):
        """Xử lý khi End User chủ động bấm Từ chối."""
        self.timer.stop()
        logger.info(f"User bấm REJECT cho permission_id [{self.permission_id}]")
        self._resolve_and_close(granted=False)

    def _resolve_and_close(self, granted: bool):
        """Gửi kết quả về PermissionService và đóng cửa sổ Popup."""
        if self.permission_service:
            self.permission_service.handle_user_response(self.permission_id, granted)
        self.accept() if granted else self.reject()
        self.close()