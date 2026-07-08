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

## Backend Authentication

```text
Web App
    │
Connect
    │
    ▼
Gateway
    │
Authenticate
    │
    ▼
Connection Accepted
```

---

## Client App Authentication

```text
Client App
   │
Connect
   │
   ▼
Gateway
   │
machineId
machineSecret
   │
Authenticate
   │
Register
```

Sau khi xác thực thành công, Client App sẽ được thêm vào Machine Registry.

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
Start Stream

↓

Frame

↓

Frame

↓

Frame

↓

Stop Stream
```

Gateway chỉ chuyển tiếp dữ liệu.

Gateway không xử lý hình ảnh.

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

```text
AUTHENTICATION_FAILED

AUTHORIZATION_FAILED

MACHINE_OFFLINE

MACHINE_NOT_FOUND

INVALID_COMMAND

PERMISSION_DENIED

INVALID_PATH

TIMEOUT

INTERNAL_ERROR
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
- tech_stack.md
