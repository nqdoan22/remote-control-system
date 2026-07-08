# Tech Stack

## Overview

Tài liệu này mô tả các công nghệ, thư viện và quy ước được sử dụng trong dự án.

---

# Technology Stack

| Thành phần | Công nghệ |
|------------|-----------|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Gateway | FastAPI + WebSocket + asyncio |
| Agent | Python |
| Database | SQLite |
| Communication | WebSocket + JSON |

---

# Main Libraries

## Backend / Gateway

- FastAPI
- Uvicorn
- websockets
- PyJWT
- asyncio
- pydantic

## Agent

- psutil
- mss
- opencv-python
- pywin32
- pynput
- aiofiles

## Frontend

- React
- React Router
- Axios
- TailwindCSS

---

# Project Structure

```text
project/
│
├── web_app/
│
├── gateway/
│
├── agent/
│
├── docs/
│
└── scripts/
```

---

# Coding Conventions

## Naming

- File: snake_case
- Class: PascalCase
- Function: snake_case
- Variable: snake_case

## Communication

- JSON
- camelCase cho field trong message.

---

# Logging

Mỗi thành phần có logger riêng.

- Backend Log
- Gateway Log
- Agent Log

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
- Remote Update Agent

---

# Related Documents

- project_requirements.md
- system_specification.md
- system_architecture.md
- communication_protocol.md
- security_design.md
