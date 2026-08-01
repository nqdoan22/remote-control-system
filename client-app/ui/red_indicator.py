"""
===============================================================================
FILE: client-app/ui/red_indicator.py
PURPOSE: Đèn báo đỏ nhấp nháy trên màn hình khi các tính năng nhạy cảm (Webcam, 
         Live Screen) đang được bật và truyền dữ liệu đi.
ARCHITECTURE ROLE:
  - Hiện thực hóa tính "Minh bạch tuyệt đối" (Transparency) của triết lý Privacy-First.
  - Cửa sổ chạy đè lên góc trên cùng màn hình (Always-on-Top, Floating Overlay).
  - Sử dụng cơ chế Click-Through (cho phép chuột bấm xuyên qua) để không gây 
    phiền nhiễu cho End User khi đang làm việc.
===============================================================================
"""

import logging
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush

# Import cấu hình ứng dụng
from config import settings

logger = logging.getLogger("RedIndicator")


class RedIndicatorWidget(QWidget):
    """
    Widget hiển thị đèn đỏ nhấp nháy ở góc trên bên phải màn hình.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_active = False
        self.dot_visible = True  # Trạng thái ẩn/hiện của chấm đỏ để tạo hiệu ứng nhấp nháy

        # 1. Cấu hình các thuộc tính cửa sổ đặc biệt (Floating Overlay)
        self._setup_window_flags()

        # 2. Dựng giao diện
        self._init_ui()

        # 3. Tạo Timer cho hiệu ứng nhấp nháy (Blink animation)
        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(500)  # Đổi trạng thái mỗi 0.5 giây (500ms)
        self.blink_timer.timeout.connect(self._toggle_blink)

        # Mặc định ẩn Widget khi khởi chạy
        self.hide()

    def _setup_window_flags(self):
        """
        Khởi tạo các Cờ cửa sổ (Window Flags) đặc biệt để làm Widget nổi:
        - WindowStaysOnTopHint: Luôn nằm đè lên mọi ứng dụng khác.
        - FramelessWindowHint: Không có thanh tiêu đề, khung viền Windows.
        - Tool: Không tạo biểu tượng icon ở thanh Taskbar dưới đáy màn hình.
        - WindowTransparentForInput: CHUỘT BẤM XUYÊN QUA (Click-Through) - Rất quan trọng!
        """
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        
        # Cho phép nền Widget có độ trong suốt (Alpha Channel)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

    def _init_ui(self):
        """Thiết lập bố cục và nhãn hiển thị thông báo."""
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Chấm tròn màu đỏ (được vẽ bằng CSS)
        self.dot_label = QLabel("🔴")
        self.dot_label.setStyleSheet("font-size: 14px;")

        # Dòng chữ cảnh báo minh bạch cho End User
        self.text_label = QLabel("WEBCAM / SCREEN IS ACTIVE")
        font = QFont("Consolas", 10, QFont.Weight.Bold)
        self.text_label.setFont(font)
        self.text_label.setStyleSheet("color: #FFFFFF;")

        layout.addWidget(self.dot_label)
        layout.addWidget(self.text_label)
        self.setLayout(layout)

        # Đặt màu nền hộp thông báo: Đen mờ bo góc (Dark Semi-transparent Badge)
        self.setStyleSheet("""
            RedIndicatorWidget {
                background-color: rgba(20, 20, 20, 210);
                border: 1px solid rgba(255, 0, 0, 180);
                border-radius: 6px;
            }
        """)

        self.adjustSize()
        self._position_top_right()

    def _position_top_right(self):
        """Tính toán vị trí để ghim Widget ở góc trên bên phải màn hình chính."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            # Cách mép phải 20px, cách mép trên 20px
            x = screen_geometry.width() - self.width() - 20
            y = 20
            self.move(x, y)

    def _toggle_blink(self):
        """Đổi trạng thái hiển thị của chấm đỏ để tạo hiệu ứng nhấp nháy cảnh báo."""
        self.dot_visible = not self.dot_visible
        if self.dot_visible:
            self.dot_label.setText("🔴")
        else:
            self.dot_label.setText("⚫")

    # =========================================================================
    # PUBLIC METHODS (Hàm điều khiển từ bên ngoài)
    # =========================================================================
    def start_indicator(self, reason: str = "WEBCAM ACTIVE"):
        """
        Bật đèn đỏ nhấp nháy trên màn hình.
        Args:
            reason (str): Lý do bật (VD: 'WEBCAM ACTIVE', 'LIVE SCREEN ACTIVE')
        """
        if not settings.RED_INDICATOR_ENABLED:
            logger.info("Tính năng Red Indicator bị tắt trong file config.py.")
            return

        self.text_label.setText(reason.upper())
        self.adjustSize()
        self._position_top_right()

        self.is_active = True
        self.show()
        self.blink_timer.start()
        logger.info(f"🔴 [RED INDICATOR] Đã BẬT đèn cảnh báo: '{reason}'")

    def stop_indicator(self):
        """Tắt đèn cảnh báo và ẩn Widget."""
        self.is_active = False
        self.blink_timer.stop()
        self.hide()
        logger.info("⚪ [RED INDICATOR] Đã TẮT đèn cảnh báo.")