"""
===============================================================================
FILE: client-app/modules/screenshot.py
PURPOSE: Chụp ảnh màn hình máy tính Client, nén JPEG và mã hóa Base64.
ARCHITECTURE ROLE:
  - Direct Execution Module - Trả về dữ liệu ảnh tĩnh dạng Base64.
  - Sử dụng `mss` tối ưu hiệu năng + `Pillow` nén chất lượng theo config.py.
  - Xử lý hoàn toàn trên RAM (BytesIO), không ghi file tạm xuống ổ cứng.
===============================================================================
"""

import base64
import io
import logging
from typing import Dict, Any, Optional
import mss
from PIL import Image

# Import cấu hình để lấy thông số JPEG_QUALITY
from config import settings

logger = logging.getLogger("ScreenshotModule")


def take_screenshot(monitor_index: int = 0) -> Dict[str, Any]:
    """
    Chụp ảnh màn hình máy Client và nén thành chuỗi mã hóa Base64 JPEG.
    
    Args:
        monitor_index (int): 0 là chụp toàn bộ màn hình (gộp các màn), 
                             1, 2... là chụp màn hình đơn tương ứng.
                             
    Returns:
        Dict[str, Any]: {
            "success": bool,
            "image_base64": str (Chuỗi Base64 ảnh JPEG),
            "width": int,
            "height": int,
            "message": str
        }
    """
    try:
        with mss.mss() as sct:
            # Kiểm tra chỉ số màn hình hợp lệ
            if monitor_index < 0 or monitor_index >= len(sct.monitors):
                monitor_index = 0  # Mặc định lấy monitor tổng nếu index vượt giới hạn

            monitor = sct.monitors[monitor_index]
            sct_img = sct.grab(monitor)

            # Chuyển đổi dữ liệu raw pixels từ mss sang Pillow Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # Lưu ảnh vào bộ nhớ tạm RAM (BytesIO) với nén JPEG
            buffer = io.BytesIO()
            img.save(
                buffer, 
                format="JPEG", 
                quality=settings.JPEG_QUALITY, 
                optimize=True
            )
            buffer.seek(0)

            # Mã hóa Bytes sang dạng chuỗi Base64 ASCII
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            logger.info(
                f"📸 Đã chụp màn hình [{monitor_index}] ({img.width}x{img.height}) | "
                f"Chất lượng JPEG: {settings.JPEG_QUALITY}% | Dung lượng: {len(img_base64) // 1024} KB"
            )

            return {
                "success": True,
                "image_base64": img_base64,
                "width": img.width,
                "height": img.height,
                "message": "Chụp màn hình thành công."
            }

    except Exception as e:
        err_msg = f"Lỗi khi chụp màn hình: {str(e)}"
        logger.error(f"❌ {err_msg}")
        return {
            "success": False,
            "image_base64": "",
            "width": 0,
            "height": 0,
            "message": err_msg
        }


# =============================================================================
# BLOCK TEST ĐỘC LẬP
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- TEST MODULE SCREENSHOT ---")
    
    result = take_screenshot(0)
    if result["success"]:
        print(f"✅ Thành công! Kích thước: {result['width']}x{result['height']}")
        print(f"Độ dài chuỗi Base64: {len(result['image_base64'])} chars")
        print(f"Ví dụ 50 ký tự đầu Base64: {result['image_base64'][:50]}...")
    else:
        print(f"❌ Thất bại: {result['message']}")