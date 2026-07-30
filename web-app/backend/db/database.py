"""
===============================================================================
FILE: web-app/backend/db/database.py
PURPOSE: Thiết lập cấu hình kết nối CSDL (SQLite) sử dụng ORM SQLAlchemy.
ARCHITECTURE ROLE: 
  - Đóng vai trò là "Cầu nối CSDL" tầng DB.
  - Khởi tạo Engine, SessionFactory và Base class cho các ORM Models.
  - Cung cấp hàm get_db() làm Dependency Injection cho FastAPI Routers.
===============================================================================
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# 1. Khởi tạo Engine kết nối tới SQLite từ DATABASE_URL trong config.py
# check_same_thread=False là bắt buộc đối với SQLite khi dùng trong FastAPI (đa luồng)
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 2. Khởi tạo SessionLocal - Nhà máy sản xuất các phiên làm việc với CSDL (Database Sessions)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Class Base - Lớp cơ sở mà tất cả các bảng (Models) trong db/models.py sẽ kế thừa
Base = declarative_base()


# 4. Dependency function cấp phát Database Session cho các API Router
def get_db():
    """
    Hàm Dependency cấp phát một phiên kết nối CSDL (DB Session) cho mỗi request API.
    Sau khi API xử lý xong, session sẽ tự động được đóng lại (close) để giải phóng tài nguyên.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()