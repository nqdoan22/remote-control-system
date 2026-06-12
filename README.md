# Remote Control System

Hệ thống điều khiển máy tính từ xa gồm 3 thành phần độc lập.

## Cấu trúc

```
remote-control-system/
├── web-app/
│   ├── backend/        # Python FastAPI
│   └── frontend/       # React (Vite)
├── gateway/            # Python WebSocket Gateway
└── client-app/         # C# WPF Windows Client
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

Mở `client-app/RemoteControlClient.sln` bằng Visual Studio và build.

## Kiến trúc

```
[Browser - React] ←HTTP/WS→ [FastAPI Backend] ←WS→ [Gateway] ←WS→ [C# WPF Client]
```
