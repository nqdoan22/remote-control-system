"""
===============================================================================
FILE: client-app/modules/file_manager.py
PURPOSE: Quản lý Duyệt, Tải lên, Tải về và Xóa File trong phạm vi Sandbox an toàn.
ARCHITECTURE ROLE:
  - Thực thi các thao tác File I/O tuân thủ chính sách Bảo mật (Sandbox Isolation).
  - Tự động Sanitize Path ngăn chặn tấn công Directory Traversal (../../).
  - Mọi thao tác bị chặn tuyệt đối nếu ra khỏi settings.SANDBOX_DIR.
===============================================================================
"""

import base64
import logging
import os
from pathlib import Path
import shutil
from typing import List, Dict, Any, Optional

# Import cấu hình lấy SANDBOX_DIR
from config import settings

logger = logging.getLogger("FileManagerModule")


def _sanitize_path(relative_or_subpath: str) -> Path:
    """
    Hàm bổ trợ kiểm tra và quy đổi đường dẫn an toàn trong Sandbox.
    
    Raises:
        PermissionError: Nếu đường dẫn vượt ra khỏi thư mục SANDBOX_DIR.
    """
    # Loại bỏ ký tự phân cách thừa ở đầu đường dẫn
    clean_subpath = relative_or_subpath.lstrip("/\\")
    
    # Tạo đường dẫn tuyệt đối đầy đủ và phân giải các ký tự '..' nếu có
    target_path = (settings.SANDBOX_DIR / clean_subpath).resolve()
    sandbox_root = settings.SANDBOX_DIR.resolve()

    # Kiểm tra đường dẫn đích có nằm trong Sandbox hay không
    try:
        # Trong Python 3.9+, is_relative_to dùng để kiểm tra cha-con an toàn
        if not target_path.is_relative_to(sandbox_root):
            raise PermissionError("Thao tác bị từ chối! Đường dẫn nằm ngoài phạm vi Sandbox.")
    except AttributeError:
        # Dành cho Python bản cũ hơn nếu không có is_relative_to
        if not str(target_path).startswith(str(sandbox_root)):
            raise PermissionError("Thao tác bị từ chối! Đường dẫn nằm ngoài phạm vi Sandbox.")

    return target_path


def list_directory(subpath: str = "") -> Dict[str, Any]:
    """
    Xem danh sách File và Folder trong một thư mục con của Sandbox.
    """
    try:
        target_dir = _sanitize_path(subpath)

        if not target_dir.exists():
            return {"success": False, "code": "FILE_NOT_FOUND", "message": f"Thư mục không tồn tại: {subpath}", "items": []}

        if not target_dir.is_dir():
            return {"success": False, "code": "INVALID_PATH", "message": f"Đường dẫn không phải là thư mục: {subpath}", "items": []}

        items: List[Dict[str, Any]] = []
        for entry in target_dir.iterdir():
            try:
                stats = entry.stat()
                items.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size_bytes": stats.st_size if entry.is_file() else 0,
                    "modified_time": int(stats.st_mtime)
                })
            except Exception:
                continue

        logger.info(f"📂 Đã liệt kê {len(items)} mục trong Sandbox: '/{subpath}'")
        return {
            "success": True,
            "message": "Lấy danh sách file thành công.",
            "current_path": str(target_dir.relative_to(settings.SANDBOX_DIR.resolve())),
            "items": items
        }

    except PermissionError as pe:
        logger.warning(f"🛡️ [SECURITY BREACH ATTEMPT] {str(pe)}")
        return {"success": False, "code": "INVALID_PATH", "message": str(pe), "items": []}
    except Exception as e:
        logger.error(f"❌ Lỗi duyệt thư mục: {str(e)}")
        return {"success": False, "code": "INTERNAL_ERROR", "message": f"Lỗi hệ thống: {str(e)}", "items": []}


