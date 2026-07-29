# client-app/modules/file_manager.py
import os
import shutil
import logging
from config import config

logger = logging.getLogger("Module-FileManager")

class FileManager:
    """Module quản lý File nhưng BỊ GIỚI HẠN chặt chẽ trong thư mục Sandbox."""
    
    def __init__(self):
        self.sandbox_dir = os.path.abspath(config.SANDBOX_DIR)
        
    def _is_safe_path(self, target_path: str) -> bool:
        """
        Kiểm tra bảo mật: Đường dẫn được yêu cầu CÓ NẰM TRONG thư mục Sandbox không?
        Ngăn chặn các thủ thuật Directory Traversal (VD: ../../../windows/system32).
        """
        # Chuyển đổi target_path thành đường dẫn tuyệt đối
        abs_target = os.path.abspath(os.path.join(self.sandbox_dir, target_path.lstrip("/\\")))
        # Kiểm tra xem đường dẫn đích có bắt đầu bằng thư mục gốc Sandbox không
        return abs_target.startswith(self.sandbox_dir)

    def _get_abs_path(self, target_path: str) -> str:
        """Lấy đường dẫn tuyệt đối an toàn."""
        return os.path.abspath(os.path.join(self.sandbox_dir, target_path.lstrip("/\\")))

    def list_dir(self, path: str = "") -> dict:
        """Liệt kê các thư mục và file trong đường dẫn (nằm trong Sandbox)."""
        if not self._is_safe_path(path):
            return {"success": False, "error": "Truy cập bị từ chối: Nằm ngoài Sandbox."}
            
        target = self._get_abs_path(path)
        if not os.path.exists(target):
            return {"success": False, "error": "Thư mục không tồn tại."}
            
        try:
            items = []
            for item in os.listdir(target):
                item_path = os.path.join(target, item)
                is_dir = os.path.isdir(item_path)
                items.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "sizeBytes": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                    "modifiedAt": int(os.path.getmtime(item_path)) if os.path.exists(item_path) else None
                })
            return {"success": True, "path": path, "entries": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_file(self, path: str) -> dict:
        """Đọc file trong Sandbox và trả về nội dung Base64."""
        if not self._is_safe_path(path):
            return {"success": False, "error": "Truy cập bị từ chối: Nằm ngoài Sandbox."}
        target = self._get_abs_path(path)
        if not os.path.exists(target) or not os.path.isfile(target):
            return {"success": False, "error": "File không tồn tại."}
        try:
            import base64, mimetypes
            with open(target, "rb") as f:
                content_b64 = base64.b64encode(f.read()).decode("utf-8")
            mime_type, _ = mimetypes.guess_type(target)
            return {
                "success": True,
                "filename": os.path.basename(target),
                "content": content_b64,
                "sizeBytes": os.path.getsize(target),
                "mimeType": mime_type or "application/octet-stream"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_file(self, destination_path: str, content_b64: str) -> dict:
        """Ghi file vào Sandbox từ nội dung Base64."""
        if not self._is_safe_path(destination_path):
            return {"success": False, "error": "Truy cập bị từ chối: Nằm ngoài Sandbox."}
        target = self._get_abs_path(destination_path)
        try:
            import base64
            os.makedirs(os.path.dirname(target), exist_ok=True)
            data = base64.b64decode(content_b64)
            with open(target, "wb") as f:
                f.write(data)
            return {
                "success": True,
                "savedPath": target,
                "message": f"Đã upload {os.path.basename(target)}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, path: str) -> dict:
        """Xóa file hoặc thư mục rỗng trong Sandbox."""
        if not self._is_safe_path(path):
            return {"success": False, "error": "Truy cập bị từ chối: Nằm ngoài Sandbox."}
            
        target = self._get_abs_path(path)
        if not os.path.exists(target):
            return {"success": False, "error": "File không tồn tại."}
            
        try:
            if os.path.isfile(target):
                os.remove(target)
            else:
                os.rmdir(target) # Chỉ xóa thư mục rỗng
            return {"success": True, "message": f"Đã xóa {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Khởi tạo instance dùng chung
file_manager = FileManager()