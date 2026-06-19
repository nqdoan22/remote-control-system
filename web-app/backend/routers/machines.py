from fastapi import APIRouter, Depends, HTTPException, status
from core import security
from main import client  # Import instance client từ main để lấy data kết nối

router = APIRouter(prefix="/api/machines", tags=["Machines Management"])

@router.get("/")
async def get_machines(current_user: dict = Depends(security.get_current_user)):
    """
    Lấy danh sách tất cả các máy Agent đang kết nối vào Gateway.
    Yêu cầu đăng nhập.
    """
    # Giả lập hoặc lấy từ thuộc tính `online_machines` thiết kế thêm trong GatewayClient
    # Cấu trúc mẫu: [{"machine_id": "DESKTOP-PC1", "ip": "192.168.1.15", "os": "Windows 11", "status": "online"}]
    online_machines = getattr(client, "online_machines", {})
    
    # Nếu chưa có dữ liệu thật từ agent, trả về list rỗng hoặc mock data để test frontend
    if not online_machines:
        return [
            {"machine_id": "MOCK-DESKTOP-01", "ip": "192.168.1.50", "os": "Windows 10", "status": "online"},
            {"machine_id": "MOCK-LAPTOP-02", "ip": "192.168.1.65", "os": "Windows 11", "status": "online"}
        ]
        
    return list(online_machines.values())

@router.get("/{machine_id}")
async def get_machine(machine_id: str, current_user: dict = Depends(security.get_current_user)):
    """
    Lấy thông tin chi tiết của một máy cụ thể.
    """
    online_machines = getattr(client, "online_machines", {})
    
    if machine_id in online_machines:
        return online_machines[machine_id]
        
    # Mock data phục vụ test basic flow
    if machine_id == "MOCK-DESKTOP-01":
        return {"machine_id": "MOCK-DESKTOP-01", "ip": "192.168.1.50", "os": "Windows 10", "status": "online"}
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Không tìm thấy máy với ID: {machine_id} hoặc máy đã offline."
    )