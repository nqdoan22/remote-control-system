# Communication Protocol

## Overview

Tài liệu này mô tả giao thức truyền thông giữa các thành phần trong hệ thống.

Các kết nối bao gồm:

- Web App ↔ Gateway
- Gateway ↔ Client App

Toàn bộ dữ liệu được truyền dưới dạng **JSON** thông qua **WebSocket**.

---

# Communication Model

```text
Administrator
      │
      ▼
   Web App
      │
      │ Request
      ▼
   Gateway
      │
      │ Request
      ▼
    Client App
      │
      │ Response
      ▼
   Gateway
      │
      │ Response
      ▼
   Web App
```

Gateway chỉ thực hiện:

- Authentication
- Authorization
- Routing
- Connection Management

Gateway **không xử lý Business Logic**.

---

# General Message Format

Mọi message trong hệ thống đều sử dụng cùng một cấu trúc.

```json
{
  "messageId": "uuid",
  "type": "process.list",
  "timestamp": 1710000000,
  "source": "gateway",
  "destination": "client-app-01",
  "payload": {}
}
```

---

## Fields

| Field       | Description                       |
| ----------- | --------------------------------- |
| messageId   | Mã định danh duy nhất của message |
| type        | Loại message                      |
| timestamp   | Thời điểm gửi                     |
| source      | Thành phần gửi                    |
| destination | Thành phần nhận                   |
| payload     | Dữ liệu của message               |

---

# Message Types

Hệ thống sử dụng ba loại message.

## Request

Yêu cầu thực hiện một hành động.

Ví dụ:

```json
{
  "type": "process.kill",
  "payload": {
    "pid": 1234
  }
}
```

---

## Response

Phản hồi cho một Request.

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {}
  }
}
```

---

## Event

Thông báo một sự kiện.

Ví dụ:

```json
{
  "type": "heartbeat",
  "payload": {
    "status": "online"
  }
}
```

---

# Message Naming Convention

Tên message sử dụng quy tắc:

```text
module.action
```

Ví dụ:

```text
application.list
application.start
application.stop

process.list
process.kill

screen.screenshot
screen.live.start
screen.live.stop

webcam.start
webcam.stop

keylogger.start
keylogger.stop

file.upload
file.download

power.lock
power.restart
power.shutdown
power.sleep
```

Quy tắc này giúp dễ mở rộng khi bổ sung module mới.

---

# Authentication Flow

## Web App Authentication

```text
Web App
    │
    │ 1. Connect WebSocket
    ▼
Gateway
    │
    │ 2. Receive auth.webapp { token }
    │ 3. Validate JWT token
    ▼
Connection Accepted / Rejected
```

Chi tiết JWT token spec xem tại `security_design.md`.

---

## Client App Authentication

```text
Client App
   │
   │ 1. Connect WebSocket
   ▼
Gateway
   │
   │ 2. Receive auth.client { machineId, machineSecret, hostname, ipAddress }
   │ 3. Validate credentials
   │ 4. Register vào Machine Registry
   ▼
Connection Accepted / Rejected
```

Sau khi xác thực thành công, Client App sẽ được thêm vào Machine Registry.

Chi tiết payload xem tại `api_contract.md`.

---

# Heartbeat

Client App gửi Heartbeat định kỳ.

```json
{
  "type": "heartbeat",
  "payload": {
    "status": "online"
  }
}
```

Gateway sử dụng Heartbeat để:

- Kiểm tra Client App còn hoạt động.
- Cập nhật trạng thái Machine.
- Phát hiện mất kết nối.

## Heartbeat Parameters

| Parameter             | Value | Mô tả                                                        |
| --------------------- | ----- | ------------------------------------------------------------ |
| `HEARTBEAT_INTERVAL`  | 15s   | Client App gửi heartbeat mỗi 15 giây                        |
| `HEARTBEAT_TIMEOUT`   | 45s   | Không nhận được heartbeat trong 45s → Gateway đánh dấu Offline |
| `RECONNECT_INTERVAL`  | 5s    | Client App thử kết nối lại sau mỗi 5 giây                   |
| `RECONNECT_MAX_RETRY` | ∞     | Client App thử kết nối lại vô thời hạn                      |

---

# Permission Confirmation Flow

Một số chức năng nhạy cảm yêu cầu End User xác nhận trước khi thực hiện.

Danh sách chức năng nhạy cảm và message types tương ứng xem tại `api_contract.md` — **Sensitive Feature List**.

Luồng xử lý:

```text
Web App
    │
    │ [feature].start  (vd: screen.live.start)
    ▼
