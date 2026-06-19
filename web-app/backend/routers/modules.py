from fastapi import APIRouter, Depends, Query, Body
from core import security
from main import client

router = APIRouter(prefix="/api/modules", tags=["Modules Control"])

# --- Group 1: Applications (Ứng dụng) ---
@router.get("/{machine_id}/applications")
async def get_applications(machine_id: str, current_user: dict = Depends(security.get_current_user)):
    """Yêu cầu Agent liệt kê các ứng dụng (giới hạn ứng dụng, %CPU)."""
    await client.send_command(
        machine_id=machine_id,
        module="applications",
        action="list",
        payload={}
    )
    return {"status": "command_sent", "message": "Đã gửi yêu cầu lấy danh sách ứng dụng."}

@router.post("/{machine_id}/applications/open")
async def open_application(
    machine_id: str, 
    app_name: str = Body(..., embed=True),
    current_user: dict = Depends(security.get_current_user)
):
    """Yêu cầu mở một ứng dụng cụ thể."""
    await client.send_command(
        machine_id=machine_id,
        module="applications",
        action="start",
        payload={"app_name": app_name}
    )
    return {"status": "command_sent", "detail": f"Đã gửi lệnh mở {app_name}"}

@router.post("/{machine_id}/applications/close")
async def close_application(
    machine_id: str, 
    app_name: str = Body(..., embed=True),
    current_user: dict = Depends(security.get_current_user)
):
    """Yêu cầu đóng một ứng dụng đang chạy."""
    await client.send_command(
        machine_id=machine_id,
        module="applications",
        action="stop",
        payload={"app_name": app_name}
    )
    return {"status": "command_sent", "detail": f"Đã gửi lệnh đóng {app_name}"}


# --- Group 2: Processes (Tiến trình) ---
@router.get("/{machine_id}/processes")
async def get_processes(machine_id: str, current_user: dict = Depends(security.get_current_user)):
    """Lấy danh sách toàn bộ tiến trình hệ thống (%CPU, %RAM)."""
    await client.send_command(
        machine_id=machine_id,
        module="process",
        action="list",
        payload={}
    )
    return {"status": "command_sent", "message": "Đã gửi yêu cầu lấy danh sách tiến trình."}

@router.post("/{machine_id}/processes/kill")
async def kill_process(
    machine_id: str, 
    pid: int = Body(..., embed=True),
    current_user: dict = Depends(security.get_current_user)
):
    """Kill một tiến trình theo PID."""
    await client.send_command(
        machine_id=machine_id,
        module="process",
        action="kill",
        payload={"pid": pid}
    )
    return {"status": "command_sent", "detail": f"Đã gửi lệnh kill PID {pid}"}


# --- Group 3: Screenshot & Live Stream (Màn hình) ---
@router.get("/{machine_id}/screenshot")
async def take_screenshot(machine_id: str, current_user: dict = Depends(security.get_current_user)):
    """Yêu cầu chụp màn hình hiện tại (Cần user xác nhận bên phía Agent)."""
    await client.send_command(
        machine_id=machine_id,
        module="screen",
        action="screenshot",
        payload={}
    )
    return {"status": "command_sent", "message": "Đã gửi yêu cầu chụp màn hình. Đang chờ xác nhận từ client."}


# --- Group 4: File Management (Quản lý tệp tin) ---
@router.get("/{machine_id}/files")
async def browse_files(
    machine_id: str, 
    path: str = Query("C:\\", description="Đường dẫn thư mục muốn xem"),
    current_user: dict = Depends(security.get_current_user)
):
    """Duyệt danh sách file trong thư mục được giới hạn."""
    await client.send_command(
        machine_id=machine_id,
        module="file",
        action="browse",
        payload={"path": path}
    )
    return {"status": "command_sent", "target_path": path}

@router.get("/{machine_id}/files/download")
async def download_file(
    machine_id: str, 
    file_path: str = Query(...),
    current_user: dict = Depends(security.get_current_user)
):
    """Gửi yêu cầu tải file từ máy Agent về."""
    await client.send_command(
        machine_id=machine_id,
        module="file",
        action="download",
        payload={"file_path": file_path}
    )
    return {"status": "command_sent", "file": file_path}


# --- Group 5: Power Control (Điều khiển nguồn - Yêu cầu Approval từ Client) ---
@router.post("/{machine_id}/power/shutdown")
async def shutdown(machine_id: str, current_user: dict = Depends(security.get_current_user)):
    """Tắt máy từ xa."""
    await client.send_command(
        machine_id=machine_id,
        module="power",
        action="shutdown",
        payload={}
    )
    return {"status": "command_sent", "message": "Đã gửi lệnh Shutdown. Chờ xác nhận từ người dùng máy mục tiêu."}

@router.post("/{machine_id}/power/sleep")
async def sleep(machine_id: str, current_user: dict = Depends(security.get_current_user)):
    """Đưa máy vào chế độ ngủ."""
    await client.send_command(
        machine_id=machine_id,
        module="power",
        action="sleep",
        payload={}
    )
    return {"status": "command_sent", "message": "Đã gửi lệnh Sleep. Chờ xác nhận từ người dùng máy mục tiêu."}