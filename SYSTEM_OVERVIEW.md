# System Overview – Remote Control System

> File này mô tả chi tiết kiến trúc, công nghệ, giao thức giao tiếp và cấu trúc mã nguồn của toàn bộ hệ thống. Mục đích: dùng làm tài liệu tham chiếu khi phát triển, và làm ngữ cảnh (context) khi trao đổi với AI.

---

## 1. Mục tiêu hệ thống

Xây dựng hệ thống cho phép một **Web App** điều khiển từ xa nhiều **máy tính Windows**, thông qua một **Gateway** trung gian. Hệ thống có 8 module chức năng: Applications, Processes, Screenshot, Live Screen, Key Logger, File Download, Webcam, Power Control. Mỗi module trên máy bị điều khiển đều yêu cầu cơ chế cấp quyền (permission).

---

## 2. Kiến trúc tổng thể

```
┌─────────────┐        HTTP/REST         ┌──────────────────┐
│   Browser   │ ───────────────────────► │   Web Backend     │
│  (React)    │ ◄─────────────────────── │   (FastAPI)       │
└─────────────┘                          └─────────┬─────────┘
       │                                            │
       │  WebSocket (real-time:                    │ WebSocket
       │  Live Screen, Key Logger,                 │ (lệnh điều khiển +
       │  Webcam stream)                           │  kết quả)
       │                                            ▼
       │                                  ┌──────────────────┐
       └─────────────────────────────────►│     Gateway       │
                                           │  (Python asyncio  │
                                           │   + websockets)   │
                                           └─────────┬─────────┘
                                                      │ WebSocket
                                                      ▼
                                           ┌──────────────────┐
                                           │  Windows Client   │
                                           │  (C# WPF)         │
                                           │  - Modules        │
                                           │  - Permission     │
                                           └──────────────────┘
```

**3 thành phần độc lập, giao tiếp qua mạng:**

| Thành phần | Vai trò | Công nghệ |
|---|---|---|
| Web App | Giao diện người dùng, xác thực, điều phối lệnh | Backend: FastAPI (Python) / Frontend: React (Vite) |
| Gateway | Trung gian kết nối, định tuyến message | Python (asyncio + websockets) |
| Client App | Cài trên máy Windows bị điều khiển, thực thi lệnh | C# WPF (.NET) |

---

## 3. Luồng kết nối & xác thực

1. **Client App khởi động** → mở kết nối WebSocket đến Gateway (`ws://<gateway-host>:8765`)
2. Gateway gán `machine_id` cho client, lưu vào `ConnectionManager`
3. Gateway thông báo cho Web Backend (qua WebSocket riêng hoặc kênh nội bộ) rằng có máy mới online
4. **Người dùng đăng nhập Web App** (username/password) → Backend trả về JWT token
5. Frontend dùng token cho các request REST và kết nối WebSocket đến Gateway (qua Backend hoặc trực tiếp – xem mục 6)
6. Frontend gọi `GET /api/machines` → Backend hỏi Gateway danh sách máy online → trả về Frontend
7. Người dùng chọn máy + module → gửi lệnh

---

## 4. Giao thức giao tiếp (Message Protocol)

Tất cả message giữa Web App ↔ Gateway ↔ Client App đều ở dạng **JSON qua WebSocket**.

### 4.1 Cấu trúc message chung

```json
{
  "type": "string",        // loại message, xem bảng bên dưới
  "machine_id": "string",  // ID máy đích/nguồn (bắt buộc với lệnh điều khiển)
  "payload": { }           // dữ liệu kèm theo, tùy theo "type"
}
```

### 4.2 Bảng các loại message (`type`)

#### Hệ thống / kết nối

| type | Chiều | Mô tả |
|---|---|---|
| `register` | Client → Gateway | Client đăng ký khi kết nối, gửi kèm `MachineInfo` (tên máy, IP, OS) |
| `machine_online` | Gateway → Web | Thông báo máy mới online |
| `machine_offline` | Gateway → Web | Thông báo máy ngắt kết nối |
| `permission_request` | Gateway → Client | Yêu cầu hỏi quyền người dùng cho một module |
| `permission_response` | Client → Gateway | Phản hồi Allow/Deny từ người dùng |

