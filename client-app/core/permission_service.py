"""
===============================================================================
FILE: client-app/core/permission_service.py
PURPOSE: Quản lý logic xin quyền End User, đếm ngược Timeout 15 giây và điều phối
         kết quả phê duyệt cho các tính năng nhạy cảm.
ARCHITECTURE ROLE:
  - Hiện thực hóa triết lý Bảo vệ Quyền riêng tư (Privacy-First).
  - Khớp nối dữ liệu với WSPermissionRequestPayload & WSPermissionResponsePayload.
  - Sử dụng asyncio.Future + PyQt6 Signals để tạm dừng luồng xử lý lệnh,
    chờ phản hồi tương tác từ giao diện UI Popup (Main Thread).
===============================================================================
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

# Import cấu hình ứng dụng
from config import settings

logger = logging.getLogger("PermissionService")


class PermissionService(QObject):
    """
    Service đóng vai trò Trọng tài quản lý các yêu cầu xin quyền (User Consent).
    Kế thừa QObject để sử dụng hệ thống Signal/Slot của PyQt6.
    """

    # =========================================================================
    # SIGNALS (Tín hiệu phát sang Main GUI Thread để hiển thị Popup)
    # Params: (permission_id: str, feature: str, requested_by: str, timeout_seconds: int)
    # =========================================================================
    show_popup_signal = pyqtSignal(str, str, str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Bảng lưu trữ các yêu cầu xin quyền đang chờ xử lý (In-flight Requests)
        # Cấu trúc: { permission_id: asyncio.Future }
        self._pending_requests: Dict[str, asyncio.Future] = {}

    async def request_permission(
        self, 
        feature: str, 
        requested_by: str, 
        original_message_id: str
    ) -> bool:
        """
        Hàm bất đồng bộ được gọi bởi CommandDispatcher khi nhận lệnh nhạy cảm.
        
        Args:
            feature (str): Tên chức năng nhạy cảm (VD: 'webcam', 'screen.live', 'keylogger')
            requested_by (str): Tên Admin thực hiện gửi lệnh
            original_message_id (str): ID tin nhắn gốc của lệnh
            
        Returns:
            bool: True nếu End User chọn ACCEPT, False nếu REJECT hoặc TIMEOUT 15s.
        """
        # 1. Tạo một permission_id duy nhất khớp với Schema protocol.py
        permission_id = str(uuid.uuid4())
        
        # 2. Tạo asyncio.Future để chờ kết quả từ UI Popup
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_requests[permission_id] = future

        logger.info(
            f"🔒 [PERMISSION REQUEST] Tạo yêu cầu [{permission_id}] cho feature: '{feature}' | Admin: '{requested_by}'"
        )

        # 3. Phát Signal yêu cầu Main Thread hiển thị Popup Popup
        self.show_popup_signal.emit(
            permission_id,
            feature,
            requested_by,
            settings.PERMISSION_TIMEOUT_SECONDS
        )

        # 4. Tạm dừng (await) chờ kết quả từ Popup HOẶC quá thời hạn 15s Timeout
        try:
            # Buffer thêm 1 giây cho độ trễ vẽ giao diện GUI
            timeout_limit = settings.PERMISSION_TIMEOUT_SECONDS + 1.0
            
            granted = await asyncio.wait_for(future, timeout=timeout_limit)
            
            if granted:
                logger.info(f"✅ [PERMISSION GRANTED] End User ĐÃ ĐỒNG Ý yêu cầu [{permission_id}] ({feature})")
            else:
                logger.warning(f"❌ [PERMISSION DENIED] End User ĐÃ TỪ CHỐI yêu cầu [{permission_id}] ({feature})")
                
            return granted

        except asyncio.TimeoutError:
            logger.error(
                f"⏰ [PERMISSION TIMEOUT] Đã quá {settings.PERMISSION_TIMEOUT_SECONDS}s người dùng không tương tác. "
                f"Tự động TỪ CHỐI yêu cầu [{permission_id}] ({feature})!"
            )
            return False
            
        finally:
            # Dọn dẹp request khỏi bộ nhớ sau khi hoàn tất
            self._cleanup_request(permission_id)

    def handle_user_response(self, permission_id: str, granted: bool):
        """
        Hàm được GUI Popup (Main Thread) gọi khi End User bấm nút ACCEPT / REJECT 
        hoặc khi Thanh đếm ngược 15s trên giao diện chạy hết.
        
        Args:
            permission_id (str): Mã yêu cầu xin quyền
            granted (bool): True nếu bấm Accept, False nếu bấm Reject/Hết giờ
        """
        if permission_id in self._pending_requests:
            future = self._pending_requests[permission_id]
            
            # Gán kết quả vào Future để giải phóng lệnh 'await' ở hàm request_permission
            if not future.done():
                future.set_result(granted)
        else:
            logger.debug(f"Nhận phản hồi cho permission_id đã bị dọn dẹp hoặc hết hạn: {permission_id}")

    def _cleanup_request(self, permission_id: str):
        """
        Xóa request khỏi Dictionary lưu trữ để tránh rò rỉ bộ nhớ (Memory Leak).
        """
        if permission_id in self._pending_requests:
            del self._pending_requests[permission_id]