"""
===============================================================================
FILE: web-app/backend/routers/machines.py
PURPOSE: API Router Quản lý Danh sách và Trạng thái các máy Agent (Machines/Clients).
ARCHITECTURE ROLE: 
  - Đóng vai trò là "Cuốn danh bạ máy trạm".
  - Cung cấp API cho Frontend (dashboard.jsx) hiển thị danh sách máy, IP, OS, trạng thái Online/Offline.
  - Cung cấp API nhận tín hiệu điểm danh (Heartbeat) từ Gateway/Agent để cập nhật trạng thái.
===============================================================================
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Import công cụ CSDL và Security
from db.database import get_db
from db.models import Machine, User
from schemas.machine import MachineResponse, MachineUpdateStatus, MachineListResponse, MachineStatus
from core.security import get_current_user

# Khởi tạo Logger và Router
logger = logging.getLogger("MachinesRouter")
router = APIRouter(prefix="/machines", tags=["Machine Management"])


# =========================================================================
# 🌟 API 1: LẤY DANH SÁCH TẤT CẢ CÁC MÁY AGENT (GET /api/v1/machines/)
# =========================================================================
@router.get("/", response_model=MachineListResponse, summary="Lấy danh sách tất cả các máy Agent")
def get_all_machines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua (phân trang)"),
    limit: int = Query(50, ge=1, le=200, description="Số bản ghi tối đa trả về"),
    status: Optional[MachineStatus] = Query(None, description="Lọc trạng thái: online / offline / busy"),
):
    """
    API phục vụ màn hình Dashboard trên Frontend:
    Mở bảng 'machines' trong CSDL và trả về danh sách các máy Agent đã từng kết nối.
    Hỗ trợ phân trang (skip/limit) và lọc theo trạng thái (status).
    Trả về theo đúng MachineListResponse Schema ({ total, machines }) mà Frontend mong đợi.
    """
    query = db.query(Machine)
    if status is not None:
        query = query.filter(Machine.status == status.value)
    total = query.count()
    machines = query.order_by(Machine.last_seen.desc()).offset(skip).limit(limit).all()
    return MachineListResponse(total=total, machines=machines)


# =========================================================================
# 🌟 API 2: LẤY THÔNG TIN CHI TIẾT 1 MÁY (GET /api/v1/machines/{machine_id})
# =========================================================================
@router.get("/{machine_id}", response_model=MachineResponse, summary="Lấy chi tiết 1 máy Agent")
def get_machine_by_id(
    machine_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    API xem chi tiết cấu hình của 1 máy Agent cụ thể dựa theo machine_id.
    """
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy máy trạm có ID: '{machine_id}'"
        )
    return machine


# =========================================================================
# 🌟 API 3: CẬP NHẬT TRẠNG THÁI / ĐIỂM DANH (POST /api/v1/machines/heartbeat)
# =========================================================================
@router.post("/heartbeat", response_model=MachineResponse, summary="Cập nhật trạng thái điểm danh của Agent")
def update_machine_heartbeat(
    status_data: MachineUpdateStatus,
    db: Session = Depends(get_db)
):
    """
    API nhận thông báo điểm danh:
    Khi Gateway phát hiện một Agent vừa kết nối (Online) hoặc ngắt kết nối (Offline),
    hoặc Agent định kỳ gửi tín hiệu "Tôi còn sống", Gateway sẽ gọi API này để ghi nhận vào DB.
    """
    # 1. Tìm máy trong Database
    machine = db.query(Machine).filter(Machine.machine_id == status_data.machine_id).first()

    now = datetime.now(timezone.utc)

    # 2. Nếu máy chưa từng xuất hiện -> Tạo bản ghi mới trong CSDL
    if not machine:
        logger.info(f"✨ Phát hiện máy Agent MỚI kết nối: '{status_data.machine_id}'")
        machine = Machine(
            machine_id=status_data.machine_id,
            hostname=status_data.hostname,
            ip_address=status_data.ip_address,
            os_info=status_data.os_info,
            status=status_data.status,
            last_seen=now
        )
        db.add(machine)
    # 3. Nếu máy đã có trong CSDL -> Cập nhật thông tin và lần cuối nhìn thấy (last_seen)
    else:
        machine.status = status_data.status
        machine.last_seen = now
        if status_data.hostname:
            machine.hostname = status_data.hostname
        if status_data.ip_address:
            machine.ip_address = status_data.ip_address
        if status_data.os_info:
            machine.os_info = status_data.os_info

    db.commit()
    db.refresh(machine)
    return machine


# =========================================================================
# 🌟 API 4: XÓA MÁY KHỎI DANH SÁCH (DELETE /api/v1/machines/{machine_id})
# =========================================================================
@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa một máy Agent")
def delete_machine(
    machine_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    API cho phép Admin loại bỏ một máy cũ/hỏng ra khỏi danh sách quản lý trên CSDL.
    """
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy máy trạm có ID: '{machine_id}'"
        )
    
    db.delete(machine)
    db.commit()
    return None