#### Module: Applications

| type | Chiều | Payload |
|---|---|---|
| `applications_list_request` | Web → Client | `{}` |
| `applications_list_result` | Client → Web | `{ "apps": [{ "name", "pid", "title" }] }` |
| `applications_open` | Web → Client | `{ "app_path": "string" }` |
| `applications_close` | Web → Client | `{ "pid": int }` |

#### Module: Processes

| type | Chiều | Payload |
|---|---|---|
| `processes_list_request` | Web → Client | `{}` |
| `processes_list_result` | Client → Web | `{ "processes": [{ "pid", "name", "cpu_percent", "queue" }] }` |

#### Module: Screenshot

| type | Chiều | Payload |
|---|---|---|
| `screenshot_request` | Web → Client | `{}` |
| `screenshot_result` | Client → Web | `{ "image_base64": "string" }` |

#### Module: Live Screen

| type | Chiều | Payload |
|---|---|---|
| `live_screen_start` | Web → Client | `{}` |
| `live_screen_stop` | Web → Client | `{}` |
| `live_screen_frame` | Client → Web | `{ "image_base64": "string", "timestamp": "..." }` (gửi liên tục) |
| `live_screen_input` | Web → Client | `{ "event": "mouse|keyboard", "data": {...} }` (điều khiển ngược lại) |

#### Module: Key Logger

| type | Chiều | Payload |
|---|---|---|
| `keylogger_start` | Web → Client | `{}` |
| `keylogger_stop` | Web → Client | `{}` |
| `keylogger_data` | Client → Web | `{ "key": "string", "timestamp": "HH:mm:ss" }` (stream real-time, không lưu DB) |

#### Module: File Download

| type | Chiều | Payload |
|---|---|---|
| `file_list_request` | Web → Client | `{ "path": "string" }` |
| `file_list_result` | Client → Web | `{ "items": [{ "name", "is_dir", "size" }] }` |
| `file_download_request` | Web → Client | `{ "path": "string" }` |
| `file_download_chunk` | Client → Web | `{ "chunk_base64": "string", "is_last": bool }` |

#### Module: Webcam

| type | Chiều | Payload |
|---|---|---|
| `webcam_start` | Web → Client | `{}` (kích hoạt permission popup) |
| `webcam_stop` | Web → Client | `{}` |
| `webcam_frame` | Client → Web | `{ "image_base64": "string" }` (stream liên tục) |

#### Module: Power Control

| type | Chiều | Payload |
|---|---|---|
| `power_shutdown` | Web → Client | `{}` (kích hoạt permission popup) |
| `power_sleep` | Web → Client | `{}` (kích hoạt permission popup) |
| `power_result` | Client → Web | `{ "success": bool, "message": "string" }` |

### 4.3 Cơ chế Permission

- Mỗi lệnh thuộc các module nhạy cảm (tất cả 8 module hiện tại) trước khi thực thi sẽ kiểm tra `PermissionService` trên Client App:
  - **Always Allow** → thực thi ngay, gửi `*_result`
  - **Always Deny** → trả về lỗi permission ngay, không hiện popup
  - **Always Ask** → gửi `permission_request` hiện popup, chờ `permission_response` từ người dùng rồi mới thực thi hoặc từ chối

---

## 5. Web App

### 5.1 Backend (FastAPI – Python)

```
web-app/backend/
├── main.py                  # Entry point, khai báo app + router
├── requirements.txt
├── routers/                 # API endpoints theo nhóm chức năng
│   ├── auth.py              # POST /api/auth/login, /logout
│   ├── machines.py          # GET /api/machines, /api/machines/{id}
│   └── modules.py           # Endpoints cho 8 module (REST cho action không real-time)
├── core/
│   ├── config.py            # Settings: SECRET_KEY, GATEWAY_WS_URL, ...
│   ├── security.py          # JWT: create_access_token, verify_token
│   └── gateway_client.py     # Kết nối/giao tiếp với Gateway qua WebSocket
└── api/                      # (thư mục dự phòng, có thể gộp với routers/)
```

