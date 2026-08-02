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

| Feature         | Trigger Message       |
| --------------- | --------------------- |
| Live Screen     | `screen.live.start`   |
| Webcam          | `webcam.start`        |
| Key Logger      | `keylogger.start`     |
| Power — Lock    | `power.lock`          |
| Power — Restart | `power.restart`       |
| Power — Shutdown| `power.shutdown`      |
| Power — Sleep   | `power.sleep`         |

Mọi chức năng **không có trong bảng trên** đều không yêu cầu xác nhận.

---

# System Messages & Heartbeat

| Parameter                  | Value (mặc định) | Mô tả                                                                 |
| -------------------------- | ----------------- | ---------------------------------------------------------------------- |
| `HEARTBEAT_INTERVAL`       | 5s                 | Client App gửi heartbeat mỗi 5 giây (`config.py::HEARTBEAT_INTERVAL_SECONDS`). |
| `HEARTBEAT_TIMEOUT`        | 45s                | Nếu Gateway không nhận được heartbeat trong 45s → đánh dấu Offline (`gateway/config.py::HEARTBEAT_TIMEOUT`, cấu hình qua `.env`). |
| `HEARTBEAT_CHECK_INTERVAL` | 5s                 | Chu kỳ Gateway quét các machine hết hạn heartbeat (background task).  |
| `RECONNECT_INTERVAL`       | 5s                 | Client App thử kết nối lại sau mỗi 5 giây.                            |
| `RECONNECT_MAX_RETRY`      | ∞                  | Client App thử kết nối lại vô thời hạn.                               |

> `HEARTBEAT_TIMEOUT` là giá trị cấu hình được ở Gateway (`.env`); 45s là mặc định hiện tại, có thể chỉnh về ngưỡng thấp hơn (VD: 15s ~ 3 lần rớt heartbeat) tùy độ ổn định mạng LAN thực tế.

### heartbeat

**Client App → Gateway** *(xử lý tại Gateway, không forward xuống Web App)*

```json
{
  "messageId": "uuid",
  "type": "heartbeat",
  "timestamp": 1710000000,
  "source": "client-app-01",
  "destination": "gateway",
  "payload": {
    "status": "online",
    "cpu_usage": 15.2,
    "ram_usage": 42.7
  }
}

```

---

# Authentication Messages

Gateway mở **hai WebSocket endpoint riêng biệt** — mỗi loại kết nối phải nối đúng path của mình, không dùng chung một URL:

| Endpoint            | Dành cho    | Type message đầu tiên bắt buộc |
| ------------------- | ----------- | ------------------------------- |
| `ws://<host>:8765/client` | Client App  | `auth.client`                   |
| `ws://<host>:8765/webapp` | Web App     | `auth.webapp`                   |

Kết nối tới path khác sẽ bị Gateway đóng ngay với close code `4004`. Nếu message đầu tiên không đúng type mong đợi, hoặc không gửi trong vòng 10 giây (`AUTH_TIMEOUT`), Gateway trả `error AUTHENTICATION_FAILED` rồi đóng kết nối với close code `4001`.

## Client App Authentication

**Client App → Gateway** (ngay sau khi kết nối WebSocket tới `/client`)

```json
{
  "messageId": "uuid",
  "type": "auth.client",
  "timestamp": 1710000000,
  "source": "client-app-01",
  "destination": "gateway",
  "payload": {
    "machineId": "client-app-01",
    "machineSecret": "d8e8fca2dc0f896fd7cb4cb0031ba249",
    "hostname": "DESKTOP-ABC123",
    "ipAddress": "192.168.1.100"
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
    "data": {}
  }
}

```

> `machineId`/`machineSecret` được đối chiếu với danh sách `REGISTERED_MACHINES` cấu hình tại Gateway (`.env`). Sai thông tin → `error AUTHENTICATION_FAILED` + đóng kết nối. Sau nhiều lần đăng nhập sai liên tiếp từ cùng một IP, Gateway tạm khóa IP đó (`AUTH_MAX_ATTEMPTS` / `AUTH_LOCKOUT_SECONDS`).

---

## Web App Authentication

**Web App → Gateway** (ngay sau khi kết nối WebSocket tới `/webapp`)

