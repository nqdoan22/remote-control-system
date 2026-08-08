# Remote Control System

Hệ thống điều khiển máy tính từ xa gồm 3 thành phần độc lập. Chi tiết từng thành phần xem ở README riêng: [gateway/README.md](gateway/README.md), [client-app/README.md](client-app/README.md), [web-app/README.md](web-app/README.md).

## 📦 Release & Source code

- **Bản chạy (GitHub Release):** https://github.com/nqdoan22/remote-control-system/releases — tải `RemoteControlClient-win64.zip` để chạy Client App không cần cài Python.
- **Source code (Google Drive):** _`<DÁN LINK GOOGLE DRIVE Ở ĐÂY>`_
- **Cách tạo bản release:** xem [docs/RELEASE_GUIDE.md](docs/RELEASE_GUIDE.md). Đóng gói Client App thành `.exe`:

  ```powershell
  cd client-app
  powershell -ExecutionPolicy Bypass -File build_exe.ps1
  ```

## Cấu trúc

```
remote-control-system/
├── web-app/
│   ├── backend/        # Python FastAPI
│   └── frontend/       # React (Vite)
├── gateway/            # Python WebSocket Gateway
└── client-app/         # Python PyQt6 Windows Client
```

## Khởi động

### 1. Gateway

```bash
cd gateway
pip install -r requirements.txt
python main.py
```

### 2. Web App Backend

```bash
cd web-app/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Web App Frontend

```bash
cd web-app/frontend
npm install
npm run dev
```

### 4. Client App

Client App là ứng dụng Python PyQt6 (không phải project .NET). `requirements.txt` hiện đang trống nên cần cài trực tiếp các package được dùng trong mã nguồn:

```bash
cd client-app
pip install PyQt6 websockets psutil pynput mss Pillow opencv-python pydantic pydantic-settings
python main.py
```

Chi tiết xem [client-app/README.md](client-app/README.md).

## Kiến trúc

```
[Browser - React] <-HTTP/WS-> [FastAPI Backend] <-WS-> [Gateway] <-WS-> [Python PyQt6 Client]
```

## Tài liệu khác

- [docs/system_architecture.md](docs/system_architecture.md): kiến trúc hệ thống.
- [docs/communication_protocol.md](docs/communication_protocol.md): giao thức giao tiếp WebSocket.
- [docs/api_contract.md](docs/api_contract.md): API contract.
- [docs/security_design.md](docs/security_design.md): thiết kế bảo mật.
- [docs/project_requirements.md](docs/project_requirements.md): yêu cầu dự án.
- [docs/system_specification.md](docs/system_specification.md): đặc tả hệ thống.
- [docs/TECH_STACK.md](docs/TECH_STACK.md): tech stack.
