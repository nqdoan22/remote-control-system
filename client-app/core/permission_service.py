# client-app/core/permission_service.py
import json
import os
import logging
from config import config

logger = logging.getLogger("PermissionService")

class PermissionManager:
    """
    Lớp quản lý trạng thái phân quyền của các module.
    Dữ liệu được lưu trữ xuống file permissions.json để ghi nhớ cho các lần chạy sau.
    """
    def __init__(self):
        # Đường dẫn tới file lưu trữ cấu hình phân quyền (đặt trong thư mục Sandbox)
        self.config_file = os.path.join(config.SANDBOX_DIR, "permissions.json")
        
        # Các hằng số trạng thái phân quyền
        self.STATE_ASK = "ASK"       # Luôn hiển thị Popup hỏi ý kiến người dùng
        self.STATE_ALLOW = "ALLOW"   # Luôn cho phép (Không cần hỏi)
        self.STATE_DENY = "DENY"     # Luôn từ chối (Chặn ngay lập tức)
        
        # Cấu hình mặc định cho 8 module cốt lõi: Ban đầu tất cả đều là ASK (Phải hỏi)
        self.default_permissions = {
            "processes": self.STATE_ASK,
            "applications": self.STATE_ASK,
            "screenshot": self.STATE_ASK,
            "live_screen": self.STATE_ASK,
            "keylogger": self.STATE_ASK,
            "file_manager": self.STATE_ASK,
            "webcam": self.STATE_ASK,
            "power_control": self.STATE_ASK
        }
        
        # Tải cấu hình từ file lên bộ nhớ RAM khi khởi động
        self.permissions = self.load_permissions()

    def load_permissions(self) -> dict:
        """Đọc file cấu hình. Nếu chưa có file thì tạo mới với cấu hình mặc định."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Gộp dữ liệu đọc được với cấu hình mặc định (phòng trường hợp thiếu key)
                    return {**self.default_permissions, **data}
            except Exception as e:
                logger.error(f"Loi doc file permissions: {e}. Dung cau hinh mac dinh.")
                return self.default_permissions
        else:
            self.save_permissions(self.default_permissions)
            return self.default_permissions

    def save_permissions(self, perms: dict):
        """Lưu toàn bộ cấu hình phân quyền xuống file JSON."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(perms, f, indent=4)
            self.permissions = perms
            logger.info("Da luu cau hinh phan quyen thanh cong.")
        except Exception as e:
            logger.error(f"Loi ghi file permissions: {e}")

    def get_permission(self, module_name: str) -> str:
        """Lấy trạng thái cấp quyền hiện tại của một module cụ thể."""
        # Trích xuất tên module từ chuỗi action (VD: từ 'webcam.start' lấy chữ 'webcam')
        base_module = module_name.split('.')[0]
        return self.permissions.get(base_module, self.STATE_ASK)

# Khởi tạo một thực thể duy nhất (Singleton) dùng chung cho toàn hệ thống
permission_manager = PermissionManager()