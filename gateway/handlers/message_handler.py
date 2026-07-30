# gateway/handlers/message_handler.py
"""
===============================================================================
FILE: gateway/handlers/message_handler.py
PURPOSE: Xử lý, xác thực và phân loại các gói tin WebSocket gửi tới Gateway.
ARCHITECTURE ROLE:
  - Tiếp nhận chuỗi JSON thô (raw message) từ WebSocket Server (main.py).
  - Kiểm tra và xác thực kết nối ban đầu (system.auth) cho Agent & WebApp.
  - Phản hồi Heartbeat (system.ping -> system.pong).
  - Ép kiểu & Kiểm tra cú pháp theo Pydantic WSMessage Schema.
  - Chuyển giao gói tin đã xác minh cho ConnectionManager để định tuyến.
===============================================================================
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from websockets.server import WebSocketServerProtocol
from pydantic import ValidationError

# Import WSMessage và WSErrorPayload từ protocol schema
from schemas.protocol import WSMessage, WSErrorPayload
from core.connection_manager import manager

logger = logging.getLogger("Gateway.MessageHandler")

# Secret key cấu hình cho Agent và JWT (Có thể nạp từ môi trường hoặc file .env)
AGENT_SECRET_KEY = os.getenv("AGENT_SECRET_KEY", "DEFAULT_SECRET_KEY_123")


class MessageHandler:
    """
    Lớp xử lý logic kiểm tra an ninh, xác thực và phân loại gói tin tại Gateway.
    """

    def __init__(self):
        # Bộ nhớ tạm lưu trạng thái xác thực của từng kết nối Socket:
        # { websocket: {"authenticated": True/False, "type": "agent"|"webapp", "id": "client-app-01"} }
        self.socket_state: Dict[WebSocketServerProtocol, Dict[str, Any]] = {}

    def is_authenticated(self, websocket: WebSocketServerProtocol) -> bool:
        """Kiểm tra xem socket này đã trải qua bước system.auth thành công chưa."""
        return self.socket_state.get(websocket, {}).get("authenticated", False)

    def get_socket_id(self, websocket: WebSocketServerProtocol) -> Optional[str]:
        """Lấy machine_id hoặc identifier gắn liền với socket."""
        return self.socket_state.get(websocket, {}).get("id")

    async def handle_disconnect(self, websocket: WebSocketServerProtocol) -> None:
        """
        Dọn dẹp tài nguyên và thông báo trạng thái khi một kết nối bị đóng.
        """
        state = self.socket_state.pop(websocket, None)
        if state:
            client_type = state.get("type")
            client_id = state.get("id")

            if client_type == "agent" and client_id:
                await manager.unregister_agent(client_id)
                
                # Báo cho tất cả WebApp Admin biết máy Agent này vừa bị ngắt kết nối
                offline_event = WSMessage(
                    type="agent.status",
                    source="gateway",
                    destination="webapp",
                    payload={"machineId": client_id, "status": "offline"}
                )
                await manager.broadcast_to_webapps(offline_event.model_dump_json())

            elif client_type == "webapp":
                await manager.unregister_webapp(websocket)

    async def process_message(self, websocket: WebSocketServerProtocol, raw_message: str) -> None:
        """
        Hàm trung tâm tiếp nhận và xử lý mọi chuỗi JSON tin nhắn gửi tới từ WebSocket.
        """
        # Step 1: Parse JSON thô
        try:
            msg_dict = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning("[INVALID JSON] Nhận gói tin không tuân thủ định dạng JSON.")
            await self._send_error(
                websocket, 
                code="BAD_REQUEST", 
                message="Gói tin gửi lên không đúng định dạng JSON."
            )
            return

        # Step 2: Validate cấu trúc Envelope chuẩn với WSMessage Schema
        try:
            msg = WSMessage(**msg_dict)
        except ValidationError as e:
            logger.warning(f"[INVALID SCHEMA] Gói tin không khớp với WSMessage Schema: {e}")
            await self._send_error(
                websocket, 
                code="INVALID_SCHEMA", 
                message="Gói tin không tuân thủ cấu trúc envelope chuẩn (WSMessage)."
            )
            return

        # Step 3: Xử lý gói tin Xác thực ban đầu (system.auth)
        if msg.type == "system.auth":
            await self._handle_auth(websocket, msg)
            return

        # Step 4: Kiểm tra An ninh (Chặn tất cả các gói tin khác nếu chưa Authenticated)
        if not self.is_authenticated(websocket):
            logger.warning(f"[UNAUTHORIZED] Socket chưa xác thực cố gửi lệnh '{msg.type}'.")
            await self._send_error(
                websocket,
                code="UNAUTHORIZED",
                message="Bạn phải gửi gói tin 'system.auth' để xác thực trước khi thực hiện tác vụ.",
                original_msg_id=msg.messageId
            )
            return

        # Step 5: Xử lý Heartbeat Ping/Pong nội bộ Gateway
        if msg.type == "system.ping":
            await self._handle_ping(websocket, msg)
            return

        # Step 6: Cập nhật timestamp Heartbeat nếu gói tin đến từ một Agent
        socket_info = self.socket_state.get(websocket, {})
        if socket_info.get("type") == "agent":
            manager.update_agent_heartbeat(socket_info["id"])

        # Step 7: Bàn giao định tuyến cho ConnectionManager (Pass-through tốc độ cao)
        routed = await manager.route_message(raw_message, msg)
        if not routed and msg.destination != "gateway":
            await self._send_error(
                websocket,
                code="DESTINATION_UNREACHABLE",
                message=f"Không tìm thấy điểm đến '{msg.destination}' hoặc kết nối đã bị đóng.",
                original_msg_id=msg.messageId
            )

    # =========================================================================
    # CÁC HÀM XỬ LÝ LOGIC NỘI BỘ (PRIVATE METHODS)
    # =========================================================================

    async def _handle_auth(self, websocket: WebSocketServerProtocol, msg: WSMessage) -> None:
        """
        Xử lý logic xác thực cho Agent (Machine Secret) hoặc WebApp (JWT Token).
        """
        payload = msg.payload
        role = payload.get("role")

        # --- Trường hợp 1: Agent xác thực ---
        if role == "agent" or "machineSecret" in payload:
            machine_id = payload.get("machineId") or msg.source
            machine_secret = payload.get("machineSecret")

            # Kiểm tra Secret Key
            if not machine_secret or machine_secret != AGENT_SECRET_KEY:
                logger.error(f"[AUTH FAILED] Agent '{machine_id}' gửi sai Machine Secret.")
                await self._send_error(
                    websocket, 
                    code="AUTH_FAILED", 
                    message="Machine secret không hợp lệ.", 
                    original_msg_id=msg.messageId
                )
                await websocket.close(code=4001, reason="Authentication failed")
                return

            # Đăng ký Socket vào trạng thái Active
            self.socket_state[websocket] = {
                "authenticated": True,
                "type": "agent",
                "id": machine_id
            }
            await manager.register_agent(machine_id, websocket)

            # Gửi phản hồi thành công lại cho Agent
            response = WSMessage(
                type="system.auth.response",
                source="gateway",
                destination=machine_id,
                payload={"success": True, "message": "Xác thực Agent thành công."}
            )
            await websocket.send(response.model_dump_json())

            # Báo tin cho tất cả Admin WebApp biết Agent vừa Online
            online_event = WSMessage(
                type="agent.status",
                source="gateway",
                destination="webapp",
                payload={"machineId": machine_id, "status": "online"}
            )
            await manager.broadcast_to_webapps(online_event.model_dump_json())

        # --- Trường hợp 2: WebApp Admin xác thực ---
        elif role == "webapp" or "token" in payload:
            token = payload.get("token")
            
            if not token:
                logger.error("[AUTH FAILED] WebApp kết nối thiếu JWT Token.")
                await self._send_error(
                    websocket, 
                    code="AUTH_FAILED", 
                    message="Thiếu JWT Access Token.", 
                    original_msg_id=msg.messageId
                )
                await websocket.close(code=4001, reason="Authentication failed")
                return

            self.socket_state[websocket] = {
                "authenticated": True,
                "type": "webapp",
                "id": "webapp"
            }
            await manager.register_webapp(websocket)

            # Phản hồi thành công cho WebApp
            response = WSMessage(
                type="system.auth.response",
                source="gateway",
                destination="webapp",
                payload={"success": True, "message": "Xác thực WebApp thành công."}
            )
            await websocket.send(response.model_dump_json())

        else:
            await self._send_error(
                websocket,
                code="AUTH_INVALID_PAYLOAD",
                message="Payload xác thực thiếu trường 'machineSecret' hoặc 'token'.",
                original_msg_id=msg.messageId
            )

    async def _handle_ping(self, websocket: WebSocketServerProtocol, msg: WSMessage) -> None:
        """
        Phản hồi ngay gói tin Pong để duy trì kết nối Heartbeat.
        """
        pong_msg = WSMessage(
            type="system.pong",
            source="gateway",
            destination=msg.source,
            payload={"replyTo": msg.messageId}
        )
        await websocket.send(pong_msg.model_dump_json())

    async def _send_error(
        self, 
        websocket: WebSocketServerProtocol, 
        code: str, 
        message: str, 
        original_msg_id: Optional[str] = None
    ) -> None:
        """
        Tạo và gửi gói tin phản hồi lỗi theo đúng WSErrorPayload Schema.
        """
        error_payload = WSErrorPayload(
            code=code,
            message=message,
            originalMessageId=original_msg_id
        )
        error_msg = WSMessage(
            type="error",
            source="gateway",
            destination="unknown",
            payload=error_payload.model_dump()
        )
        try:
            await websocket.send(error_msg.model_dump_json())
        except Exception as e:
            logger.error(f"Không thể gửi thông điệp lỗi tới websocket: {e}")


# Tạo Singleton Instance duy nhất để main.py gọi
handler = MessageHandler()