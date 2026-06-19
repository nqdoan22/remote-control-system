import logging

logger = logging.getLogger("Handlers")

async def handle_application_list(payload):
    """Xử lý danh sách ứng dụng gửi về từ Agent."""
    logger.info(f"Đang cập nhật danh sách ứng dụng: {len(payload.get('apps', []))} items.")
    # Ở đây bạn có thể lưu vào DB hoặc Cache để Frontend lấy ra
    pass

async def handle_process_list(payload):
    """Xử lý danh sách tiến trình."""
    logger.info("Đang xử lý thông tin tiến trình...")
    # Ví dụ: kiểm tra xem có tiến trình nào ngốn quá 90% CPU không
    pass

async def handle_screenshot_data(payload):
    """Xử lý dữ liệu ảnh screenshot."""
    # Payload thường là base64 image hoặc path
    logger.info("Nhận dữ liệu màn hình mới.")
    pass

async def handle_permission_request(payload):
    """Xử lý yêu cầu cấp quyền từ Agent."""
    module = payload.get("module")
    logger.info(f"Agent yêu cầu quyền cho module: {module}")
    # Logic: Thông báo cho Frontend để người dùng Admin bấm "Đồng ý"
    pass

# Bạn có thể thêm các hàm tương tự cho Webcam, File, v.v.