**Vai trò chính:**
- Xác thực người dùng (JWT)
- Expose REST API cho Frontend (CRUD trạng thái, lệnh không cần real-time: mở app, lấy danh sách process, chụp screenshot, shutdown...)
- Giữ kết nối WebSocket đến Gateway để: nhận danh sách máy online/offline, forward lệnh, nhận kết quả
- Forward các luồng real-time (Live Screen, Key Logger, Webcam) đến Frontend qua WebSocket riêng

### 5.2 Frontend (React – Vite)

```
web-app/frontend/
├── package.json
├── index.html
└── src/
    ├── main.jsx              # Entry point
    ├── App.jsx               # Định nghĩa route: /login, /dashboard, /machine/:id
    ├── pages/
    │   ├── LoginPage.jsx      # Form đăng nhập
    │   ├── DashboardPage.jsx  # Danh sách máy (online/offline), chọn nhiều máy
    │   └── MachinePage.jsx    # Trang điều khiển 1 máy, chứa tabs cho 8 module
    ├── components/
    │   ├── modules/           # 1 component cho mỗi module
    │   │   ├── Applications.jsx
    │   │   ├── Processes.jsx
    │   │   ├── Screenshot.jsx
    │   │   ├── LiveScreen.jsx
    │   │   ├── KeyLogger.jsx
    │   │   ├── FileDownload.jsx
    │   │   ├── Webcam.jsx
    │   │   └── PowerControl.jsx
    │   └── shared/
    │       ├── MachineList.jsx   # Danh sách máy dùng chung
    │       └── ModulePanel.jsx   # Khung chứa module, dùng trong MachinePage
    ├── services/
    │   ├── api.js             # Gọi REST API (axios), có authService/machineService/moduleService
    │   └── websocket.js        # Kết nối WebSocket cho real-time stream
    └── hooks/
        └── useWebSocket.js     # Custom hook quản lý kết nối WebSocket trong component
```

**Vai trò chính:**
- Đăng nhập, lưu JWT
- Hiển thị danh sách máy, trạng thái online/offline
- Chọn 1 hoặc nhiều máy → gửi lệnh điều khiển
- Hiển thị kết quả từng module (ảnh, danh sách process, log keylogger real-time, video webcam/live screen)

---

## 6. Gateway (Python – asyncio + websockets)

```
gateway/
├── main.py                       # Entry point: khởi động WebSocket server (port 8765)
├── requirements.txt
├── core/
│   └── connection_manager.py     # Quản lý kết nối: machines{}, webapp connection
└── handlers/
    └── message_handler.py         # Phân loại & điều phối message theo "type"
```

**Vai trò chính:**
- Lắng nghe kết nối WebSocket từ:
  - Nhiều **Client App** (mỗi máy Windows một kết nối)
  - **Web Backend** (một kết nối, đóng vai trò điều phối trung tâm)
- `ConnectionManager`:
  - `register()` / `unregister()`: thêm/xóa máy, sinh `machine_id`
  - `send_to_machine(machine_id, message)`: forward lệnh từ Web đến đúng Client
  - `send_to_webapp(message)`: forward kết quả/stream từ Client về Web
  - `get_online_machines()`: trả danh sách máy đang online
- `message_handler.py`: nhận message JSON, dựa vào `type` để quyết định forward đi đâu (Web hay Client cụ thể)

**Lưu ý thiết kế:** Gateway không xử lý logic nghiệp vụ (business logic), chỉ định tuyến (routing) message. Toàn bộ logic nghiệp vụ nằm ở Web Backend (điều phối) và Client App (thực thi).

---

## 7. Client App (C# WPF)

