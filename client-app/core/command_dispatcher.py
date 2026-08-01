"""
===============================================================================
FILE: client-app/core/command_dispatcher.py
PURPOSE: Bộ điều phối lệnh (Command Dispatcher) trên Client App (Agent).
ARCHITECTURE ROLE:
  - Trước đây Gateway gửi lệnh tới Agent nhưng Agent KHÔNG có nơi xử lý
    (main.py chỉ log tin nhắn) => nút "Khởi chạy App" trên WebAdmin gửi lệnh
    tới Agent nhưng không có gì thực thi. File này lấp đúng khoảng trống đó.
  - Nhận Envelope WSMessage (dict) đã phát ra bởi GatewayService, phân loại
    theo trường `type`, gọi module thực thi tương ứng (VD: applications.py)
    rồi đóng gói KẾT QUẢ thành Envelope phản hồi gửi ngược về WebAdmin.
  - Phản hồi kèm `originalMessageId` của lệnh gốc để Backend WebApp định tuyến
    kết quả về đúng Tab Browser đã gửi lệnh (xem gateway_client.py bên web-app).
===============================================================================
"""

import logging
import time
import uuid
from typing import Any, Dict, Optional

# Import cấu hình định danh Agent
from config import settings

# Import các Module thực thi lệnh (Direct Execution - tương tác cấp OS)
from modules import applications, processes

logger = logging.getLogger("CommandDispatcher")


