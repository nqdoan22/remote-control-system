# web-app/backend/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# ------------------------------------------------------------------
# KHỞI TẠO ENGINE KẾT NỐI
# ------------------------------------------------------------------
# check_same_thread=False là BẮT BUỘC đối với SQLite trong FastAPI
# vì FastAPI xử lý các request bất đồng bộ trên nhiều thread khác nhau.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ------------------------------------------------------------------
# KHỞI TẠO SESSION FACTORY
# ------------------------------------------------------------------
# SessionLocal đại diện cho một phiên làm việc (transaction) với Database
SessionLocal = sessionmaker(
    autocommit=False, # Không tự động commit để Admin chủ động kiểm soát giao dịch
    autoflush=False,  # Không tự động đẩy thay đổi xuống DB trước khi query
    bind=engine
)

# ------------------------------------------------------------------
# BASE CLASS CHO CÁC MODELS
# ------------------------------------------------------------------
# Tất cả các Bảng (Models) trong db/models.py sẽ kế thừa từ Base class này
Base = declarative_base()

# ------------------------------------------------------------------
# DEPENDENCY INJECTION CHO FASTAPI ROUTERS
# ------------------------------------------------------------------
def get_db():
    """
    Hàm phụ trợ (Dependency) dùng trong các API Endpoints.
    Tự động mở Session khi có request và đảm bảo ĐÓNG Session sau khi xử lý xong,
    giúp tránh tình trạng rò rỉ kết nối CSDL (Connection Leak).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()