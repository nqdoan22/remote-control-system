# gateway/handlers/message_handler.py
import json
import time
import logging
from core.connection_manager import ConnectionManager

logger = logging.getLogger("Gateway.MessageHandler")

class MessageHandler:
    """Xử lý định tuyến, phân loại và kiểm soát an toàn luồng dữ liệu JSON."""
    
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def process_incoming_message(self, websocket, raw_message: str, client_type: str, sender_id: str = None):
        """
        Tiếp nhận gói tin thô, giải mã và áp đặt chính sách bảo mật nghiêm ngặt.
        """
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.error("🚨 Phát hiện gói tin lỗi định dạng cấu trúc JSON. Ngắt xử lý phòng ngừa Ransomware/Exploit.")
            return

        # ---------------------------------------------------------------------
        # 1. BỘ DỊCH TƯƠNG THÍCH (ADAPTER LAYER) - Đồng bộ mã nguồn cũ & MD mới
        # ---------------------------------------------------------------------
        # Ánh xạ các trường từ định dạng cũ của Web App sang cấu trúc chuẩn của Protocol mới
        msg_id = data.get("messageId") or data.get("request_id")
        destination = data.get("destination") or data.get("target")
        
        # Tạo trường type chuẩn "module.action" từ cấu trúc cũ
        if "type" in data:
            msg_type = data["type"]
        elif "module" in data and "action" in data:
            msg_type = f"{data['module']}.{data['action']}"
        else:
            msg_type = "unknown"

        payload = data.get("payload", {})
        
        # Nếu là dữ liệu phản hồi (Response) từ Agent, giữ nguyên cụm 'data' gốc để Web App nhận diện được
        if client_type == "agent" and "data" in data and not payload:
            payload = data["data"]

        # ---------------------------------------------------------------------
        # 2. KIỂM SOÁT AN TOÀN & PHÂN QUYỀN (Authorization Guards)
        # ---------------------------------------------------------------------
        # Nguyên tắc Least Privilege: Agent tuyệt đối không được phép gửi lệnh điều khiển
        if client_type == "agent":
            # Nếu tin nhắn từ Agent không phải là phản hồi (response) hoặc heartbeat -> Chặn ngay lập tức
            if msg_type != "heartbeat" and "response" not in msg_type and msg_type != "unknown":
                logger.error(f"⚠️ CẢNH BÁO BẢO MẬT: Agent [{sender_id}] cố tình gửi lệnh [{msg_type}] hệ thống. Nghi ngờ bị chiếm quyền!")
                await self._send_error(websocket, msg_id, "AUTHORIZATION_FAILED", "Quyền hạn không hợp lệ.")
                return
                
            if msg_type == "heartbeat":
                self.manager.update_heartbeat(sender_id)
                return

        # ---------------------------------------------------------------------
        # 3. ĐỊNH TUYẾN TIN NHẮN (Message Routing)
        # ---------------------------------------------------------------------
        # Luồng A: Từ Web App gửi xuống một máy Agent cụ thể
        if client_type == "webapp":
            if not destination:
                await self._send_error(websocket, msg_id, "INVALID_COMMAND", "Thiếu thông tin máy đích (target/destination).")
                return

            agent_ws = self.manager.get_agent_socket(destination)
            if not agent_ws:
                await self._send_error(websocket, msg_id, "MACHINE_OFFLINE", f"Máy trạm [{destination}] hiện không trực tuyến.")
                return

            # Chuẩn hóa gói tin truyền xuống Agent theo đúng giao thức trong mạng LAN
            forward_packet = {
                "messageId": msg_id,
                "request_id": msg_id, # Đảm bảo Agent C# nhận được request_id cũ nếu cần
                "type": msg_type,
                "timestamp": int(time.time()),
                "source": "webapp",
                "destination": destination,
                "payload": payload
            }
            await agent_ws.send(json.dumps(forward_packet))
            logger.info(f"➡️ Đã chuyển tiếp lệnh [{msg_type}] từ Web App xuống Agent [{destination}].")

        # Luồng B: Từ Agent phản hồi kết quả ngược về Web App
        elif client_type == "agent":
            # Tạo gói tin phản hồi chuẩn hóa phục vụ cơ chế xử lý đồng bộ Future ở Web App Backend
            return_packet = {
                "request_id": msg_id,
                "messageId": msg_id,
                "type": "response",
                "source": sender_id,
                "destination": "webapp",
                "data": payload # Trả về cấu trúc key 'data' khớp hoàn toàn với `gateway_client.py`
            }
            
            # Gửi cho toàn bộ các instance Web App đang lắng nghe
            for webapp_ws in self.manager.webapp_connections:
                try:
                    await webapp_ws.send(json.dumps(return_packet))
                except Exception:
                    pass
            logger.info(f"⬅️ Đã trả kết quả lệnh [{msg_id}] từ Agent [{sender_id}] về Web App.")

    async def _send_error(self, websocket, msg_id: str, code: str, message: str):
        """Hàm phụ trợ trả về lỗi chuẩn hóa hệ thống."""
        error_response = {
            "request_id": msg_id,
            "type": "error",
            "payload": {
                "code": code,
                "message": message
            }
        }
        try:
            await websocket.send(json.dumps(error_response))
        except Exception:
            pass