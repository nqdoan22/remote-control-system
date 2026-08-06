"""
===============================================================================
FILE: web-app/backend/routers/audit_log.py
PURPOSE: API Router truy xuất Nhật ký thao tác hệ thống (Audit Logs).
ARCHITECTURE ROLE: 
  - Đóng vai trò cung cấp API đọc lịch sử thao tác (Audit Logs) cho Frontend.
  - Dữ liệu được GHI vào bảng 'audit_logs' bởi routers/modules.py (thông qua
    hàm dispatch_command_and_log). Router này chỉ phục vụ phần ĐỌC + lọc + phân trang.
  - Khớp với schemas/audit_log.py (AuditLogListResponse / AuditLogResponse).
===============================================================================
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

# Import công cụ CSDL và Security
from db.database import get_db
from db.models import AuditLog, User
from schemas.audit_log import AuditLogListResponse
from core.security import get_current_user

# Khởi tạo Logger và Router
logger = logging.getLogger("AuditLogRouter")
router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


# =========================================================================
# 🌟 API 1: LẤY DANH SÁCH NHẬT KÝ THAO TÁC (GET /api/v1/audit-logs)
# =========================================================================
@router.get("", response_model=AuditLogListResponse, summary="Lấy danh sách nhật ký thao tác")
def get_audit_logs(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua (phân trang)"),
    limit: int = Query(50, ge=1, le=500, description="Số bản ghi tối đa trả về"),
    action: Optional[str] = Query(
        None,
        description="Lọc theo loại hành động (message type theo api_contract.md, VD: power.lock)",
    ),
    target_machine_id: Optional[str] = Query(
        None,
        description="Lọc theo mã máy Agent chịu tác động (machine_id)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Bắt buộc phải có Token Admin mới xem được
):
    """
    API phục vụ màn hình Dashboard trên Frontend:
    Mở bảng 'audit_logs' trong CSDL và trả về danh sách nhật ký mới nhất.
    Hỗ trợ phân trang (skip/limit) và lọc theo action / target_machine_id.
    Trả về theo đúng AuditLogListResponse Schema ({ total, logs }) mà Frontend mong đợi.
    """
    query = db.query(AuditLog)

    # Áp dụng bộ lọc nếu có
    if action:
        query = query.filter(AuditLog.action == action)
    if target_machine_id:
        query = query.filter(AuditLog.target_machine_id == target_machine_id)

    # Đếm tổng số bản ghi sau khi lọc (trước khi phân trang)
    total = query.count()

    # Sắp xếp mới nhất lên đầu, rồi phân trang
    logs = (
        query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return AuditLogListResponse(total=total, logs=logs)
