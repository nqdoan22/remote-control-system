# web-app/backend/routers/machines.py
from fastapi import APIRouter, HTTPException, status

# 🚪 Tạo phòng riêng quản lý Máy tính với tiền tố (prefix) là /api/machines
router = APIRouter(prefix="/api/machines", tags=["Machines Management"])

# 💾 MOCK DATA: Giả lập danh sách máy lưu ở bộ nhớ Backend (Sau này sẽ kết nối với Gateway thật)
MOCK_MACHINES = [
    {"id": "agent_01", "name": "DESKTOP-PHONG-LAB-A", "ip": "192.168.1.15", "status": "online", "os": "Windows 11 Pro"},
    {"id": "agent_02", "name": "LAPTOP-GIANG-VIEN", "ip": "192.168.1.20", "status": "online", "os": "Windows 10 Home"},
    {"id": "agent_03", "name": "SERVER-BACKUP-TEST", "ip": "192.168.1.100", "status": "offline", "os": "Windows Server 2022"}
]

# 📋 Ô CỬA 1: Lấy danh sách TOÀN BỘ máy tính (Phục vụ giao diện chính của Dashboard)
# Đường dẫn đầy đủ sẽ là: GET http://127.0.0.1:8000/api/machines
@router.get("/")
def get_all_machines():
    return {
        "status": "success",
        "total": len(MOCK_MACHINES),
        "data": MOCK_MACHINES
    }

# 🔍 Ô CỬA 2: Lấy thông tin CHI TIẾT của MỘT máy cụ thể dựa vào ID trên URL
# Đường dẫn đầy đủ sẽ là: GET http://127.0.0.1:8000/api/machines/{machine_id}
@router.get("/{machine_id}")
def get_machine_detail(machine_id: str):
    # Duyệt qua danh sách để tìm máy có ID khớp với ID người dùng yêu cầu
    for machine in MOCK_MACHINES:
        if machine["id"] == machine_id:
            return {
                "status": "success",
                "data": machine
            }
    
    # 🚨 Nếu duyệt hết bảng mà không thấy máy nào trùng ID, trả về lỗi 404 Không tìm thấy
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Không tìm thấy thiết bị nào có mã ID: {machine_id}"
    )