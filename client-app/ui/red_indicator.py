# client-app/ui/red_indicator.py
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

class RedIndicatorOverlay(QWidget):
    """
    Lớp tạo khung viền đỏ nhấp nháy bao quanh màn hình máy tính.
    Kích hoạt khi các module nhạy cảm (Webcam / Live Screen) đang bật.
    """
    def __init__(self):
        super().__init__()
        self.is_visible_state = False
        self.init_ui()
        
        # Timer để tạo hiệu ứng nhấp nháy viền (500ms = 0.5 giây)
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_visibility)

    def init_ui(self):
        """Cấu hình cửa sổ vô hình, xuyên thấu chuột."""
        # Bỏ thanh tiêu đề, luôn nằm trên cùng, xuyên thấu (click xuyên qua)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        # Đặt nền cửa sổ trong suốt 100%
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Phóng to cửa sổ ra toàn bộ kích thước màn hình
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

    def toggle_visibility(self):
        """Thay đổi trạng thái để tạo hiệu ứng chớp tắt."""
        self.is_visible_state = not self.is_visible_state
        self.update() # Lệnh này yêu cầu PyQt6 gọi lại hàm paintEvent() bên dưới

    def paintEvent(self, event):
        """Sự kiện vẽ đồ họa: Vẽ viền đỏ dày 10 pixel quanh màn hình."""
        if self.is_visible_state:
            painter = QPainter(self)
            # Khử răng cưa cho nét vẽ mượt hơn
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Cấu hình bút vẽ: Màu đỏ (Red), độ dày 10px
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(10)
            painter.setPen(pen)
            
            # Vẽ hình chữ nhật ôm sát viền (trừ đi 5px mỗi cạnh để không bị lẹm)
            rect = self.rect()
            painter.drawRect(
                rect.x() + 5, 
                rect.y() + 5, 
                rect.width() - 10, 
                rect.height() - 10
            )

    def start_blinking(self):
        """Bật viền đỏ nhấp nháy."""
        self.show()
        self.is_visible_state = True
        self.blink_timer.start(500)

    def stop_blinking(self):
        """Tắt hoàn toàn viền đỏ cảnh báo."""
        self.blink_timer.stop()
        self.hide()