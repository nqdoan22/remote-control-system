# client-app/modules/webcam.py
import cv2
import base64
import logging

logger = logging.getLogger("Module-Webcam")

class WebcamManager:
    """Module chụp ảnh từ Webcam của thiết bị."""
    
    @staticmethod
    def capture_photo() -> dict:
        """Mở webcam, lấy 1 khung hình, và đóng webcam ngay lập tức."""
        try:
            # Khởi tạo kết nối với Webcam (index 0 thường là camera mặc định)
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                return {"success": False, "error": "Không tìm thấy hoặc không thể mở Webcam trên máy này."}
            
            # Đọc 1 khung hình
            ret, frame = cap.read()
            
            # Giải phóng camera lập tức để tránh thiết bị bị treo/chiếm dụng
            cap.release()
            
            if not ret:
                return {"success": False, "error": "Không thể chụp ảnh từ luồng Webcam."}
            
            # Nén thành JPEG để nhẹ hơn
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                return {"success": False, "error": "Lỗi nén ảnh Webcam."}
            
            # Mã hóa Base64
            encoded_string = base64.b64encode(buffer).decode('utf-8')
            
            logger.info("📷 Đã chụp ảnh Webcam thành công.")
            return {
                "success": True,
                "format": "jpeg",
                "image_b64": encoded_string
            }
        except Exception as e:
            logger.error(f"❌ Lỗi truy cập Webcam: {e}")
            return {"success": False, "error": str(e)}

# Khởi tạo instance
webcam_manager = WebcamManager()