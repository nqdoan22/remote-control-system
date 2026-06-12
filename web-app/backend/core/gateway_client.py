import asyncio
import websockets
import json

class GatewayClient:
    """Manages WebSocket connection from Web App backend to Gateway."""

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(f"{self.gateway_url}/webapp")

    async def send_command(self, machine_ids: list, module: str, action: str, payload: dict = {}):
        """Send a command to one or multiple machines."""
        for machine_id in machine_ids:
            message = {
                "target": machine_id,
                "module": module,
                "action": action,
                "payload": payload,
            }
            await self.websocket.send(json.dumps(message))

    async def receive(self):
        return json.loads(await self.websocket.recv())

gateway_client = GatewayClient("ws://localhost:8765")
