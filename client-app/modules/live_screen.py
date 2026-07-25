# client-app/modules/live_screen.py
import mss
import cv2
import numpy as np
import base64
import logging

logger = logging.getLogger("Module-LiveScreen")

class LiveScreenManager:
    """Module lấy luồng khung hình (frames) cho tính năng Live Screen."""
    
    def __init__(self):
        self.sct = mss.mss()

    def get_frame(self, quality: int = 50) -> dict:
        """
        Lấy 1 khung hình hiện tại, nén dưới dạng JPEG để tiết kiệm băng thông.
        quality: Chất lượng nén (0-100), mặc định 50 để truyền mượt.
        """
        try:
            monitor = self.sct.monitors[1]
            sct_img = self.sct.grab(monitor)
            
            # Chuyển dữ liệu mss sang ma trận của numpy (để OpenCV đọc được)
            img_np = np.array(sct_img)
            
            # Xóa kênh Alpha (trong BGRA) để thành BGR chuẩn của OpenCV
            frame_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
            
            # Nén ảnh thành JPEG trên RAM
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success, buffer = cv2.imencode('.jpg', frame_bgr, encode_param)
            
            if not success:
                return {"success": False, "error": "Không thể nén khung hình màn hình"}
                
            # Mã hóa Base64
            encoded_string = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "success": True, 
                "format": "jpeg",
                "frame_b64": encoded_string
            }
        except Exception as e:
            logger.error(f"❌ Lỗi Live Screen: {e}")
            return {"success": False, "error": str(e)}

# Khởi tạo instance
live_screen_manager = LiveScreenManager()