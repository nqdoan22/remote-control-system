# Communication Protocol

## Overview

Tài liệu này định nghĩa giao thức truyền thông tiêu chuẩn (Standardized Communication Protocol) giữa các thành phần trong hệ thống.

Các kết nối bao gồm:
- **Web App (Backend) ↔ Gateway**
- **Gateway ↔ Client App (Agent)**

Để đảm bảo tính đồng nhất, tốc độ cao theo thời gian thực và dễ dàng gỡ lỗi (debug), toàn bộ dữ liệu trong hệ thống được truyền tải dưới định dạng **JSON** thông qua giao thức **WebSocket (ws://)**.

---

# Communication Model

```text
[ Administrator ]
      │ (HTTPS / REST)
      ▼
+-----------+
|  Web App  | (Tạo JSON Command)
+-----------+
      │
      │ (WebSocket Request + JWT)
      ▼
+-----------+
|  Gateway  | (Message Broker)
+-----------+
      │
      │ (WebSocket Request định tuyến theo ID)
      ▼
+------------+
| Client App | (Thực thi & Bật Popup xin quyền)
+------------+
      │
      │ (WebSocket Response / Stream Base64)
      ▼
+-----------+
|  Gateway  | (Chuyển tiếp)
+-----------+
      │
      │ (WebSocket Response)
      ▼
+-----------+
|  Web App  | (Ghi Audit Log & Cập nhật UI)
+-----------+

```

**Vai trò của Gateway:**

* Chỉ thực hiện: Authentication (Xác thực kết nối), Routing (Định tuyến thông điệp dựa trên `destination`), và Connection Management (Quản lý Heartbeat).
* **Tuyệt đối KHÔNG xử lý Business Logic**, không lưu trữ hay giải mã dữ liệu Streaming.

---

# General Message Format (Định dạng Thông điệp)

Mọi message giao tiếp trong hệ thống đều tuân thủ chặt chẽ một cấu trúc JSON duy nhất (JSON RPC-like).

```json
{
  "messageId": "550e8400-e29b-41d4-a716-446655440000",
  "type": "process.list",
  "timestamp": 1710000000,
  "source": "gateway",
  "destination": "client-app-01",
  "payload": {
    "filter": "chrome"
  }
}

```

## Fields Definition

| Field | Kiểu dữ liệu | Description (Mô tả) |
| --- | --- | --- |
| `messageId` | String (UUID) | Mã định danh duy nhất của message để map Request với Response. |
| `type` | String | Loại thao tác/lệnh (VD: `system.heartbeat`, `screen.live.start`). |
| `timestamp` | Integer | Thời điểm gửi (Unix Epoch Time) để kiểm tra độ trễ mạng. |
| `source` | String | ID của thành phần gửi (VD: `webapp-backend`, `client-id-123`). |
| `destination` | String | ID của thành phần nhận (`gateway` hoặc `client-id-xyz`). |
| `payload` | Object | Dữ liệu linh hoạt chứa tham số lệnh hoặc kết quả trả về. |

---

# Message Types (Phân loại Thông điệp)

Hệ thống sử dụng 3 loại message chính được phân biệt qua trường `type`.

## 1. Request (Yêu cầu)

Là lệnh gửi từ Web App xuống Client App. Bắt buộc phải có Response tương ứng.

```json
{
  "messageId": "req-001",
  "type": "process.kill",
  "source": "webapp",
  "destination": "client-01",
  "payload": { "pid": 1234 }
}

```

## 2. Response (Phản hồi)

Kết quả thực thi từ Client App gửi về Web App. Sử dụng lại `messageId` của Request gốc.

```json
{
  "messageId": "req-001", 
  "type": "response",
  "source": "client-01",
  "destination": "webapp",
  "payload": {
    "success": true,
    "data": { "message": "Process 1234 terminated successfully" }
  }
}

```

## 3. Event (Sự kiện / Luồng liên tục)

Dùng cho tín hiệu Heartbeat hoặc dữ liệu Stream không cần phản hồi trực tiếp.

```json
{
  "messageId": "evt-002",
  "type": "system.heartbeat",
  "source": "client-01",
  "destination": "gateway",
  "payload": {
    "status": "online",
    "cpu_usage": 15.2
  }
}

```

---

# Message Naming Convention (Quy tắc đặt tên Type)

Tên message tuân theo format: `[module].[action]`

| Module | Lệnh (Actions) |
| --- | --- |
| **system** | `heartbeat`, `auth` |
| **application** | `list`, `start`, `stop` |
| **process** | `list`, `kill` |
| **screen** | `screenshot`, `live.start`, `live.stop`, `live.frame` |
| **webcam** | `start`, `stop`, `frame` |
| **keylogger** | `start`, `stop`, `data` |
| **file** | `list`, `upload`, `download` |
| **power** | `lock`, `restart`, `shutdown`, `sleep` |

---

# Authentication Flow (Luồng Xác thực)

## 1. Web App (Backend) Authentication

Web App Backend đóng vai trò như một Super Client. Khi mở WebSocket tới Gateway, thông điệp đầu tiên bắt buộc phải là `system.auth` chứa **JWT Secret**.

## 2. Client App Authentication

Khi Agent khởi động, nó mở kết nối và gửi thông tin định danh:

```json
{
  "type": "system.auth",
  "source": "client-01",
  "destination": "gateway",
  "payload": {
    "machineSecret": "d8e8fca2dc0f896fd7cb4cb0031ba249"
  }
}

```

*Nếu sai Secret, Gateway đóng kết nối ngay lập tức với mã code `1008 Policy Violation`.*

---

# Data Streaming & File Transfer (Truyền tải Dữ liệu lớn)

Vì WebSocket trong dự án thống nhất dùng chuỗi JSON, các dữ liệu nhị phân (Ảnh Screenshot, Khung hình Webcam, File) **bắt buộc phải được mã hóa sang chuỗi Base64** trước khi đưa vào trường `payload`.

## Streaming (Live Screen / Webcam)

Client App chụp ảnh, nén JPEG, mã hóa Base64 và gửi liên tục:

```json
{
  "type": "screen.live.frame",
  "payload": {
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
  }
}

```

## File Transfer

Tệp tin được chia nhỏ (Chunking) để không làm nghẽn luồng JSON:

* Client App kiểm tra đường dẫn thư mục Sandbox. Nếu hợp lệ, tiến hành đọc file.
* Đóng gói từng phần file bằng Base64 và gửi đi.
* Nếu cố tình đọc ngoài Sandbox (VD: `C:\Windows`), Client trả về mã lỗi `INVALID_PATH`.

---

# Error Handling & Standard Codes

Nếu có lỗi (Bao gồm cả việc End User từ chối lệnh), Client trả về message có type `error`.

```json
{
  "messageId": "req-002",
  "type": "error",
  "payload": {
    "code": "USER_REJECTED",
    "message": "End User denied the webcam request."
  }
}

```

## Danh sách Error Codes chuẩn:

| Mã lỗi | Mô tả nguyên nhân |
| --- | --- |
| `AUTHENTICATION_FAILED` | Sai Token hoặc sai Machine Secret. |
| `MACHINE_OFFLINE` | Gateway không tìm thấy Client ID trong Registry. |
| `INVALID_COMMAND` | Lệnh không tồn tại hoặc sai format JSON. |
| `USER_REJECTED` | **End User bấm Reject trên Popup xin quyền.** |
| `CONSENT_TIMEOUT` | **End User không phản hồi sau 15 giây (Auto-Reject).** |
| `INVALID_PATH` | Cố ý truy cập file ngoài thư mục Sandbox. |
| `INTERNAL_ERROR` | Lỗi xảy ra trong lúc gọi thư viện hệ thống (psutil, cv2). |

---

# Design Decisions (Quyết định thiết kế)

1. **Tại sao sử dụng duy nhất JSON?**
* Dễ đọc, dễ debug và log lại vào Database (SQLite hỗ trợ JSON rất tốt).
* Python (`json`) và Javascript (Web) phân tích cú pháp (parse) JSON nguyên bản với hiệu năng cực cao.


2. **Tại sao mọi Request đều cần có `messageId`?**
* Do tính chất bất đồng bộ (Asynchronous) của WebSocket, Web App có thể gửi nhiều lệnh cùng lúc. `messageId` giúp Backend biết chính xác phản hồi `response` này thuộc về `request` nào.


3. **Mã hóa Base64 cho Video Stream có làm chậm hệ thống không?**
* Có tăng dung lượng payload (~33%), nhưng chấp nhận được trong môi trường mạng LAN (Băng thông thường từ 100Mbps - 1Gbps). Đổi lại, kiến trúc Gateway đơn giản đi rất nhiều do không phải xử lý phân tách gói tin Binary và Text riêng biệt.



---

# Related Documents

* `project_requirements.md`
* `system_specification.md`
* `system_architecture.md`
* `security_design.md`
* `TECH_STACK.md`

```

