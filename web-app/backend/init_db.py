"""
===============================================================================
FILE: web-app/backend/init_db.py
PURPOSE: Script khởi tạo Cơ sở dữ liệu và cấy dữ liệu mẫu (Seeding Data).
ARCHITECTURE ROLE: 
  - Khởi tạo các Bảng CSDL thật dựa trên cấu hình ORM Models.
  - Tự động tạo sẵn 1 tài khoản Super Admin mặc định nếu CSDL chưa có dữ liệu.
  - Chạy độc lập 1 lần khi triển khai hoặc tích hợp vào Lifespan của FastAPI.
===============================================================================
"""

import logging
from db.database import engine, SessionLocal, Base
from db.models import User, Machine
from core.security import get_password_hash
from core.config import settings

# Thiết lập ghi log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InitDB")


def init_db():
    """
    Hàm khởi tạo CSDL và cấy tài khoản Admin mặc định.
    """
    logger.info("🛠 Đang tạo các Bảng trong CSDL (nếu chưa tồn tại)...")
    
    # 🌟 HÀM CỐT LÕI 1: Quét tất cả Class kế thừa Base trong models.py để tạo Bảng trong SQLite
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tạo các Bảng CSDL thành công!")

    # Mở một phiên làm việc với CSDL
    db = SessionLocal()

    try:
        # 🌟 HÀM CỐT LÕI 2: Kiểm tra tài khoản Admin mặc định đã tồn tại chưa
        default_admin_username = "admin"
        admin_user = db.query(User).filter(User.username == default_admin_username).first()

        if not admin_user:
            logger.info(f"🔑 Không tìm thấy tài khoản '{default_admin_username}'. Đang khởi tạo tài khoản mặc định...")
            
            # Mật khẩu mặc định lấy từ settings hoặc admin123
            raw_password = getattr(settings, "FIRST_SUPERUSER_PASSWORD", "admin123")
            
            # Băm mật khẩu bằng hàm get_password_hash từ core/security.py
            hashed_pwd = get_password_hash(raw_password)

            # Tạo đối tượng User mới
            new_admin = User(
                username=default_admin_username,
                hashed_password=hashed_pwd,
                role="admin",
                is_active=True
            )

            # Lưu vào CSDL
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)

            logger.info(f"🎉 Đã khởi tạo thành công tài khoản mặc định:")
            logger.info(f"   👉 Username: {default_admin_username}")
            logger.info(f"   👉 Password: {raw_password}")
        else:
            logger.info(f"ℹ️ Tài khoản '{default_admin_username}' đã tồn tại trong CSDL. Bỏ qua bước khởi tạo user.")

    except Exception as e:
        logger.error(f"❌ Lỗi khi khởi tạo dữ liệu CSDL: {e}")
        db.rollback()
    finally:
        # Luôn đóng session sau khi thao tác xong
        db.close()


if __name__ == "__main__":
    # Cho phép chạy file trực tiếp bằng câu lệnh: python init_db.py
    logger.info("🚀 Bắt đầu quá trình khởi tạo CSDL...")
    init_db()
    logger.info("✨ Hoàn tất quá trình khởi tạo CSDL!")