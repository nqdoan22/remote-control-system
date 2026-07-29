# API Contract

## Overview

Tài liệu này là **single source of truth** cho toàn bộ message contract trong hệ thống.

Mọi thành phần (Web App, Gateway, Client App) phải tuân thủ chính xác các định nghĩa trong tài liệu này khi implement.

Tài liệu bao gồm:

- Định nghĩa payload cho từng message type.
- Message flow cho Permission Confirmation.
- Streaming frame format.
- File transfer protocol (Sandboxed).
- Heartbeat parameters.
- Danh sách đầy đủ error codes chuẩn.

> Phần mô tả tổng quan giao thức và design rationale xem tại `communication_protocol.md`.

---

# Sensitive Feature List

Đây là danh sách duy nhất xác định các chức năng yêu cầu Permission Confirmation từ End User.

| Feature         | Trigger Message          |
| --------------- | ------------------------ |
| Screenshot      | `screen.screenshot`      |
| Live Screen     | `screen.live.start`      |
| Webcam          | `webcam.start`           |
| Key Logger      | `keylogger.start`        |
| Power — Lock    | `power.lock`             |
| Power — Restart | `power.restart`          |
| Power — Shutdown| `power.shutdown`         |
| Power — Sleep   | `power.sleep`            |

Mọi chức năng **không có trong bảng trên** đều không yêu cầu xác nhận.

---

# System Messages & Heartbeat

| Parameter             | Value  | Mô tả                                                       |
| --------------------- | ------ | ----------------------------------------------------------- |
| `HEARTBEAT_INTERVAL`  | 5s     | Client App gửi heartbeat mỗi 5 giây                         |
| `HEARTBEAT_TIMEOUT`   | 15s    | Nếu rớt heartbeat 3 lần liên tiếp (15s) → đánh dấu Offline  |
| `RECONNECT_INTERVAL`  | 5s     | Client App thử kết nối lại sau mỗi 5 giây                   |
| `RECONNECT_MAX_RETRY` | ∞      | Client App thử kết nối lại vô thời hạn                      |

### system.heartbeat

**Client App → Gateway**

```json
{
  "messageId": "uuid",
  "type": "system.heartbeat",
  "timestamp": 1710000000,
  "source": "client-app-01",
  "destination": "gateway",
  "payload": {
    "status": "online",
    "cpu_usage": 15.2
  }
}

```

---

# Authentication Messages

## Client App Authentication

**Client App → Gateway** (ngay sau khi kết nối WebSocket)

```json
{
  "messageId": "uuid",
  "type": "system.auth",
  "timestamp": 1710000000,
  "source": "client-app-01",
  "destination": "gateway",
  "payload": {
    "machineSecret": "d8e8fca2dc0f896fd7cb4cb0031ba249"
  }
}

```

**Gateway → Client App** (response)

```json
{
  "messageId": "uuid",
  "type": "response",
  "timestamp": 1710000000,
  "source": "gateway",
  "destination": "client-app-01",
  "payload": {
    "success": true,
    "data": {
      "sessionToken": "jwt-token-string"
    }
  }
}

```

---

## Web App Authentication

**Web App → Gateway** (ngay sau khi kết nối WebSocket)

```json
{
  "messageId": "uuid",
  "type": "system.auth",
  "timestamp": 1710000000,
  "source": "webapp",
  "destination": "gateway",
  "payload": {
    "token": "jwt-token-from-backend"
  }
}

```

**Gateway → Web App** (response)

```json
{
  "messageId": "uuid",
  "type": "response",
  "timestamp": 1710000000,
  "source": "gateway",
  "destination": "webapp",
  "payload": {
    "success": true,
    "data": {}
  }
}

```

---

# Permission Confirmation Messages

Áp dụng cho các chức năng trong **Sensitive Feature List**.

## Flow

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
  │ Hiển thị Popup (Always-on-top) cho End User
  │
  ├── Accept → permission.response { granted: true }
  └── Reject → permission.response { granted: false }
        │
        ▼
      Gateway
        │
        ├── granted: true  → chuyển tiếp lệnh gốc tới Client App
        └── granted: false → trả error USER_REJECTED về Web App

