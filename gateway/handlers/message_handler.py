import json

async def handle_message(manager, machine_id: str, raw_message: str):
    """Phân loại và điều phối message từ Client App"""
    message = json.loads(raw_message)
    msg_type = message.get("type")

    # TODO: Điều phối theo type
    # Ví dụ các type: "register", "screenshot_result",
    # "processes_result", "keylog_data", "screen_frame",
    # "webcam_frame", "permission_response", ...
    pass
