from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_machines():
    # TODO: Lấy danh sách máy đang online từ Gateway
    pass

@router.get("/{machine_id}")
def get_machine(machine_id: str):
    # TODO: Lấy thông tin chi tiết một máy
    pass