Gateway
    │
    │ permission.request
    ▼
Client App
    │
    │ Hiển thị Permission Dialog cho End User
    │
    ├── Accept → permission.response { granted: true }
    │               → Gateway chuyển tiếp lệnh gốc tới Client App
    │
    └── Reject → permission.response { granted: false }
                    → Gateway trả error PERMISSION_DENIED về Web App
```

- Timeout xác nhận: **30 giây**. Nếu End User không phản hồi, Gateway trả về `PERMISSION_TIMEOUT`.
- Chi tiết payload của `permission.request` và `permission.response` xem tại `api_contract.md`.

---

# Command Flow

```text
Administrator
      │
      ▼
Web App
      │
      ▼
Gateway
      │
      ▼
  Client App
      │
Execute
      │
      ▼
Gateway
      │
      ▼
Web App
```

Mỗi Request phải có đúng một Response.

---

# Streaming

Streaming được sử dụng cho:

- Live Screen
- Webcam

Luồng xử lý:

```text
Start Stream → Frame → Frame → Frame → Stop Stream
```

Gateway chỉ chuyển tiếp dữ liệu, không xử lý hình ảnh.

Chi tiết frame format (encoding, FPS, kích thước tối đa) xem tại `api_contract.md`.

---

# File Transfer

Quy trình Upload / Download:

```text
Upload:

Web App

↓

Gateway

↓

Client App

↓

Sandbox Folder

↓

Gateway

↓

Web App

Download:

Web App

↓

Gateway

↓

Client App
↓

Sandbox Folder

↓

Gateway

↓

Web App
```

Client App chỉ được phép truy cập thư mục Sandbox.

Mọi yêu cầu file transfer phải kiểm tra đường dẫn trước khi thực hiện.

Nếu đường dẫn nằm ngoài Sandbox, hệ thống trả về `INVALID_PATH`.

Chi tiết file transfer payload và giới hạn kích thước xem tại `api_contract.md`.

# Error Response

Nếu xảy ra lỗi, Client App hoặc Gateway trả về:

```json
{
  "type": "error",
  "payload": {
    "code": "PERMISSION_DENIED",
    "message": "Permission denied."
  }
}
```

---

## Standard Error Codes

Danh sách đầy đủ error codes xem tại `api_contract.md` — **Error Codes**.

Các error codes chính:

```text
AUTHENTICATION_FAILED    — xác thực thất bại
AUTHORIZATION_FAILED     — không đủ quyền
MACHINE_OFFLINE          — máy không online
MACHINE_NOT_FOUND        — không tìm thấy machine
INVALID_COMMAND          — lệnh không hợp lệ
PERMISSION_DENIED        — End User từ chối
PERMISSION_TIMEOUT       — End User không phản hồi trong 30s
INVALID_PATH             — đường dẫn ngoài sandbox
FILE_TOO_LARGE           — file vượt quá 50 MB
ALREADY_RUNNING          — chức năng đang chạy rồi
TIMEOUT                  — không nhận được phản hồi
INTERNAL_ERROR           — lỗi hệ thống
```

---

# Design Decisions

## Tại sao sử dụng JSON?

- Dễ đọc.
- Dễ debug.
- Dễ mở rộng.
- Hỗ trợ tốt trong Python và JavaScript.

---

## Tại sao thống nhất một Message Format?

- Đơn giản hóa việc xử lý.
- Giảm số lượng parser.
- Dễ bảo trì.

---

## Tại sao mọi Request đều có Response?

- Theo dõi được trạng thái thực hiện.
- Dễ xử lý Timeout.
- Thuận tiện cho Audit Log.

---

# Assumptions

- Tất cả các kết nối đều sử dụng WebSocket.
- Message luôn được gửi dưới dạng JSON.
- Gateway là thành phần trung gian duy nhất.

---

# Related Documents

- project_requirements.md
- system_specification.md
- system_architecture.md
- security_design.md
- TECH_STACK.md
- **api_contract.md** — payload spec đầy đủ cho mọi message type
