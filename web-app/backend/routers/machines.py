# web-app/backend/routers/machines.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from db.models import Machine, User
from schemas.machine import MachineResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/machines", tags=["Machines Registry"])

@router.get("/", response_model=List[MachineResponse])
def get_all_machines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Bắt buộc phải có Token mới được xem
):
    """
    Lấy danh sách toàn bộ các máy trạm (Agent) đã từng kết nối vào hệ thống.
    Bao gồm thông tin định danh và trạng thái (online/offline).
    """
    machines = db.query(Machine).all()
    return machines