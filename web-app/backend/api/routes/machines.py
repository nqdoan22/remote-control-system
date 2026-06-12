from fastapi import APIRouter
from core.gateway_client import gateway_client

router = APIRouter()

@router.get("/")
async def get_machines():
    """Get list of all connected machines from Gateway."""
    # TODO: Query Gateway for connected machines list
    return {"machines": []}

@router.get("/{machine_id}/status")
async def get_machine_status(machine_id: str):
    """Get online/offline status of a specific machine."""
    # TODO: Query Gateway for machine status
    return {"machine_id": machine_id, "status": "unknown"}
