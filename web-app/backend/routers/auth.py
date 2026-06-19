from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from core import security

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Giả lập tài khoản admin duy nhất trong hệ thống để test
MOCK_ADMIN_DB = {
    "username": "admin",
    "role": "super_admin"
}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint xử lý đăng nhập bằng chuỗi thô để phục vụ mục đích test nhanh giao diện.
    """
    username = form_data.username
    password = form_data.password

    # 1. Kiểm tra username
    if username != MOCK_ADMIN_DB["username"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác"
        )

    # 2. So sánh chuỗi thô trực tiếp để tránh lỗi so khớp salt/hash khi reload
    if password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác"
        )

    # 3. Tạo token nếu đúng
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
    """
    return {"status": "success", "message": f"User {current_user['username']} logged out thành công từ Client."}