```

## permission.request

**Gateway → Client App**

```json
{
  "messageId": "uuid",
  "type": "permission.request",
  "timestamp": 1710000000,
  "source": "gateway",
  "destination": "client-app-01",
  "payload": {
    "permissionId": "uuid",
    "feature": "screen.live",
    "requestedBy": "admin@system",
    "originalMessageId": "uuid-of-original-request"
  }
}

```

## permission.response

**Client App → Gateway**

```json
{
  "messageId": "uuid",
  "type": "permission.response",
  "timestamp": 1710000000,
  "source": "client-app-01",
  "destination": "gateway",
  "payload": {
    "permissionId": "uuid",
    "granted": true
  }
}

```

## Permission Timeout

* Nếu End User không phản hồi trong **15 giây**, hệ thống tự động đánh giá là Từ chối và trả về lỗi `CONSENT_TIMEOUT` cho Web App.

---

# Machine Management Messages

## machine.list

**Web App → Gateway**

```json
{
  "type": "machine.list",
  "payload": {}
}

```

**Gateway → Web App** (response)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {
      "machines": [
        {
          "machineId": "machine-uuid",
          "hostname": "DESKTOP-ABC123",
          "ipAddress": "192.168.1.100",
          "status": "online",
          "lastSeen": 1710000000
        }
      ]
    }
  }
}

```

---

# Application Management Messages

## application.list

**Web App → Gateway → Client App**

```json
{
  "type": "application.list",
  "payload": {}
}

```

**Client App → Gateway → Web App** (response)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {
      "applications": [
        {
          "name": "Chrome",
          "pid": 1234,
          "cpuUsage": 5.2,
          "mainWindowTitle": "New Tab - Google Chrome"
        }
      ]
    }
  }
}

```

> Application được định nghĩa là tiến trình có cửa sổ giao diện (MainWindowHandle != 0).

## application.start

**Web App → Gateway → Client App**

```json
{
  "type": "application.start",
  "payload": {
    "path": "C:\\Program Files\\App\\app.exe"
  }
}

```

## application.stop

**Web App → Gateway → Client App**

```json
{
  "type": "application.stop",
  "payload": {
    "pid": 1234
  }
}

```

---

# Process Management Messages

## process.list

**Web App → Gateway → Client App**

```json
{
  "type": "process.list",
  "payload": {}
}

```

**Client App → Gateway → Web App** (response)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {
      "processes": [
        {
          "pid": 1234,
          "name": "chrome.exe",
          "cpuUsage": 5.2,
          "memoryMB": 256.4
        }
      ]
    }
  }
}

```

## process.kill

**Web App → Gateway → Client App**

```json
{
  "type": "process.kill",
  "payload": {
    "pid": 1234
  }
}

```

**Client App → Gateway → Web App** (response)

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

# Screen Monitoring Messages

## screen.screenshot

**Web App → Gateway → Client App**

```json
{
  "type": "screen.screenshot",
  "payload": {}
}

```

**Client App → Gateway → Web App** (response)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {
      "image": "<base64-encoded-jpeg>",
      "width": 1920,
      "height": 1080,
      "timestamp": 1710000000
    }
  }
}

```

> Ảnh screenshot được encode dưới dạng JPEG, base64. Chất lượng JPEG: 80%.

---

## Live Screen

> Chức năng nhạy cảm — xem **Permission Confirmation Messages**.

### screen.live.start

**Web App → Gateway → Client App** *(sau khi permission granted)*

```json
{
  "type": "screen.live.start",
  "payload": {
    "fps": 10
  }
}

```

| Field | Value mặc định | Mô tả |
| --- | --- | --- |
| `fps` | 10 | Số frame mỗi giây, tối đa 30 |

**Client App → Gateway → Web App** (response xác nhận bắt đầu)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {}
  }
}

```

### screen.live.frame

**Client App → Gateway → Web App** *(liên tục sau khi start)*

```json
{
  "type": "screen.live.frame",
  "payload": {
    "image_base64": "<base64-encoded-jpeg>",
    "width": 1920,
    "height": 1080,
    "frameIndex": 42,
    "timestamp": 1710000000
  }
}

```

