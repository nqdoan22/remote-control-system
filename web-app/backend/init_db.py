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
    logger.info("Dang khoi tao cac bang CSDL SQLite...")
    
    # 1. Tạo tất cả các bảng dựa trên định nghĩa trong models.py
    Base.metadata.create_all(bind=engine)
    logger.info("Cac bang (users, machines, audit_logs) da duoc tao thanh cong.")

    # 2. Khởi tạo phiên làm việc để kiểm tra / tạo Admin mặc định
    db = SessionLocal()
    try:
        # Kiểm tra xem đã có user nào tên 'admin' chưa
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if not existing_admin:
            logger.info("Chua tim thay tai khoan Admin. Dang tao tai khoan Admin mac dinh...")
            
            default_admin = User(
                username="admin",
                hashed_password=hash_password("admin123"), # Mật khẩu mặc định: admin123
                role="Admin"
            )
            db.add(default_admin)
            db.commit()
            db.refresh(default_admin)
            
            logger.info("Tao tai khoan thanh cong! Username: 'admin' | Password: 'admin123'")
        else:
            logger.info("Tai khoan Admin da ton tai. Bo qua buoc tao mac dinh.")
            
    except Exception as e:
        logger.error(f"Loi khi khoi tao du lieu mac dinh: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()