from fastapi import FastAPI
import asyncio

app = FastAPI()
client = GatewayClient("ws://localhost:8765")

@app.on_event("startup")
async def startup_event():
    # Khởi chạy kết nối trong background khi server bật
    asyncio.create_task(client.connect())

@app.post("/control/{machine_id}")
async def control_machine(machine_id: str, command: dict):
    # API endpoint để Frontend gọi lệnh
    await client.send_command(
        machine_id=machine_id,
        module=command["module"],
        action=command["action"],
        payload=command["payload"]
    )
    return {"status": "sent"}