# web-app/backend/init_db.py
import logging
import bcrypt
from db.database import engine, SessionLocal, Base
from db.models import User

# Cấu hình log
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [INIT DB] - %(levelname)s - %(message)s")
logger = logging.getLogger("InitDB")

def hash_password(password: str) -> str:
    """
    Hàm băm mật khẩu trực tiếp bằng thư viện bcrypt nguyên bản.
    Giúp tránh hoàn toàn lỗi bất tương thích của passlib trên các phiên bản Python mới.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def init_db():
    """
    Khởi tạo CSDL SQLite và tài khoản Admin mặc định nếu chưa tồn tại.
    """
    logger.info("🛠️ Đang khởi tạo các bảng CSDL SQLite...")
    
    # 1. Tạo tất cả các bảng dựa trên định nghĩa trong models.py
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Các bảng (users, machines, audit_logs) đã được tạo thành công.")

    # 2. Khởi tạo phiên làm việc để kiểm tra / tạo Admin mặc định
    db = SessionLocal()
    try:
        # Kiểm tra xem đã có user nào tên 'admin' chưa
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if not existing_admin:
            logger.info("🔑 Chưa tìm thấy tài khoản Admin. Đang tạo tài khoản Admin mặc định...")
            
            default_admin = User(
                username="admin",
                hashed_password=hash_password("admin123"), # Mật khẩu mặc định: admin123
                role="Admin"
            )
            db.add(default_admin)
            db.commit()
            db.refresh(default_admin)
            
            logger.info("🎉 Tạo tài khoản thành công! Username: 'admin' | Password: 'admin123'")
        else:
            logger.info("ℹ️ Tài khoản Admin đã tồn tại. Bỏ qua bước tạo mặc định.")
            
    except Exception as e:
        logger.error(f"❌ Lỗi khi khởi tạo dữ liệu mặc định: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()