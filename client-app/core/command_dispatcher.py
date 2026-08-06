"""
===============================================================================
FILE: client-app/core/command_dispatcher.py
PURPOSE: Bộ điều phối lệnh (Command Dispatcher) trên Client App (Agent).
ARCHITECTURE ROLE:
  - Nhận Envelope WSMessage (dict) đã phát ra bởi GatewayService, phân loại
    theo trường `type` ĐÚNG như bảng message type trong docs/api_contract.md,
    gọi module thực thi tương ứng (modules/*.py) rồi đóng gói KẾT QUẢ thành
    Envelope "response"/"error" chuẩn contract gửi ngược về Gateway.
  - Chạy trên Main GUI Thread (được gọi từ AgentApplication._handle_gateway_message,
    vốn là slot nhận pyqtSignal từ GatewayService — Qt tự động Queued Connection
    xuyên Thread). Các module bất đồng bộ (live_screen, webcam) được lên lịch
    chạy trên Event Loop của GatewayService qua gateway_service.run_coroutine_threadsafe().
===============================================================================
"""

import logging
import mimetypes
import time
import uuid
from typing import Any, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

# Import cấu hình định danh Agent
from config import settings

# Import các Module thực thi lệnh (Direct Execution - tương tác cấp OS)
from modules import applications, processes, screenshot, file_manager, power_control
from modules.live_screen import screen_streamer
from modules.webcam import webcam_streamer
from modules.keylogger import keylogger_service

logger = logging.getLogger("CommandDispatcher")


