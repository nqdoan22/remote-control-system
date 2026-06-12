class ConnectionManager:
    def __init__(self):
        self.machines = {}  # machine_id -> websocket
        self.webapp = None  # websocket của Web App

    async def register(self, websocket) -> str:
        # TODO: Đăng ký máy mới kết nối, sinh machine_id
        # TODO: Thông báo cho Web App có máy mới online
        pass

    async def unregister(self, machine_id: str):
        # TODO: Xóa máy khỏi danh sách
        # TODO: Thông báo cho Web App máy offline
        pass

    async def send_to_machine(self, machine_id: str, message: dict):
        # TODO: Gửi lệnh đến một máy cụ thể
        pass

    async def send_to_webapp(self, message: dict):
        # TODO: Gửi dữ liệu về Web App
        pass

    def get_online_machines(self) -> list:
        # TODO: Trả về danh sách máy đang online
        pass