# Giới hạn kích thước file tải lên/xuống qua WebSocket theo docs/api_contract.md
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def download_file(subpath: str) -> Dict[str, Any]:
    """
    Đọc file từ Sandbox và trả về dữ liệu mã hóa Base64 cho Admin tải về.
    """
    try:
        target_file = _sanitize_path(subpath)

        if not target_file.exists() or not target_file.is_file():
            return {"success": False, "code": "FILE_NOT_FOUND", "message": "File không tồn tại hoặc là thư mục.", "file_data_base64": ""}

        if target_file.stat().st_size > MAX_FILE_SIZE:
            return {"success": False, "code": "FILE_TOO_LARGE", "message": "File vượt quá dung lượng cho phép (Max 50MB).", "file_data_base64": ""}

        with open(target_file, "rb") as f:
            encoded_bytes = base64.b64encode(f.read())
            base64_str = encoded_bytes.decode("utf-8")

        logger.info(f"📥 Đã xuất file từ Sandbox: '{subpath}' ({target_file.stat().st_size} bytes)")
        return {
            "success": True,
            "message": f"Tải file '{target_file.name}' thành công.",
            "file_name": target_file.name,
            "file_data_base64": base64_str
        }

    except PermissionError as pe:
        return {"success": False, "code": "INVALID_PATH", "message": str(pe), "file_data_base64": ""}
    except Exception as e:
        return {"success": False, "code": "INTERNAL_ERROR", "message": f"Lỗi đọc file: {str(e)}", "file_data_base64": ""}


def upload_file(subpath: str, file_data_base64: str) -> Dict[str, Any]:
    """
    Giải mã chuỗi Base64 từ Admin và lưu thành file vào Sandbox.
    """
    try:
        target_file = _sanitize_path(subpath)

        file_bytes = base64.b64decode(file_data_base64)
        if len(file_bytes) > MAX_FILE_SIZE:
            return {"success": False, "code": "FILE_TOO_LARGE", "message": "File vượt quá dung lượng cho phép (Max 50MB)."}

        # Tự động tạo các thư mục cha nếu chưa có
        target_file.parent.mkdir(parents=True, exist_ok=True)

        with open(target_file, "wb") as f:
            f.write(file_bytes)

        logger.info(f"📤 Đã ghi file thành công vào Sandbox: '{subpath}' ({len(file_bytes)} bytes)")
        return {
            "success": True,
            "message": f"Đã tải lên thành công file '{target_file.name}'.",
            "saved_path": str(target_file),
        }

    except PermissionError as pe:
        return {"success": False, "code": "INVALID_PATH", "message": str(pe)}
    except Exception as e:
        return {"success": False, "code": "INTERNAL_ERROR", "message": f"Lỗi ghi file: {str(e)}"}


def delete_item(subpath: str) -> Dict[str, Any]:
    """
    Xóa File hoặc Thư mục trong Sandbox.
    """
    try:
        target_item = _sanitize_path(subpath)

        if not target_item.exists():
            return {"success": False, "code": "FILE_NOT_FOUND", "message": "Mục cần xóa không tồn tại."}

        if target_item.is_file():
            target_item.unlink()
        elif target_item.is_dir():
            shutil.rmtree(target_item)

        logger.info(f"🗑️ Đã xóa thành công mục trong Sandbox: '{subpath}'")
        return {"success": True, "message": f"Đã xóa thành công '{target_item.name}'."}

    except PermissionError as pe:
        return {"success": False, "code": "INVALID_PATH", "message": str(pe)}
    except Exception as e:
        return {"success": False, "code": "INTERNAL_ERROR", "message": f"Lỗi khi xóa: {str(e)}"}


# =============================================================================
# BLOCK TEST ĐỘC LẬP
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- TEST MODULE FILE MANAGER ---")
    print(f"Thư mục Sandbox hiện tại: {settings.SANDBOX_DIR.resolve()}")

    # 1. Test upload file thử nghiệm
    dummy_text_b64 = base64.b64encode(b"Hello World from Agent Sandbox!").decode("utf-8")
    up_res = upload_file("test_folder/hello.txt", dummy_text_b64)
    print(f"\n1. Test Upload: {up_res}")

    # 2. Test xem danh sách
    list_res = list_directory("test_folder")
    print(f"\n2. Test List Dir: {list_res}")

    # 3. Test thử tấn công Directory Traversal
    print("\n3. Test bảo mật - Thử truy cập C:\\Windows\\System32:")
    hack_res = list_directory("../../Windows/System32")
    print(f"Kết quả chặn: {hack_res}")