> Mỗi frame là JPEG base64. Chất lượng JPEG: 60% (ưu tiên tốc độ). Kích thước tối đa mỗi frame: 512 KB sau encode.

### screen.live.stop

**Web App → Gateway → Client App**

```json
{
  "type": "screen.live.stop",
  "payload": {}
}

```

---

# Webcam Messages

> Chức năng nhạy cảm — xem **Permission Confirmation Messages**.

## webcam.start

**Web App → Gateway → Client App** *(sau khi permission granted)*

```json
{
  "type": "webcam.start",
  "payload": {
    "fps": 10
  }
}

```

**Client App → Gateway → Web App** (response xác nhận bắt đầu)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {}
  }
}

```

## webcam.frame

**Client App → Gateway → Web App** *(liên tục sau khi start)*

```json
{
  "type": "webcam.frame",
  "payload": {
    "image_base64": "<base64-encoded-jpeg>",
    "width": 640,
    "height": 480,
    "frameIndex": 42,
    "timestamp": 1710000000
  }
}

```

> Kích thước frame mặc định: 640×480. Chất lượng JPEG: 70%.

## webcam.stop

**Web App → Gateway → Client App**

```json
{
  "type": "webcam.stop",
  "payload": {}
}

```

> Client App phải **tắt webcam indicator (chấm đỏ)** ngay khi nhận được lệnh này.

---

# Key Logger Messages

> Chức năng nhạy cảm — xem **Permission Confirmation Messages**.

## keylogger.start

**Web App → Gateway → Client App** *(sau khi permission granted)*

```json
{
  "type": "keylogger.start",
  "payload": {}
}

```

## keylogger.stop

**Web App → Gateway → Client App**

```json
{
  "type": "keylogger.stop",
  "payload": {}
}

```

## keylogger.data

**Client App → Gateway → Web App** *(event — gửi định kỳ khi đang chạy)*

```json
{
  "type": "keylogger.data",
  "payload": {
    "entries": [
      {
        "key": "H",
        "timestamp": 1710000001
      },
      {
        "key": "e",
        "timestamp": 1710000001
      }
    ],
    "windowTitle": "Notepad"
  }
}

```

> `keylogger.data` được gửi mỗi 2 giây hoặc khi buffer đạt 50 phím, tùy điều kiện nào đến trước.

---

# File Transfer Messages

> Chỉ được phép thao tác trong **sandbox folder** đã cấu hình (mặc định: `~/AgentSandbox`, cấu hình trong `config.py`).
> Mọi nỗ lực truy cập đường dẫn tuyệt đối hoặc dùng `../` nằm ngoài sandbox sẽ bị từ chối với lỗi `INVALID_PATH`.

## file.list

**Web App → Gateway → Client App**

```json
{
  "type": "file.list",
  "payload": {
    "path": "~/AgentSandbox/"
  }
}

```

**Client App → Gateway → Web App** (response)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {
      "entries": [
        {
          "name": "document.pdf",
          "type": "file",
          "sizeBytes": 204800,
          "modifiedAt": 1710000000
        },
        {
          "name": "subfolder",
          "type": "directory",
          "modifiedAt": 1710000000
        }
      ]
    }
  }
}

```

## file.download

**Web App → Gateway → Client App**

```json
{
  "type": "file.download",
  "payload": {
    "path": "~/AgentSandbox/document.pdf"
  }
}

```

**Client App → Gateway → Web App** (response)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {
      "filename": "document.pdf",
      "content": "<base64-encoded-bytes>",
      "sizeBytes": 204800,
      "mimeType": "application/pdf"
    }
  }
}

```

> Kích thước file tối đa cho download: **50 MB**. Vượt quá sẽ trả về `FILE_TOO_LARGE`.

## file.upload

**Web App → Gateway → Client App**

```json
{
  "type": "file.upload",
  "payload": {
    "destinationPath": "~/AgentSandbox/uploaded.pdf",
    "filename": "uploaded.pdf",
    "content": "<base64-encoded-bytes>",
    "sizeBytes": 204800
  }
}

