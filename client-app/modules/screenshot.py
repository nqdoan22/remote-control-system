# client-app/modules/screenshot.py
import mss
import mss.tools
import base64
import logging

logger = logging.getLogger("Module-Screenshot")

class ScreenshotManager:
    """Module chụp ảnh màn hình hiện tại của người dùng."""
    
    @staticmethod
    def capture() -> dict:
        """
        Chụp màn hình chính (Monitor 1) và trả về chuỗi ảnh dạng Base64.
        Dạng Base64 giúp dễ dàng đóng gói vào JSON để gửi qua WebSocket.
        """
        try:
            with mss.mss() as sct:
                # Lấy màn hình chính (monitors[1] thường là màn hình chính)
                monitor = sct.monitors[1]
                
                # Chụp khung hình
                sct_img = sct.grab(monitor)
                
                # Chuyển đổi sang định dạng PNG thô trên RAM
                png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
                
                # Mã hóa sang Base64 chuỗi (String)
                encoded_string = base64.b64encode(png_bytes).decode('utf-8')
                
                logger.info("📸 Đã chụp ảnh màn hình thành công.")
                return {
                    "success": True, 
                    "format": "png",
                    "image_b64": encoded_string
                }
        except Exception as e:
            logger.error(f"❌ Lỗi khi chụp màn hình: {e}")
            return {"success": False, "error": str(e)}

# Khởi tạo instance dùng chung
screenshot_manager = ScreenshotManager()