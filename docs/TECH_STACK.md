# Tech Stack & Cấu trúc Mã nguồn – Remote Control System

> Tài liệu này mô tả công nghệ, framework, thư viện và cấu trúc thư mục cụ thể của từng thành phần. Đọc cùng với `SYSTEM_SPEC.md` để hiểu đầy đủ hệ thống.

---

## 1. Tổng quan công nghệ

| Thành phần | Ngôn ngữ | Framework / Thư viện chính |
|---|---|---|
| Web Backend | Python | FastAPI, websockets, python-jose (JWT), passlib |
| Web Frontend | JavaScript | React, Vite, React Router, Axios |
| Gateway | Python | asyncio, websockets |
| Client App | C# (.NET) | WPF, System.Net.WebSockets |

---

## 2. Web App – Backend (FastAPI / Python)

### Cấu trúc thư mục

```
web-app/backend/
├── main.py                   # Entry point, khai báo app + router
├── requirements.txt
├── routers/
│   ├── auth.py               # POST /api/auth/login, /logout
│   ├── machines.py           # GET /api/machines, /api/machines/{id}
│   └── modules.py            # Endpoints cho 8 module (REST cho action không real-time)
├── core/
│   ├── config.py             # Settings: SECRET_KEY, GATEWAY_WS_URL, ...
│   ├── security.py           # JWT: create_access_token, verify_token
│   └── gateway_client.py     # Kết nối/giao tiếp với Gateway qua WebSocket
└── api/                      # (thư mục dự phòng, có thể gộp với routers/)
```

### Vai trò chính

- Xác thực người dùng bằng JWT (JSON Web Token).
- Expose REST API cho Frontend: CRUD trạng thái, các lệnh không cần real-time (mở app, lấy danh sách process, chụp screenshot, shutdown...).
- Duy trì kết nối WebSocket đến Gateway để: nhận danh sách máy online/offline, forward lệnh, nhận kết quả.
- Forward các luồng real-time (Live Screen, Key Logger, Webcam) đến Frontend qua WebSocket riêng.

---

## 3. Web App – Frontend (React / Vite)

### Cấu trúc thư mục

```
web-app/frontend/
├── package.json
├── index.html
└── src/
    ├── main.jsx               # Entry point
    ├── App.jsx                # Định nghĩa route: /login, /dashboard, /machine/:id
    ├── pages/
    │   ├── LoginPage.jsx      # Form đăng nhập
    │   ├── DashboardPage.jsx  # Danh sách máy (online/offline), chọn nhiều máy
    │   └── MachinePage.jsx    # Trang điều khiển 1 máy, chứa tabs cho 8 module
    ├── components/
    │   ├── modules/
    │   │   ├── Applications.jsx
    │   │   ├── Processes.jsx
    │   │   ├── Screenshot.jsx
    │   │   ├── LiveScreen.jsx
    │   │   ├── KeyLogger.jsx
    │   │   ├── FileDownload.jsx
    │   │   ├── Webcam.jsx
    │   │   └── PowerControl.jsx
    │   └── shared/
    │       ├── MachineList.jsx    # Danh sách máy dùng chung
    │       └── ModulePanel.jsx    # Khung chứa module, dùng trong MachinePage
    ├── services/
    │   ├── api.js              # Gọi REST API (axios): authService, machineService, moduleService
    │   └── websocket.js        # Kết nối WebSocket cho real-time stream
    └── hooks/
        └── useWebSocket.js     # Custom hook quản lý kết nối WebSocket trong component
```

### Vai trò chính

- Đăng nhập, lưu JWT token.
- Hiển thị danh sách máy và trạng thái online/offline.
- Cho phép chọn 1 hoặc nhiều máy để gửi lệnh điều khiển.
- Hiển thị kết quả: ảnh screenshot, danh sách process, log keylogger real-time, video webcam/live screen.

---

## 4. Gateway (Python asyncio + websockets)

### Cấu trúc thư mục

```
gateway/
├── main.py                       # Entry point: khởi động WebSocket server (port 8765)
├── requirements.txt
├── core/
│   └── connection_manager.py     # Quản lý kết nối: machines{}, webapp connection
└── handlers/
    └── message_handler.py        # Phân loại & điều phối message theo "type"
```

### Vai trò chính

- Lắng nghe kết nối WebSocket từ nhiều Client App và từ Web Backend.
- `ConnectionManager`:
  - `register()` / `unregister()`: thêm/xóa máy, sinh `machine_id`.
  - `send_to_machine(machine_id, message)`: forward lệnh từ Web đến đúng Client.
  - `send_to_webapp(message)`: forward kết quả/stream từ Client về Web.
  - `get_online_machines()`: trả danh sách máy đang online.
- `message_handler.py`: nhận message JSON, dựa vào `type` để quyết định forward đi đâu.

---

## 5. Client App (C# WPF / .NET)

### Cấu trúc thư mục

```
client-app/RemoteControlClient/
├── App.xaml / App.xaml.cs        # Entry point, khởi tạo GatewayService khi start
├── Models/
│   ├── MachineInfo.cs            # MachineId, MachineName, IpAddress, OsVersion
│   └── CommandMessage.cs         # Cấu trúc message: Type, MachineId, Payload
├── Services/
│   ├── GatewayService.cs         # Kết nối WebSocket đến Gateway, gửi/nhận message
│   └── PermissionService.cs      # Quản lý trạng thái permission (AlwaysAsk/Allow/Deny)
├── Modules/
│   ├── ApplicationsModule.cs
│   ├── ProcessesModule.cs
│   ├── ScreenshotModule.cs
│   ├── LiveScreenModule.cs
│   ├── KeyLoggerModule.cs
│   ├── FileDownloadModule.cs
│   ├── WebcamModule.cs
│   └── PowerControlModule.cs
└── Views/
    ├── MainWindow.xaml(.cs)              # Màn hình chính: trạng thái kết nối
    ├── PermissionSettingsWindow.xaml     # Cấu hình quyền cho 8 module
    └── PermissionPopupWindow.xaml        # Popup xin phép real-time
```

### Vai trò chính

- Kết nối và duy trì WebSocket đến Gateway; tự động reconnect khi mất kết nối.
- `GatewayService.OnMessageReceived()` điều phối lệnh đến đúng Module theo `Type`.
- Mỗi Module: kiểm tra `PermissionService` → thực thi → gửi kết quả về qua `GatewayService.SendAsync()`.
- `PermissionSettingsWindow`: UI cấu hình quyền trước (Always Ask / Allow / Deny) cho từng module.
- `PermissionPopupWindow`: hiện khi `permission_request` được nhận và module ở chế độ Always Ask.

### Thư viện thực thi theo module

| Module | API / Thư viện |
|---|---|
| Applications | `System.Diagnostics.Process` |
| Processes | `System.Diagnostics.Process`, `PerformanceCounter` |
| Screenshot | `System.Drawing.Graphics.CopyFromScreen` |
| Live Screen | Capture loop + `SendInput` (Win32 API) |
| Key Logger | Low-level keyboard hook: `SetWindowsHookEx` (Win32 API) |
| File Download | `System.IO.Directory`, `System.IO.File` (chunked) |
| Webcam | `AForge.Video` hoặc `OpenCvSharp` |
| Power Control | `Process.Start("shutdown", ...)` |
