from fastapi import APIRouter

router = APIRouter()

# --- Applications ---
@router.get("/{machine_id}/applications")
def get_applications(machine_id: str):
    # TODO: Lấy danh sách ứng dụng đang chạy
    pass

@router.post("/{machine_id}/applications/open")
def open_application(machine_id: str):
    # TODO: Mở ứng dụng trên máy bị điều khiển
    pass

@router.post("/{machine_id}/applications/close")
def close_application(machine_id: str):
    # TODO: Đóng ứng dụng trên máy bị điều khiển
    pass

# --- Processes ---
@router.get("/{machine_id}/processes")
def get_processes(machine_id: str):
    # TODO: Lấy danh sách tiến trình (CPU%, Queue)
    pass

# --- Screenshot ---
@router.get("/{machine_id}/screenshot")
def take_screenshot(machine_id: str):
    # TODO: Chụp màn hình và trả về ảnh
    pass

# --- File Download ---
@router.get("/{machine_id}/files")
def browse_files(machine_id: str):
    # TODO: Duyệt file trên máy bị điều khiển
    pass

@router.get("/{machine_id}/files/download")
def download_file(machine_id: str):
    # TODO: Tải file từ máy bị điều khiển
    pass

# --- Power Control ---
@router.post("/{machine_id}/power/shutdown")
def shutdown(machine_id: str):
    # TODO: Shutdown máy (yêu cầu approval từ client)
    pass

@router.post("/{machine_id}/power/sleep")
def sleep(machine_id: str):
    # TODO: Sleep máy (yêu cầu approval từ client)
    pass
