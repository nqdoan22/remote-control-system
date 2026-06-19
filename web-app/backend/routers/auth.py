from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from core import security

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Giả lập tài khoản admin duy nhất trong hệ thống để test
# Mật khẩu gốc là "admin123", đã được băm sẵn bằng bcrypt
MOCK_ADMIN_DB = {
    "username": "admin",
    "hashed_password": security.hash_password("admin123"), # Hoặc điền chuỗi hash cố định vào đây
    "role": "super_admin"
}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint xử lý đăng nhập. 
    Sử dụng OAuth2PasswordRequestForm để tương thích hoàn hảo với Swagger UI của FastAPI.
    """
    username = form_data.username
    password = form_data.password

    # 1. Kiểm tra username
    if username != MOCK_ADMIN_DB["username"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác"
        )

    # 2. Kiểm tra mật khẩu bằng hàm verify đã viết ở security.py
    if not security.verify_password(password, MOCK_ADMIN_DB["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác"
        )

    # 3. Tạo token nếu đúng (Lưu username vào trường 'sub' theo chuẩn JWT)
    access_token = security.create_access_token(
        data={"sub": MOCK_ADMIN_DB["username"], "role": MOCK_ADMIN_DB["role"]}
    )

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"username": username, "role": MOCK_ADMIN_DB["role"]}
    }

@router.post("/logout")
def logout(current_user: dict = Depends(security.get_current_user)):
    """
    Endpoint xử lý đăng xuất.
    Vì JWT là Stateless (không lưu trạng thái trên server), việc logout thực chất 
    là Frontend tự xóa token ở phía Client (Cookie/LocalStorage). 
    Endpoint này trả về thông báo thành công.
    """
    return {"status": "success", "message": f"User {current_user['username']} logged out thành công từ Client."}