```json
{
  "messageId": "uuid",
  "type": "auth.webapp",
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

> Token được xác thực bằng `JWT_SECRET` cấu hình tại Gateway (`.env`), phải khớp với secret dùng để ký JWT ở Web App Backend.

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
        └── granted: false → trả error PERMISSION_DENIED về Web App

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

Có 2 lớp timeout độc lập:

1. **Client App (15 giây, `PERMISSION_TIMEOUT_SECONDS`):** Nếu End User không bấm Accept/Reject trên Popup trong 15 giây, Client App tự động coi là Từ chối và **chủ động gửi** `permission.response { granted: false }` về Gateway → Gateway trả lỗi `PERMISSION_DENIED` cho Web App.
2. **Gateway (30 giây mặc định, `PERMISSION_TIMEOUT` trong `.env`):** Là lớp bảo vệ dự phòng — nếu vì lý do nào đó (VD: Client App mất kết nối giữa chừng) Gateway không nhận được `permission.response` trong khoảng thời gian này, Gateway tự trả lỗi `PERMISSION_TIMEOUT` cho Web App mà không cần chờ Client App phản hồi.

> Vì (1) luôn xảy ra trước (2) trong điều kiện vận hành bình thường, lỗi thực tế Web App nhận được khi End User không phản hồi là `PERMISSION_DENIED`; `PERMISSION_TIMEOUT` chỉ xuất hiện khi Client App bị treo/mất kết nối trong lúc chờ Popup.

---

# Command Routing Convention

Mọi command gửi từ Web App tới một Client App cụ thể **phải** chứa field `destinationMachineId` trong `payload`.

Gateway sử dụng field này để biết forward message đến machine nào.
Field sẽ bị bỏ ra trước khi forward xuống Client App.

```json
{
  "type": "<command-type>",
  "payload": {
    "destinationMachineId": "machine-uuid",
    "...": "(các field payload của command)"
  }
}
```

| Field                  | Bắt buộc | Mô tả                                     |
| ---------------------- | -------- | ----------------------------------------- |
| `destinationMachineId` | ✅ Có    | UUID của máy đích (lấy từ `machine.list`) |

Ngoại lệ: `machine.list` không cần `destinationMachineId` vì được xử lý tại Gateway.

---

# Machine Management Messages

## machine.list

**Web App → Gateway** *(không cần destinationMachineId)*

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
  "payload": {
    "destinationMachineId": "machine-uuid"
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

> Chỉ được phép thao tác trong **sandbox folder** đã cấu hình (mặc định: `C:\AgentSandbox\`).
> Mọi nỗ lực truy cập đường dẫn tuyệt đối hoặc dùng `../` nằm ngoài sandbox sẽ bị từ chối với lỗi `INVALID_PATH`.

## file.list

**Web App → Gateway → Client App**

```json
{
  "type": "file.list",
  "payload": {
    "path": "C:\\AgentSandbox\\"
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
    "path": "C:\\AgentSandbox\\document.pdf"
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
    "destinationPath": "C:\\AgentSandbox\\uploaded.pdf",
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
      "savedPath": "C:\\AgentSandbox\\uploaded.pdf"
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

Lỗi có thể do **Client App** phát ra (gửi ngược về Gateway để forward cho Web App) hoặc do chính **Gateway** phát ra (khi route/permission/timeout thất bại, không cần hỏi Client App).

Ví dụ lỗi từ Client App (thực thi lệnh thất bại):

```json
{
  "messageId": "uuid",
  "type": "error",
  "timestamp": 1710000000,
  "source": "client-app-01",
  "destination": "gateway",
  "payload": {
    "code": "INTERNAL_ERROR",
    "message": "Không thể truy cập webcam trên máy.",
    "originalMessageId": "uuid-of-failed-request"
  }
}

```

Ví dụ lỗi do Gateway phát ra (End User từ chối cấp quyền):

```json
{
  "messageId": "uuid",
  "type": "error",
  "timestamp": 1710000000,
  "source": "gateway",
  "destination": "webapp",
  "payload": {
    "code": "PERMISSION_DENIED",
    "message": "Permission denied for 'webcam.start'.",
    "originalMessageId": "uuid-of-failed-request"
  }
}

```

---

# Error Codes

## Authentication & Authorization

| Code | Mô tả |
| --- | --- |
| `AUTHENTICATION_FAILED` | Sai Token, sai `machineId`/`machineSecret`, hoặc không gửi `auth.client`/`auth.webapp` đúng hạn/đúng thứ tự. |
| `AUTHORIZATION_FAILED` | *(Dự kiến, chưa implement)* Token hợp lệ nhưng không đủ quyền thực hiện hành động. Hiện tại message type không hợp lệ từ Web App được trả về bằng `INVALID_COMMAND` thay vì mã này. |

## Machine

| Code | Mô tả |
| --- | --- |
| `MACHINE_OFFLINE` | Gateway không tìm thấy Client ID trong Registry, hoặc gửi message tới machine thất bại. |
| `MACHINE_NOT_FOUND` | Không tìm thấy `machineId` trong Registry của Gateway. |

## Permission

| Code | Mô tả |
| --- | --- |
| `PERMISSION_DENIED` | End User bấm Reject trên Popup xin quyền (hoặc tự động Reject sau 15 giây không phản hồi). *(Trước đây gọi là `USER_REJECTED`.)* |
| `PERMISSION_TIMEOUT` | Gateway không nhận được `permission.response` trong thời gian chờ cấu hình (mặc định 30 giây). *(Trước đây gọi là `CONSENT_TIMEOUT`.)* |

## Command

| Code | Mô tả |
| --- | --- |
| `INVALID_COMMAND` | Lệnh không tồn tại, sai format JSON, message type không được phép, hoặc thiếu `destinationMachineId`. |
| `ALREADY_RUNNING` | Chức năng (live screen / webcam / keylogger) đang chạy rồi. |
| `NOT_RUNNING` | Chức năng chưa được khởi động, không thể stop. |
| `TIMEOUT` | Client App không phản hồi (`response`/`error`) trong `COMMAND_TIMEOUT` giây (mặc định 15s) sau khi Gateway forward lệnh. |

## File

| Code | Mô tả |
| --- | --- |
| `INVALID_PATH` | Cố ý truy cập file ngoài thư mục Sandbox |
| `FILE_NOT_FOUND` | File không tồn tại tại đường dẫn chỉ định |
| `FILE_TOO_LARGE` | Kích thước file vượt quá 50 MB |

## Hardware

| Code | Mô tả |
| --- | --- |
| `WEBCAM_NOT_FOUND` | Không mở được thiết bị webcam trên máy (bao gồm cả trường hợp đang bị ứng dụng khác chiếm dụng — Client App hiện tại không phân biệt hai trường hợp này, `WEBCAM_ALREADY_IN_USE` chưa được implement riêng). |

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