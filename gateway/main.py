import asyncio
import websockets
from core.connection_manager import ConnectionManager
from handlers.message_handler import handle_message

manager = ConnectionManager()

async def handle_client(websocket, path):
    """Xử lý kết nối từ Windows Client App"""
    machine_id = await manager.register(websocket)
    try:
        async for message in websocket:
            await handle_message(manager, machine_id, message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await manager.unregister(machine_id)

async def main():
    print("Gateway đang chạy tại ws://0.0.0.0:8765")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await asyncio.Future()  # Chạy mãi mãi

if __name__ == "__main__":
    asyncio.run(main())