class CommandDispatcher:
    """
    Lớp điều phối trung tâm: nhận lệnh từ Gateway -> thực thi -> trả kết quả.

    Cách mở rộng thêm Module:
      - Viết handler dạng `_handle_<action_name>(payload, original_message)`.
      - Đăng ký action name vào bảng `self._handlers` ở phương thức __init__.
    """

    def __init__(self, gateway_service, main_window):
        """
        Args:
            gateway_service: Đối tượng GatewayService (để gửi phản hồi về Gateway).
            main_window: Đối tượng MainWindow (để ghi log công khai cho End User).
        """
        self.gateway_service = gateway_service
        self.main_window = main_window

        # Bảng ánh xạ: Loại lệnh (message['type']) -> Hàm xử lý tương ứng.
        # 👉 Đây chính là nơi "nối" tên action Frontend gửi lên với hàm module Python.
        self._handlers: Dict[str, callable] = {
            "get_applications": self._handle_get_applications,
            "start_application": self._handle_start_application,
            "stop_application": self._handle_stop_application,
            "get_processes": self._handle_get_processes,
            "kill_process": self._handle_kill_process,
        }

    # =========================================================================
    # ĐIỂM VÀO CHÍNH (PUBLIC ENTRYPOINT)
    # =========================================================================
    def dispatch(self, message: Dict[str, Any]) -> None:
        """
        Hàm trung tâm được main.py gọi mỗi khi nhận 1 tin nhắn từ Gateway.
        Phân loại và điều phối tới handler phù hợp.

        Args:
            message (dict): Envelope WSMessage đã parse từ JSON
                            gồm: messageId, type, source, destination, payload.
        """
        msg_type = message.get("type", "")
        payload = message.get("payload", {}) or {}
        handler = self._handlers.get(msg_type)

        # Lệnh không thuộc Module nào đang được triển khai -> chỉ ghi log
        if handler is None:
            logger.info(f"[DISPATCH] Bỏ qua lệnh chưa đăng ký xử lý: type='{msg_type}'")
            return

        logger.info(f"[DISPATCH] Nhận lệnh type='{msg_type}' từ '{message.get('source')}'")
        try:
            handler(payload, message)
        except Exception as e:
            logger.error(f"[DISPATCH] Lỗi khi xử lý lệnh '{msg_type}': {e}", exc_info=True)
            # Trả lỗi về cho WebAdmin để Admin biết thay vì im lặng
            self._send_response(
                response_type=f"{msg_type}_response",
                original_message=message,
                status="error",
                message=f"Lỗi xử lý lệnh trên Agent: {e}",
                data=None,
            )

    # =========================================================================
    # CÁC HANDLER CỦA MODULE APPLICATIONS (Khởi chạy / Đóng / Liệt kê App)
    # =========================================================================

    def _handle_get_applications(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        """
        Xử lý lệnh 'get_applications':
          - Gọi applications.list_applications() quét danh sách cửa sổ GUI đang mở.
          - Chuyển đổi cấu trúc dữ liệu sang đúng field Frontend Applications.jsx
            đang đọc: { pid, name, title, cpu_percent }.
        """
        raw_apps = applications.list_applications()

        # ADAPTER: ánh xạ field của backend (app_name, window_title) -> frontend (name, title)
        app_list = [
            {
                "pid": app.get("pid"),
                "name": app.get("app_name", "Unknown"),
                "title": app.get("window_title", ""),
                "cpu_percent": 0,  # Module chưa tính %CPU; Frontend có fallback '?? 0'
            }
            for app in raw_apps
        ]

        self._send_response(
            response_type="get_applications_response",
            original_message=original,
            status="success",
            message=f"Tìm thấy {len(app_list)} ứng dụng GUI đang chạy.",
            data=app_list,
        )

    def _handle_start_application(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        """
        Xử lý lệnh 'start_application' (Nút "▶ Khởi chạy App" trên WebAdmin):
          - Lấy tên lệnh/đường dẫn từ payload['app_name'].
          - Gọi applications.launch_application() mở ứng dụng bằng subprocess.Popen.
        """
        app_command = str(payload.get("app_name", "")).strip()
        if not app_command:
            self._send_response(
                response_type="start_application_response",
                original_message=original,
                status="error",
                message="Thiếu tên/đường dẫn ứng dụng (app_name).",
            )
            return

        result = applications.launch_application(app_command)

        # Ghi log minh bạch lên giao diện Agent để End User theo dõi
        self.main_window.append_log(f"🚀 Lệnh khởi chạy ứng dụng: '{app_command}'")
        if result.get("success"):
            self.main_window.append_log(f"✅ Khởi chạy thành công (PID: {result.get('pid')}).")

        self._send_response(
            response_type="start_application_response",
            original_message=original,
            status="success" if result.get("success") else "error",
            message=result.get("message", ""),
            data={"pid": result.get("pid")},
        )

    def _handle_stop_application(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        """
        Xử lý lệnh 'stop_application' (Nút "🛑 Đóng App" trên WebAdmin):
          - Lấy PID cần đóng từ payload['pid'].
          - Gọi applications.close_application() terminate rồi kill nếu cần.
        """
        try:
            pid = int(payload.get("pid"))
        except (TypeError, ValueError):
            self._send_response(
                response_type="stop_application_response",
                original_message=original,
                status="error",
                message="PID không hợp lệ.",
            )
            return

        result = applications.close_application(pid)
        self._send_response(
            response_type="stop_application_response",
            original_message=original,
            status="success" if result.get("success") else "error",
            message=result.get("message", ""),
        )

    # =========================================================================
    # CÁC HANDLER CỦA MODULE PROCESSES (Liệt kê & Kill Tiến trình)
    # =========================================================================

    def _handle_get_processes(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        """
        Xử lý lệnh 'get_processes' (Tab Processes trên WebAdmin):
          - Gọi processes.list_processes() quét toàn bộ tiến trình hệ thống.
          - Chuyển đổi cấu trúc dữ liệu sang đúng field Frontend Processes.jsx
            đang đọc: { pid, name, cpu_percent, memory_mb }.
        """
        raw_processes = processes.list_processes()

        # ADAPTER: giữ các field Frontend cần, loại bỏ field thừa cho gọn payload
        process_list = [
            {
                "pid": proc.get("pid"),
                "name": proc.get("name", "Unknown"),
                "cpu_percent": proc.get("cpu_percent", 0.0),
                "memory_mb": proc.get("memory_mb", 0.0),
            }
            for proc in raw_processes
        ]

        self._send_response(
            response_type="get_processes_response",
            original_message=original,
            status="success",
            message=f"Đã quét {len(process_list)} tiến trình đang chạy.",
            data=process_list,
        )

    def _handle_kill_process(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        """
        Xử lý lệnh 'kill_process' (Nút "⚡ Kill Process" trên WebAdmin):
          - Lấy PID cần diệt từ payload['pid'].
          - Gọi processes.kill_process() terminate rồi kill nếu cần.
        """
        try:
            pid = int(payload.get("pid"))
        except (TypeError, ValueError):
            self._send_response(
                response_type="kill_process_response",
                original_message=original,
                status="error",
                message="PID không hợp lệ.",
            )
            return

        result = processes.kill_process(pid)
        self._send_response(
            response_type="kill_process_response",
            original_message=original,
            status="success" if result.get("success") else "error",
            message=result.get("message", ""),
        )

    # =========================================================================
    # HÀM BỔ TRỢ: ĐÓNG GÓI & GỬI ENVELOPE PHẢN HỒI VỀ WEBADMIN
    # =========================================================================
    def _send_response(
        self,
        response_type: str,
        original_message: Dict[str, Any],
        status: str,
        message: str,
        data: Optional[Any] = None,
    ) -> None:
        """
        Đóng gói kết quả thực thi thành Envelope WSMessage chuẩn rồi gửi về Gateway.

        Ghi chú cơ chế định tuyến phản hồi:
          - destination = 'webapp' -> Gateway broadcast gói tin này tới Backend WebApp.
          - payload['originalMessageId'] = messageId của lệnh gốc -> Backend WebApp
            (gateway_client.py) dò trong bảng browser_pending để trả về đúng Browser.
        """
        # Lấy messageId của lệnh gốc để Backend WebApp định tuyến về đúng Tab Admin
        original_message_id = original_message.get("messageId")

        response_envelope = {
            "messageId": str(uuid.uuid4()),
            "type": response_type,
            "timestamp": int(time.time()),
            "source": settings.CLIENT_ID,
            "destination": "webapp",
            "payload": {
                # replyTo: ghi chú cho người đọc log biết phản hồi của lệnh nào
                "replyTo": original_message_id,
                # originalMessageId: KHÓA ĐỊNH TUYẾN để Backend WebApp trả về đúng Browser
                "originalMessageId": original_message_id,
                "status": status,
                "message": message,
                "data": data,
            },
        }

        # Gửi qua GatewayService (thread-safe, dùng asyncio.run_coroutine_threadsafe)
        self.gateway_service.send_message_threadsafe(response_envelope)
        logger.info(f"[DISPATCH] Đã gửi phản hồi type='{response_type}' (status={status}).")
