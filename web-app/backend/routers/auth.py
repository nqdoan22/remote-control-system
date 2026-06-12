from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    # TODO: Xác thực username/password, trả về JWT token
    pass

@router.post("/logout")
def logout():
    # TODO: Hủy token
    pass
