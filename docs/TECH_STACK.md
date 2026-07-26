# Tech Stack

## Overview

Tài liệu này mô tả các công nghệ, thư viện và quy ước được sử dụng trong dự án.

---

# Technology Stack

| Thành phần    | Công nghệ                   |
| ------------- | --------------------------- |
| Frontend      | React + Vite                |
| Backend       | FastAPI (Python)            |
| Gateway       | Python asyncio + websockets |
| Client App    | Python (tkinter)            |
| Database      | SQLite                      |
| Communication | WebSocket + JSON            |

---

# Main Libraries

## Backend / Gateway

- FastAPI
- Uvicorn
- websockets
- PyJWT
- asyncio
- pydantic

## Client App

- Python 3.11+
- `tkinter` — giao diện Permission Dialog (built-in)
- `websockets` — kết nối WebSocket tới Gateway
- `Pillow` (PIL) — chụp ảnh màn hình (screenshot, live screen)
- `mss` — screen capture hiệu năng cao cho live screen
- `opencv-python` (cv2) — capture webcam
- `pynput` — keylogger (hook bàn phím và chuột)
- `psutil` — lấy thông tin process và application
- `ctypes` / `pywin32` — lock screen, power control (shutdown, restart, sleep)
- `python-dotenv` — load cấu hình từ `.env`

## Frontend

- React 18
- React Router v6
- Axios
- TailwindCSS

---

# Project Structure

```text
project/
│
├── client-app/
│   └── remote_control_client/
│
├── gateway/
│
├── web-app/
│   ├── backend/
│   └── frontend/
│
├── docs/
│
└── README.md
```

---

# Coding Conventions

## Naming

| Scope | Convention | Ví dụ |
|---|---|---|
| File (Python) | snake_case | `auth_manager.py` |
| File (JS/TS) | camelCase | `machineService.ts` |
| Class | PascalCase | `MessageRouter` |
| Function / Method (Python) | snake_case | `validate_token()` |
| Variable (Python) | snake_case | `machine_id` |
| Variable (JS/TS) | camelCase | `machineId` |

## Communication

- Tất cả message sử dụng JSON.
- Tất cả field trong JSON message dùng **camelCase**.
- Message type dùng quy tắc `module.action` (xem `communication_protocol.md`).

---

# Logging

Mỗi thành phần có logger riêng.

- Backend Log
- Gateway Log
- Client App Log

---

# Configuration

Các thông tin cấu hình được lưu trong file `.env`.

Ví dụ:

- Database
- JWT Secret
- Gateway Address
- Machine Secret

---

# Development Principles

- Module độc lập.
- Không hard-code cấu hình.
- Tách Business Logic và Communication.
- Ưu tiên Async I/O.
- Dễ mở rộng module mới.

---

# Future Improvements

Có thể bổ sung:

- HTTPS / WSS
- PostgreSQL
- Docker
- RBAC
- Multi-user
- Remote Update Client App

---

# Related Documents

- project_requirements.md
- system_specification.md
- system_architecture.md
- communication_protocol.md
- security_design.md
- **api_contract.md** — message contract và payload spec
