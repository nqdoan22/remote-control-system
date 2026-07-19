# gateway/handlers/message_handler.py
import json
import time
import logging
from core.connection_manager import ConnectionManager

logger = logging.getLogger("Gateway.MessageHandler")

class MessageHandler:
    """Xử lý định tuyến (Routing) và kiểm tra quyền (Authorization). Gateway không xử lý Business Logic[cite: 16, 18]."""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def process_incoming_message(self, websocket, raw_message: str, client_type: str, sender_id: str = None):
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return

        # ---------------------------------------------------------------------
        # 1. BỘ DỊCH TƯƠNG THÍCH THEO GIAO THỨC TRUYỀN THÔNG
        # ---------------------------------------------------------------------
        # Bắt buộc sử dụng trường messageId và type theo cấu trúc chuẩn[cite: 18].
        msg_id = data.get("messageId") 
        destination = data.get("destination") 
        msg_type = data.get("type", "unknown")
        payload = data.get("payload", {})
        
        if client_type == "agent" and "data" in data and not payload:
            payload = data["data"]

        # ---------------------------------------------------------------------
        # 2. KIỂM SOÁT AN TOÀN & PHÂN QUYỀN (AUTHORIZATION)
        # ---------------------------------------------------------------------
        # Nguyên tắc Least Privilege: Client App không được phép gửi Command tới Web App hoặc Client App khác[cite: 17].
        if client_type == "agent":
            # Gateway chỉ cho phép Client App gửi: Heartbeat, Response, Event, Streaming Data[cite: 17].
            if msg_type != "heartbeat" and "response" not in msg_type and msg_type != "unknown":
                await self._send_error(websocket, msg_id, "AUTHORIZATION_FAILED", "Quyền hạn không hợp lệ.")
                return
                
            if msg_type == "heartbeat":
                # Nhận Heartbeat định kỳ có chứa payload status online[cite: 18].
                self.manager.update_heartbeat(sender_id)
                return

        # ---------------------------------------------------------------------
        # 3. ĐỊNH TUYẾN TIN NHẮN (MESSAGE ROUTING)
        # ---------------------------------------------------------------------
        # Web App chỉ được phép: Gửi Command, Nhận Response, Nhận Event[cite: 17].
        if client_type == "webapp":
            if not destination:
                await self._send_error(websocket, msg_id, "INVALID_COMMAND", "Thiếu thông tin máy đích.")
                return

            agent_ws = self.manager.get_agent_socket(destination)
            if not agent_ws:
                # Nếu hệ thống phát hiện mất kết nối, trả về chuẩn lỗi MACHINE_OFFLINE[cite: 18].
                await self._send_error(websocket, msg_id, "MACHINE_OFFLINE", f"Máy trạm [{destination}] hiện không trực tuyến.")
                return

            forward_packet = {
                "messageId": msg_id,
                "type": msg_type,
                "timestamp": int(time.time()),
                "source": "gateway", # Phản ánh đúng chặng truyền tin
                "destination": destination,
                "payload": payload
            }
            await agent_ws.send(json.dumps(forward_packet))

        # Phản hồi từ Client App về Web App
        elif client_type == "agent":
            # Trả về Response format theo chuẩn[cite: 18].
            return_packet = {
                "messageId": msg_id,
                "type": "response",
                "timestamp": int(time.time()),
                "source": sender_id,
                "destination": "webapp",
                "payload": payload
            }
            
            for webapp_ws in self.manager.webapp_connections:
                try:
                    await webapp_ws.send(json.dumps(return_packet))
                except Exception:
                    pass

    async def _send_error(self, websocket, msg_id: str, code: str, message: str):
        """Hàm phụ trợ trả về Standard Error Code (VD: AUTHENTICATION_FAILED, PERMISSION_DENIED)[cite: 18]."""
        error_response = {
            "messageId": msg_id,
            "type": "error",
            "timestamp": int(time.time()),
            "source": "gateway",
            "destination": "webapp",
            "payload": {
                "code": code,
                "message": message
            }
        }
        try:
            await websocket.send(json.dumps(error_response))
        except Exception:
            pass