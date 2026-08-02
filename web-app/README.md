# Web App

Web App gồm 2 phần:

- `backend/`: FastAPI cung cấp REST API, WebSocket `/ws`, xác thực JWT và cầu nối tới Gateway.
- `frontend/`: React + Vite cung cấp giao diện đăng nhập, dashboard và màn hình điều khiển từng máy.

## Kiến trúc

Luồng chính của hệ thống:

`Browser -> FastAPI Backend -> Gateway -> Client App`

Backend tự kết nối tới Gateway bằng WebSocket, sau đó frontend giao tiếp với backend bằng HTTP và WebSocket.

## Backend

### Vai trò

- Xác thực người dùng bằng JWT.
- Lưu và truy vấn dữ liệu máy trạm, nhật ký thao tác và trạng thái kết nối.
- Đóng vai trò cầu nối để đẩy lệnh từ frontend tới Gateway.
- Nhận phản hồi / stream realtime từ Gateway và chuyển về frontend.

### Cổng và điểm vào

- REST API mặc định: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- WebSocket cho frontend: `ws://localhost:8000/ws`

### API chính

REST endpoints:

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/machines/`
- `GET /api/v1/machines/{machine_id}`
- `POST /api/v1/machines/heartbeat`
- `DELETE /api/v1/machines/{machine_id}`
- `POST /api/v1/modules/applications`
- `POST /api/v1/modules/processes`
- `POST /api/v1/modules/screenshot`
- `POST /api/v1/modules/live-screen`
- `POST /api/v1/modules/keylogger`
- `POST /api/v1/modules/file/action`
- `POST /api/v1/modules/file/upload`
- `POST /api/v1/modules/webcam`
- `POST /api/v1/modules/power`

> ⚠️ Frontend hiện gọi thêm `POST /api/v1/auth/change-password` và `GET /api/v1/audit-logs` (xem `frontend/src/services/api.js`), nhưng backend **chưa có router nào xử lý 2 endpoint này** — gọi tới sẽ trả lỗi 404. Đây là API contract chưa khớp giữa 2 phía, cần bổ sung route ở backend hoặc gỡ lời gọi ở frontend.

### Tính năng giao diện

- Đăng nhập admin.
- Xem dashboard danh sách máy và audit logs.
- Xem chi tiết một máy.
- Điều khiển 8 module:
  - Applications
  - Processes
  - Screenshot
  - Live Screen
  - Keylogger
  - File Transfer
  - Webcam
  - Power Control

### Cấu hình môi trường backend

File `backend/core/config.py` đọc biến từ `.env`. Các biến thường dùng:

```env
SECRET_KEY=replace-me
DATABASE_URL=sqlite:///./sql_app.db
GATEWAY_WS_URL=ws://localhost:8765/webapp
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=AdminPass123!
```

Ngoài ra backend còn dùng danh sách CORS mặc định cho `localhost:3000` và `localhost:5173`.

### Cài đặt backend

Tạo và kích hoạt môi trường ảo Python trước khi cài dependencies:

```bash
cd web-app/backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Nếu dùng PowerShell thì kích hoạt bằng:

```powershell
.\.venv\Scripts\Activate.ps1
```

Sau đó cài đặt dependencies:

```bash
cd web-app/backend
pip install -r requirements.txt
```

### Chạy backend

```bash
cd web-app/backend
python main.py
```

Hoặc chạy bằng Uvicorn:

```bash
cd web-app/backend
uvicorn main:app --reload
```

## Frontend

### Vai trò

- Hiển thị màn hình đăng nhập và dashboard.
- Gọi REST API của backend bằng Axios.
- Dùng WebSocket realtime để nhận trạng thái, response và stream dữ liệu.
- Tự động reconnect khi mất kết nối.

### Route chính

- `/login`
- `/dashboard`
- `/machine/:machineId`

### Cấu hình môi trường frontend

Frontend đọc các biến Vite sau:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
```

### Cài đặt frontend

```bash
cd web-app/frontend
npm install
```

### Chạy frontend

```bash
cd web-app/frontend
npm run dev
```

## Luồng hoạt động

1. Admin đăng nhập ở frontend.
2. Frontend lấy JWT từ backend và lưu vào `localStorage`.
3. Frontend gọi REST API để lấy danh sách máy, audit logs và chi tiết máy.
4. Khi mở trang điều khiển máy, frontend kết nối WebSocket tới backend bằng token.
5. Backend chuyển lệnh qua Gateway, Gateway forward xuống client tương ứng.
6. Phản hồi và stream realtime được đẩy ngược về browser.

## Cấu trúc thư mục

```text
web-app/
├── backend/
│   ├── main.py
│   ├── core/
│   ├── db/
│   ├── routers/
│   └── schemas/
└── frontend/
    ├── src/
    │   ├── pages/
    │   ├── components/
    │   │   └── modules/       # 1 component / module (Applications, Processes, ...)
    │   ├── hooks/              # useWebSocket.js, ...
    │   └── services/           # api.js, websocket.js
    └── package.json
```

## Ghi chú

- Backend tự khởi tạo kết nối tới Gateway khi startup.
- Các lệnh nhạy cảm như live screen, webcam, keylogger và power control có thể cần user consent từ máy client.
- Frontend mặc định làm việc với backend tại cổng `8000`.
