"""
===============================================================================
FILE: client-app/ui/main_window.py
PURPOSE: Giao diện Bảng điều khiển chính (Main Dashboard) của Client App.
ARCHITECTURE ROLE:
  - Cung cấp giao diện minh bạch cho End User theo dõi trạng thái kết nối Gateway.
  - Hiển thị chỉ số tài nguyên hệ thống thời gian thực (CPU, RAM).
  - Ghi vết Nhật ký hoạt động (Activity Logs) công khai khi có lệnh thực thi.
  - Tích hợp Khay hệ thống (System Tray Icon) giúp ứng dụng chạy ngầm gọn gàng.
===============================================================================
"""

import os
import sys
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QProgressBar, QFrame, QSystemTrayIcon, 
    QMenu, QApplication, QStyle
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QFont, QIcon, QAction, QCloseEvent

# Import cấu hình ứng dụng
from config import settings

logger = logging.getLogger("MainWindow")


class MainWindow(QMainWindow):
    """
    Cửa sổ chính của ứng dụng Client App (Agent Dashboard).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_force_quit = False  # Cờ đánh dấu khi người dùng chọn "Thoát" từ System Tray

        # 1. Cấu hình cửa sổ chính (luôn nằm trên cùng)
        self.setWindowTitle(f"Remote Administration Agent - [{settings.CLIENT_ID}]")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(600, 480)
        self.resize(650, 520)

        # 2. Xây dựng giao diện
        self._init_ui()

        # 3. Khởi tạo Khay hệ thống (System Tray Icon)
        self._setup_system_tray()

    def _init_ui(self):
        """Khởi tạo toàn bộ các thành phần giao diện trên Main Window."""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ---------------------------------------------------------------------
        # 1. HEADER: Thông tin định danh & Trạng thái kết nối Gateway
        # ---------------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)

        # Cột trái: Tên máy & IP LAN
        info_layout = QVBoxLayout()
        title_label = QLabel(f"🖥️ Machine: <b>{settings.HOSTNAME}</b> ({settings.IP_ADDRESS})")
        title_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        
        id_label = QLabel(f"Client ID: <font color='#aaaaaa'>{settings.CLIENT_ID}</font>")
        id_label.setStyleSheet("font-size: 11px;")

        info_layout.addWidget(title_label)
        info_layout.addWidget(id_label)

        # Cột phải: Badge trạng thái kết nối WebSocket
        self.status_badge = QLabel("🔴 OFFLINE")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet("""
            QLabel {
                background-color: #d9534f;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                padding: 6px 14px;
                font-size: 11px;
            }
        """)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)
        main_layout.addWidget(header_frame)

        # ---------------------------------------------------------------------
        # 2. METRICS: Chỉ số tài nguyên CPU & RAM
        # ---------------------------------------------------------------------
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 8px;")
        metrics_layout = QHBoxLayout(metrics_frame)

        # CPU Usage Bar
        cpu_box = QVBoxLayout()
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #495057;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setValue(0)
        self.cpu_bar.setFixedHeight(8)
        self.cpu_bar.setTextVisible(False)
        cpu_box.addWidget(self.cpu_label)
        cpu_box.addWidget(self.cpu_bar)

        # RAM Usage Bar
        ram_box = QVBoxLayout()
        self.ram_label = QLabel("RAM: 0%")
        self.ram_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #495057;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setValue(0)
        self.ram_bar.setFixedHeight(8)
        self.ram_bar.setTextVisible(False)
        ram_box.addWidget(self.ram_label)
        ram_box.addWidget(self.ram_bar)

        metrics_layout.addLayout(cpu_box)
        metrics_layout.addLayout(ram_box)
        main_layout.addWidget(metrics_frame)

        # ---------------------------------------------------------------------
        # 3. LOG CONSOLE: Khung hiển thị Nhật ký Hoạt động (Activity Logs)
        # ---------------------------------------------------------------------
        log_header = QLabel("📋 Nhật Ký Hoạt Động (Privacy Activity Logs):")
        log_header.setStyleSheet("font-weight: bold; font-size: 12px; color: #333333;")
        main_layout.addWidget(log_header)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        main_layout.addWidget(self.log_console)

        # ---------------------------------------------------------------------
        # 4. FOOTER: Các nút chức năng tiện ích
        # ---------------------------------------------------------------------
        footer_layout = QHBoxLayout()

        self.btn_open_sandbox = QPushButton("📁 Mở Thư Mục Sandbox")
        self.btn_open_sandbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_sandbox.clicked.connect(self._open_sandbox_folder)

        self.btn_hide_tray = QPushButton("📥 Thu Nhỏ Về Tray")
        self.btn_hide_tray.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hide_tray.clicked.connect(self.hide)

        footer_layout.addWidget(self.btn_open_sandbox)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_hide_tray)
        main_layout.addLayout(footer_layout)

        self.setCentralWidget(central_widget)

    def _setup_system_tray(self):
        """Khởi tạo biểu tượng ứng dụng ở Khay hệ thống góc dưới màn hình."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Dùng icon tiêu chuẩn từ hệ điều hành PyQt6
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip(f"Remote Agent - {settings.CLIENT_ID}")

        # Menu chuột phải ở Khay hệ thống
        tray_menu = QMenu()
        
        show_action = QAction("🖥️ Mở Bảng Điều Khiển", self)
        show_action.triggered.connect(self.showNormal)
        
        sandbox_action = QAction("📁 Mở Thư Mục Sandbox", self)
        sandbox_action.triggered.connect(self._open_sandbox_folder)

        quit_action = QAction("❌ Thoát Cho Ứng Dụng", self)
        quit_action.triggered.connect(self._force_quit)

        tray_menu.addAction(show_action)
        tray_menu.addAction(sandbox_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()

    def closeEvent(self, event: QCloseEvent):
        """
        Ghi đè sự kiện bấm nút [X] góc trên cửa sổ:
        Thay vì thoát app, ứng dụng sẽ thu nhỏ xuống Khay hệ thống (System Tray).
        """
        if self.is_force_quit:
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Remote Administration Agent",
                "Ứng dụng vẫn đang chạy ngầm ở Khay hệ thống để duy trì kết nối.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

    def _open_sandbox_folder(self):
        """Mở thư mục C:/AgentSandbox bằng Explorer của Windows."""
        os.makedirs(settings.SANDBOX_DIR, exist_ok=True)
        os.startfile(settings.SANDBOX_DIR)

    def _force_quit(self):
        """Thoát ứng dụng hoàn toàn từ Menu Khay hệ thống."""
        self.is_force_quit = True
        QApplication.quit()

    # =========================================================================
    # PUBLIC SLOTS (Các hàm nhận tín hiệu Signal từ Core Services gửi sang)
    # =========================================================================
    @pyqtSlot(bool)
    def update_connection_status(self, is_connected: bool):
        """Cập nhật trạng thái Badge kết nối WebSocket trên UI."""
        if is_connected:
            self.status_badge.setText("🟢 ONLINE")
            self.status_badge.setStyleSheet("""
                QLabel {
                    background-color: #5cb85c; color: white;
                    font-weight: bold; border-radius: 12px;
                    padding: 6px 14px; font-size: 11px;
                }
            """)
            self.append_log("✅ Đã kết nối thành công tới Gateway Server.")
        else:
            self.status_badge.setText("🔴 OFFLINE")
            self.status_badge.setStyleSheet("""
                QLabel {
                    background-color: #d9534f; color: white;
                    font-weight: bold; border-radius: 12px;
                    padding: 6px 14px; font-size: 11px;
                }
            """)
            self.append_log("⚠️ Mất kết nối tới Gateway! Đang thử kết nối lại...")

    @pyqtSlot(float, float)
    def update_metrics(self, cpu: float, ram: float):
        """Cập nhật thanh tiến trình CPU/RAM thời gian thực."""
        self.cpu_label.setText(f"CPU: {cpu:.1f}%")
        self.cpu_bar.setValue(int(cpu))
        
        self.ram_label.setText(f"RAM: {ram:.1f}%")
        self.ram_bar.setValue(int(ram))

    @pyqtSlot(str)
    def append_log(self, text: str):
        """Thêm dòng nhật ký hoạt động vào ô Log Console trên giao diện."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {text}"
        self.log_console.append(log_entry)
        logger.info(text)