class CommandDispatcher(QObject):
    """
    Lớp điều phối trung tâm: nhận lệnh từ Gateway -> thực thi -> trả kết quả.

    Cách mở rộng thêm Module:
      - Viết handler dạng `_handle_<message_type>(payload, original_message)`.
      - Đăng ký đúng message type (theo docs/api_contract.md) vào `self._handlers`.
    """

    # Phát tín hiệu bật/tắt Red Indicator (đèn báo đỏ webcam). Phải đi qua Signal
    # vì webcam.start/stop chạy trên Gateway Service Thread, còn RedIndicatorWidget
    # là widget GUI chỉ được thao tác an toàn từ Main GUI Thread.
    red_indicator_signal = pyqtSignal(bool)

    def __init__(self, gateway_service, main_window, permission_service):
        """
        Args:
            gateway_service: Đối tượng GatewayService (gửi phản hồi + lên lịch coroutine).
            main_window: Đối tượng MainWindow (ghi log công khai cho End User).
            permission_service: Đối tượng PermissionService (luồng xin quyền Sensitive Feature).
        """
        super().__init__()
        self.gateway_service = gateway_service
        self.main_window = main_window
        self.permission_service = permission_service

        # Bảng ánh xạ: message type (theo api_contract.md) -> Hàm xử lý tương ứng.
        self._handlers: Dict[str, callable] = {
            # Application
            "application.list": self._handle_application_list,
            "application.start": self._handle_application_start,
            "application.stop": self._handle_application_stop,
            # Process
            "process.list": self._handle_process_list,
            "process.kill": self._handle_process_kill,
            # Screen
            "screen.screenshot": self._handle_screen_screenshot,
            "screen.live.start": self._handle_screen_live_start,
            "screen.live.stop": self._handle_screen_live_stop,
            # Webcam
            "webcam.start": self._handle_webcam_start,
            "webcam.stop": self._handle_webcam_stop,
            # Keylogger
            "keylogger.start": self._handle_keylogger_start,
            "keylogger.stop": self._handle_keylogger_stop,
            # File
            "file.list": self._handle_file_list,
            "file.download": self._handle_file_download,
            "file.upload": self._handle_file_upload,
            # Power
            "power.lock": self._handle_power_lock,
            "power.restart": self._handle_power_restart,
            "power.shutdown": self._handle_power_shutdown,
            "power.sleep": self._handle_power_sleep,
            # Permission Confirmation flow (Gateway -> Client App)
            "permission.request": self._handle_permission_request,
        }

    # =========================================================================
    # ĐIỂM VÀO CHÍNH (PUBLIC ENTRYPOINT)
    # =========================================================================
    def dispatch(self, message: Dict[str, Any]) -> None:
        """
        Hàm trung tâm được main.py gọi mỗi khi nhận 1 tin nhắn từ Gateway.
        """
        msg_type = message.get("type", "")
        payload = message.get("payload", {}) or {}

        # "response"/"error" là ACK mà chính Gateway gửi ngược lại cho Client App
        # (VD: xác nhận auth.client thành công ở client_handler.py) — đây KHÔNG
        # phải lệnh cần thực thi, nên bỏ qua thay vì báo INVALID_COMMAND.
        if msg_type in ("response", "error"):
            logger.debug(f"[DISPATCH] Bỏ qua ACK type='{msg_type}' từ Gateway.")
            return

        handler = self._handlers.get(msg_type)

        if handler is None:
            logger.warning(f"[DISPATCH] Message type không được Client App hỗ trợ: '{msg_type}'")
            self._send_error(message, "INVALID_COMMAND", f"Message type '{msg_type}' không được Client App hỗ trợ.")
            return

        logger.info(f"[DISPATCH] Nhận lệnh type='{msg_type}' từ '{message.get('source')}'")
        try:
            handler(payload, message)
        except Exception as e:
            logger.error(f"[DISPATCH] Lỗi khi xử lý lệnh '{msg_type}': {e}", exc_info=True)
            self._send_error(message, "INTERNAL_ERROR", f"Lỗi xử lý lệnh trên Agent: {e}")

    # =========================================================================
    # APPLICATION MANAGEMENT
    # =========================================================================
    def _handle_application_list(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        raw_apps = applications.list_applications()
        app_list = [
            {
                "name": app.get("app_name", "Unknown"),
                "pid": app.get("pid"),
                # hwnd: Handle CỬA SỔ cụ thể. Cần truyền kèm khi đóng vì một app
                # (VD: Chrome) có thể có NHIỀU cửa sổ dùng chung 1 PID — chỉ có
                # hwnd mới phân biệt được từng cửa sổ để đóng đúng 1 cửa sổ.
                "hwnd": app.get("hwnd"),
                "cpuUsage": 0.0,
                "mainWindowTitle": app.get("window_title", ""),
            }
            for app in raw_apps
        ]
        self._send_response(original, {"applications": app_list})

    def _handle_application_start(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        path = str(payload.get("path", "")).strip()
        if not path:
            self._send_error(original, "INVALID_COMMAND", "Thiếu field 'path'.")
            return

        result = applications.launch_application(path)
        if result.get("success"):
            self.main_window.append_log(f"🚀 Đã khởi chạy ứng dụng: '{path}' (PID: {result.get('pid')}).")
            self._send_response(original, {})
        else:
            self._send_error(original, "INTERNAL_ERROR", result.get("message", "Không thể khởi chạy ứng dụng."))

    def _handle_application_stop(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        try:
            pid = int(payload.get("pid"))
        except (TypeError, ValueError):
            self._send_error(original, "INVALID_COMMAND", "Thiếu hoặc sai field 'pid'.")
            return

        # hwnd (tùy chọn): nếu có, chỉ đóng ĐÚNG cửa sổ đó thay vì cả tiến trình.
        # Quan trọng với Chrome/Edge: nhiều cửa sổ chung 1 PID -> terminate cả
        # tiến trình sẽ đóng hết mọi cửa sổ, còn đóng theo hwnd chỉ đóng 1 cửa sổ.
        hwnd = payload.get("hwnd")
        if hwnd is not None:
            try:
                hwnd = int(hwnd)
            except (TypeError, ValueError):
                hwnd = None

        result = applications.close_application(pid, hwnd=hwnd)
        if result.get("success"):
            self._send_response(original, {})
        else:
            self._send_error(original, "INTERNAL_ERROR", result.get("message", ""))

    # =========================================================================
    # PROCESS MANAGEMENT
    # =========================================================================
    def _handle_process_list(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        raw_processes = processes.list_processes()
        process_list = [
            {
                "pid": proc.get("pid"),
                "name": proc.get("name", "Unknown"),
                "cpuUsage": proc.get("cpu_percent", 0.0),
                "memoryMB": proc.get("memory_mb", 0.0),
            }
            for proc in raw_processes
        ]
        self._send_response(original, {"processes": process_list})

    def _handle_process_kill(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        try:
            pid = int(payload.get("pid"))
        except (TypeError, ValueError):
            self._send_error(original, "INVALID_COMMAND", "Thiếu hoặc sai field 'pid'.")
            return

        result = processes.kill_process(pid)
        if result.get("success"):
            self._send_response(original, {})
        else:
            self._send_error(original, "INTERNAL_ERROR", result.get("message", ""))

    # =========================================================================
    # SCREEN — SCREENSHOT (nhạy cảm — cần Permission Confirmation từ Gateway)
    #            & LIVE SCREEN (nhạy cảm)
    # =========================================================================
    def _handle_screen_screenshot(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        result = screenshot.take_screenshot()
        if result.get("success"):
            self._send_response(original, {
                "image": result["image_base64"],
                "width": result["width"],
                "height": result["height"],
                "timestamp": int(time.time()),
            })
        else:
            self._send_error(original, "INTERNAL_ERROR", result.get("message", "Chụp màn hình thất bại."))

    def _handle_screen_live_start(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        # KHÔNG còn từ chối ALREADY_RUNNING nữa: nếu stream cũ (VD: lần trước
        # Admin rời trang đột ngột) vẫn chưa tắt, LiveScreenStreamer.start_stream
        # sẽ tự động dừng stream cũ rồi khởi động lại -> lệnh start luôn thành công.
        fps = self._clamp_fps(payload.get("fps"), settings.SCREEN_FPS)
        # Admin đang xem CHÍNH máy này (Web App tự phát hiện và gửi kèm) → che
        # vùng khung xem Live Screen để chống đệ quy feedback loop. Nếu Web App
        # gửi kèm `video_rect` (toạ độ khung xem, CSS px, tương đối cửa sổ trình
        # duyệt) + `dpr` thì Client chỉ che ĐÚNG vùng đó — không còn đen màn hình
        # toàn bộ khi cửa sổ trình duyệt được phóng to.
        self_view = bool(payload.get("self_view", False))
        video_rect = payload.get("video_rect") if self_view else None
        try:
            dpr = float(payload.get("dpr", 1.0) or 1.0)
        except (TypeError, ValueError):
            dpr = 1.0
        frame_counter = {"n": 0}

        def on_frame(base64_img: str, width: int, height: int) -> None:
            frame_counter["n"] += 1
            self._send_frame_event(
                "screen.live.frame",
                {
                    "image_base64": base64_img,
                    "width": width,
                    "height": height,
                    "frameIndex": frame_counter["n"],
                    "timestamp": int(time.time()),
                },
            )

        # start_stream/stop_stream giờ là hàm đồng bộ chạy trên worker thread,
        # KHÔNG cần lên lịch coroutine trên event loop (event loop luôn rảnh để
        # nhận lệnh điều khiển tiếp theo ngay lập tức).
        screen_streamer.start_stream(
            on_frame,
            fps=fps,
            mask_browser_windows=self_view,
            video_rect=video_rect,
            dpr=dpr,
        )
        self.main_window.append_log(f"📹 Bắt đầu Live Screen (FPS: {fps}).")
        self._send_response(original, {})

    def _handle_screen_live_stop(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        # Idempotent: dừng stream dù đang chạy hay đã dừng đều trả response thành
        # công — tránh cảnh lệnh stop thất bại khiến stream không bao giờ tắt được.
        screen_streamer.stop_stream()
        self.main_window.append_log("🛑 Đã dừng Live Screen.")
        self._send_response(original, {})

    # =========================================================================
    # WEBCAM (nhạy cảm)
    # =========================================================================
    def _handle_webcam_start(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        if webcam_streamer.is_streaming:
            self._send_error(original, "ALREADY_RUNNING", "Webcam đang chạy rồi.")
            return

        fps = self._clamp_fps(payload.get("fps"), settings.WEBCAM_FPS)
        frame_counter = {"n": 0}

        def on_frame(base64_img: str, width: int, height: int) -> None:
            frame_counter["n"] += 1
            self._send_frame_event(
                "webcam.frame",
                {
                    "image_base64": base64_img,
                    "width": width,
                    "height": height,
                    "frameIndex": frame_counter["n"],
                    "timestamp": int(time.time()),
                },
            )

        async def _start():
            ok, error_msg = await webcam_streamer.start_webcam(on_frame, fps=fps)
            if ok:
                if settings.RED_INDICATOR_ENABLED:
                    self.red_indicator_signal.emit(True)
                self.main_window.append_log(f"📷 Bắt đầu Webcam (FPS: {fps}).")
                self._send_response(original, {})
            else:
                self._send_error(original, "WEBCAM_NOT_FOUND", error_msg or "Không thể truy cập webcam trên máy.")

        self.gateway_service.run_coroutine_threadsafe(_start())

    def _handle_webcam_stop(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        if not webcam_streamer.is_streaming:
            self._send_error(original, "NOT_RUNNING", "Webcam chưa được khởi động.")
            return

        async def _stop():
            await webcam_streamer.stop_webcam()
            self.red_indicator_signal.emit(False)
            self.main_window.append_log("🛑 Đã tắt Webcam.")
            self._send_response(original, {})

        self.gateway_service.run_coroutine_threadsafe(_stop())

    # =========================================================================
    # KEYLOGGER (nhạy cảm)
    # =========================================================================
    def _handle_keylogger_start(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        # Idempotent: start_logging() tự động dừng phiên cũ (nếu đang chạy do
        # phiên trước bị sót) rồi khởi động lại -> lệnh start LUÔN thành công,
        # không còn báo lỗi ALREADY_RUNNING (giống Live Screen).

        def on_flush(entries, window_title: str) -> None:
            # Chạy trên Thread nền riêng của KeyloggerService (không phải GUI Thread
            # cũng không phải Gateway Service Thread) -> bắt buộc dùng send_message_threadsafe.
            self.gateway_service.send_message_threadsafe({
                "messageId": str(uuid.uuid4()),
                "type": "keylogger.data",
                "timestamp": int(time.time()),
                "source": settings.CLIENT_ID,
                "destination": "gateway",
                "payload": {"entries": entries, "windowTitle": window_title},
            })

        keylogger_service.start_logging(on_flush)
        self.main_window.append_log("⌨️ Đã bật Keylogger.")
        self._send_response(original, {})

    def _handle_keylogger_stop(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        if not keylogger_service.is_logging:
            self._send_error(original, "NOT_RUNNING", "Keylogger chưa được khởi động.")
            return

        keylogger_service.stop_logging()
        self.main_window.append_log("🛑 Đã tắt Keylogger.")
        self._send_response(original, {})

    # =========================================================================
    # FILE TRANSFER (Sandboxed)
    # =========================================================================
    def _handle_file_list(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        path = str(payload.get("path", ""))
        result = file_manager.list_directory(path)
        if not result.get("success"):
            self._send_error(original, result.get("code", "INTERNAL_ERROR"), result.get("message", ""))
            return

        entries = [
            {
                "name": item["name"],
                "type": "directory" if item["is_dir"] else "file",
                "sizeBytes": item.get("size_bytes", 0),
                "modifiedAt": item.get("modified_time", 0),
            }
            for item in result.get("items", [])
        ]
        # rootPath: gốc Sandbox tuyệt đối, giúp Web Admin hiển thị/khôi phục đường
        # dẫn mặc định đúng theo cấu hình từng máy (file_manager.list_directory trả
        # về "root_path"). Contract: response.data = { rootPath, entries }.
        self._send_response(original, {
            "rootPath": result.get("root_path", str(settings.SANDBOX_DIR.resolve())),
            "entries": entries,
        })

    def _handle_file_download(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        path = str(payload.get("path", ""))
        # Tự nhận diện File/Thư mục: thư mục được nén thành <tên>.zip rồi trả về
        # (xem file_manager.download_path) — Admin chỉ cần gửi path, không cần biết loại.
        result = file_manager.download_path(path)
        if not result.get("success"):
            self._send_error(original, result.get("code", "INTERNAL_ERROR"), result.get("message", ""))
            return

        filename = result.get("file_name", "")
        content_b64 = result.get("file_data_base64", "")
        mime_type, _ = mimetypes.guess_type(filename)
        # sizeBytes lấy trực tiếp từ stat() của module — không phải decode lại
        # base64 (tránh tốn gấp đôi bộ nhớ cho file ~50MB).
        size_bytes = result.get("size_bytes") or 0

        self._send_response(original, {
            "filename": filename,
            "content": content_b64,
            "sizeBytes": size_bytes,
            "mimeType": mime_type or "application/octet-stream",
        })

    def _handle_file_upload(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        dest_path = str(payload.get("destinationPath", "")).strip()
        content_b64 = str(payload.get("content", ""))
        if not dest_path:
            self._send_error(original, "INVALID_COMMAND", "Thiếu field 'destinationPath'.")
            return

        result = file_manager.upload_file(dest_path, content_b64)
        if not result.get("success"):
            self._send_error(original, result.get("code", "INTERNAL_ERROR"), result.get("message", ""))
            return

        self._send_response(original, {"savedPath": result.get("saved_path", dest_path)})

    # =========================================================================
    # POWER MANAGEMENT (nhạy cảm)
    # =========================================================================
    def _handle_power_lock(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        self._finish_power(original, power_control.lock_screen())

    def _handle_power_restart(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        delay = self._safe_int(payload.get("delaySeconds"), default=0)
        self._finish_power(original, power_control.restart_system(delay_seconds=delay))

    def _handle_power_shutdown(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        delay = self._safe_int(payload.get("delaySeconds"), default=0)
        self._finish_power(original, power_control.shutdown_system(delay_seconds=delay))

    def _handle_power_sleep(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        self._finish_power(original, power_control.sleep_system())

    def _finish_power(self, original: Dict[str, Any], result: Dict[str, Any]) -> None:
        if result.get("success"):
            self.main_window.append_log(f"⚡ {result.get('message', '')}")
            self._send_response(original, {})
        else:
            self._send_error(original, "INTERNAL_ERROR", result.get("message", ""))

    # =========================================================================
    # PERMISSION CONFIRMATION FLOW (Gateway -> Client App)
    # =========================================================================
    def _handle_permission_request(self, payload: Dict[str, Any], original: Dict[str, Any]) -> None:
        permission_id = payload.get("permissionId", "")
        feature = payload.get("feature", "")
        requested_by = payload.get("requestedBy", "unknown")

        if not permission_id:
            logger.warning("[PERMISSION] permission.request thiếu permissionId, bỏ qua.")
            return

        async def _flow():
            granted = await self.permission_service.request_permission(permission_id, feature, requested_by)
            self.gateway_service.send_message_threadsafe({
                "messageId": str(uuid.uuid4()),
                "type": "permission.response",
                "timestamp": int(time.time()),
                "source": settings.CLIENT_ID,
                "destination": "gateway",
                "payload": {"permissionId": permission_id, "granted": granted},
            })

        self.gateway_service.run_coroutine_threadsafe(_flow())

    # =========================================================================
    # HÀM BỔ TRỢ
    # =========================================================================
    @staticmethod
    def _clamp_fps(raw_fps: Any, default_fps: int) -> int:
        """Giới hạn FPS trong khoảng [1, 30] theo docs/api_contract.md."""
        try:
            fps = int(raw_fps) if raw_fps is not None else default_fps
        except (TypeError, ValueError):
            fps = default_fps
        return max(1, min(30, fps))

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    def _send_frame_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Gửi các event streaming liên tục (screen.live.frame / webcam.frame)."""
        self.gateway_service.send_message_threadsafe({
            "messageId": str(uuid.uuid4()),
            "type": event_type,
            "timestamp": int(time.time()),
            "source": settings.CLIENT_ID,
            "destination": "gateway",
            "payload": payload,
        })

    def _send_response(self, original_message: Dict[str, Any], data: Optional[Dict[str, Any]]) -> None:
        """Gửi response thành công đúng format contract: type='response', payload={success, data}."""
        original_message_id = original_message.get("messageId")
        envelope = {
            "messageId": str(uuid.uuid4()),
            "type": "response",
            "timestamp": int(time.time()),
            "source": settings.CLIENT_ID,
            "destination": "gateway",
            "payload": {
                "success": True,
                "data": data or {},
            },
        }
        self.gateway_service.send_message_threadsafe(envelope)
        logger.info(f"[DISPATCH] Đã gửi response cho messageId={original_message_id}.")

    def _send_error(self, original_message: Dict[str, Any], code: str, message: str) -> None:
        """Gửi error đúng format contract: type='error', payload={code, message, originalMessageId}."""
        original_message_id = original_message.get("messageId")
        envelope = {
            "messageId": str(uuid.uuid4()),
            "type": "error",
            "timestamp": int(time.time()),
            "source": settings.CLIENT_ID,
            "destination": "gateway",
            "payload": {
                "code": code,
                "message": message,
                "originalMessageId": original_message_id,
            },
        }
        self.gateway_service.send_message_threadsafe(envelope)
        logger.warning(f"[DISPATCH] Đã gửi error '{code}' cho messageId={original_message_id}: {message}")