```
client-app/RemoteControlClient/
├── App.xaml / App.xaml.cs        # Entry point, khởi tạo GatewayService khi start
├── Models/
│   ├── MachineInfo.cs            # Thông tin máy: MachineId, MachineName, IpAddress, OsVersion
│   └── CommandMessage.cs         # Cấu trúc message: Type, MachineId, Payload
├── Services/
│   ├── GatewayService.cs         # Kết nối WebSocket đến Gateway, gửi/nhận message
│   └── PermissionService.cs      # Quản lý trạng thái permission (AlwaysAsk/Allow/Deny)
├── Modules/                       # Mỗi module 1 class, implement ExecuteAsync(payload)
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

**Vai trò chính:**
- Kết nối và duy trì kết nối WebSocket đến Gateway (tự động reconnect nếu mất kết nối)
- Nhận `CommandMessage` từ Gateway → `GatewayService.OnMessageReceived()` điều phối đến đúng Module theo `Type`
- Mỗi Module:
  - Kiểm tra `PermissionService.RequestPermissionAsync(moduleName)` trước khi thực thi
  - Thực thi tác vụ thực tế (dùng `System.Diagnostics`, `System.Drawing`, Win32 API, `pythonnet`/native libs nếu cần cho keylogger/webcam...)
  - Gửi kết quả về Gateway qua `GatewayService.SendAsync()`
- `PermissionSettingsWindow`: UI cho người dùng cấu hình trước (Always Ask / Allow / Deny) cho từng module
- `PermissionPopupWindow`: hiện khi có `permission_request` và module đang ở chế độ Always Ask

---

## 8. Bảng tổng hợp 8 module

| # | Module | Web action | Client thực thi | Cần permission |
|---|---|---|---|---|
| 1 | Applications | Liệt kê / mở / đóng app | `Process.GetProcesses()`, `Process.Start()`, `Process.Kill()` | ✅ |
| 2 | Processes | Liệt kê tiến trình + CPU% + Queue | `PerformanceCounter`, `Process` | ✅ |
| 3 | Screenshot | Chụp 1 ảnh màn hình | `System.Drawing.Graphics.CopyFromScreen` | ✅ |
| 4 | Live Screen | Stream màn hình + điều khiển chuột/bàn phím | Capture loop + `SendInput` Win32 API | ✅ |
| 5 | Key Logger | Bật/tắt, xem log real-time | Low-level keyboard hook (`SetWindowsHookEx`) | ✅ |
| 6 | File Download | Duyệt thư mục, tải file | `Directory.GetFiles`, `File.ReadAllBytes` (chunked) | ✅ |
| 7 | Webcam | Stream webcam | `AForge.Video`/`OpenCvSharp` | ✅ |
| 8 | Power Control | Shutdown / Sleep | `Process.Start("shutdown", ...)` | ✅ |

---

## 9. Công nghệ sử dụng (tóm tắt)

| Thành phần | Ngôn ngữ | Framework / Thư viện chính |
|---|---|---|
| Web Backend | Python | FastAPI, websockets, python-jose (JWT), passlib |
| Web Frontend | JavaScript | React, Vite, React Router, Axios |
| Gateway | Python | asyncio, websockets |
| Client App | C# (.NET) | WPF, System.Net.WebSockets (hoặc thư viện tương đương) |

---

## 10. Các điểm cần hoàn thiện (TODO tổng quan)

- [ ] Cơ chế xác thực JWT đầy đủ (login, refresh, middleware bảo vệ route)
- [ ] `gateway_client.py`: kết nối Backend ↔ Gateway, định nghĩa kênh điều khiển vs kênh stream
- [ ] `connection_manager.py`: sinh `machine_id`, lưu trạng thái, broadcast online/offline
- [ ] `message_handler.py`: implement điều phối đầy đủ theo bảng mục 4.2
- [ ] Frontend: kết nối WebSocket cho Live Screen / Key Logger / Webcam, render real-time
- [ ] Client App: implement từng Module theo Win32 API tương ứng
- [ ] Client App: `PermissionService` đọc/ghi config từ file (JSON/XML)
- [ ] Bảo mật: mã hóa kết nối (WSS/TLS), xác thực Client App với Gateway (tránh máy lạ kết nối vào)