```

**Client App → Gateway → Web App** (response)

```json
{
  "type": "response",
  "payload": {
    "success": true,
    "data": {
      "savedPath": "~/AgentSandbox/uploaded.pdf"
    }
  }
}

```

> Kích thước file tối đa cho upload: **50 MB**.

---

# Power Management Messages

> Chức năng nhạy cảm — xem **Permission Confirmation Messages**.

## power.lock

```json
{
  "type": "power.lock",
  "payload": {}
}

```

## power.restart

```json
{
  "type": "power.restart",
  "payload": {
    "delaySeconds": 0
  }
}

```

## power.shutdown

```json
{
  "type": "power.shutdown",
  "payload": {
    "delaySeconds": 0
  }
}

```

## power.sleep

```json
{
  "type": "power.sleep",
  "payload": {}
}

```

**Response chung cho tất cả Power commands** (Client App → Gateway → Web App)

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

# Error Response

```json
{
  "messageId": "uuid",
  "type": "error",
  "timestamp": 1710000000,
  "source": "client-app-01",
  "destination": "gateway",
  "payload": {
    "code": "USER_REJECTED",
    "message": "End user rejected the request.",
    "originalMessageId": "uuid-of-failed-request"
  }
}

```

---

# Error Codes

## Authentication & Authorization

| Code | Mô tả |
| --- | --- |
| `AUTHENTICATION_FAILED` | Sai Token hoặc sai Machine Secret |
| `AUTHORIZATION_FAILED` | Token hợp lệ nhưng không đủ quyền thực hiện hành động |

## Machine

| Code | Mô tả |
| --- | --- |
| `MACHINE_OFFLINE` | Gateway không tìm thấy Client ID trong Registry |
| `MACHINE_NOT_FOUND` | Không tìm thấy machineId trong CSDL |

## Permission

| Code | Mô tả |
| --- | --- |
| `USER_REJECTED` | End User bấm Reject trên Popup xin quyền |
| `CONSENT_TIMEOUT` | End User không phản hồi sau 15 giây (Auto-Reject) |

## Command

| Code | Mô tả |
| --- | --- |
| `INVALID_COMMAND` | Lệnh không tồn tại hoặc sai format JSON |
| `ALREADY_RUNNING` | Chức năng (live screen / keylogger) đang chạy rồi |
| `NOT_RUNNING` | Chức năng chưa được khởi động, không thể stop |

## File

| Code | Mô tả |
| --- | --- |
| `INVALID_PATH` | Cố ý truy cập file ngoài thư mục Sandbox |
| `FILE_NOT_FOUND` | File không tồn tại tại đường dẫn chỉ định |
| `FILE_TOO_LARGE` | Kích thước file vượt quá 50 MB |

## Hardware

| Code | Mô tả |
| --- | --- |
| `WEBCAM_NOT_FOUND` | Không tìm thấy webcam trên máy |
| `WEBCAM_ALREADY_IN_USE` | Webcam đang được sử dụng bởi ứng dụng khác |

## System

| Code | Mô tả |
| --- | --- |
| `INTERNAL_ERROR` | Lỗi xảy ra trong lúc gọi thư viện hệ thống |

---

# Response Conventions

* Mỗi Request phải có **đúng một Response**.
* Response thành công: `payload.success = true`, dữ liệu trả về trong `payload.data`.
* Response thất bại: dùng **Error Response** format với `type: "error"`.
* Streaming (Live Screen, Webcam) là ngoại lệ: sau Response xác nhận bắt đầu, Client App tiếp tục gửi Frame events cho đến khi nhận lệnh stop.

---

# Related Documents

* `communication_protocol.md` — Tổng quan giao thức, design rationale, message flow diagrams.
* `security_design.md` — Authentication flow, authorization rules, JWT spec.
* `system_architecture.md` — Kiến trúc hệ thống và trách nhiệm từng thành phần.
* `system_specification.md` — Functional và non-functional requirements.
* `TECH_STACK.md` — Công nghệ và thư viện sử dụng.

```

```