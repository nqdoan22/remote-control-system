Dưới đây là bản cập nhật cho file **`system_architecture.md`**.

Tôi đã bổ sung các thành phần hệ thống cực kỳ quan trọng để làm nổi bật **tư duy kiến trúc** của bạn, bao gồm:

1. **Tách rõ Frontend (React) và Backend (FastAPI + SQLite)** trong khối Web App.
2. **Cập nhật luồng Command Flow thành 2 luồng riêng biệt:** Luồng thực thi trực tiếp và **Luồng yêu cầu cấp quyền (User Consent Flow)**. Đây là điểm ăn tiền lớn nhất của đồ án.
3. **Thêm mô hình đa luồng (Multi-threading)** ở Client App (PyQt6 Main Thread & Asyncio Worker) để giải thích cách ứng dụng không bị đơ khi nhận lệnh.

Bạn hãy copy đoạn mã Markdown dưới đây và dán đè vào file hiện tại nhé:

```markdown
# System Architecture

## Overview

Tài liệu này mô tả kiến trúc tổng thể của hệ thống, trách nhiệm của từng thành phần, luồng xử lý thông điệp và quyết định thiết kế.

Hệ thống được thiết kế theo mô hình **3-Tier Architecture** (3 lớp), gồm ba khối độc lập:
- **Web App (Frontend + Backend + Database)**
- **Gateway (WebSocket Broker)**
- **Client App (Python PyQt6 Agent)**

Mỗi thành phần có một trách nhiệm riêng biệt, đảm bảo tính bảo mật (Security), sự lỏng lẻo trong liên kết (Low Coupling) và hiệu năng cao (High Performance) trong mạng LAN.

---

# High-level Architecture

```text
                     Administrator
                           │
                           │ HTTP / REST API
                           ▼
+------------------------------------------------------+
|                       WEB APP                        |
|                                                      |
|  [ ReactJS Frontend ] ◄──► [ FastAPI Backend ]       |
|  - Dashboard               - Auth & JWT              |
|  - Machine Control         - REST Endpoints          |
|  - Live Streaming UI       - Command Service         |
|                                  │                   |
|                            [ SQLite DB ]             |
|                            - users, machines, logs   |
+------------------------------------------------------+
                           │
                           │ WebSocket (JSON - JWT Auth)
                           ▼
+------------------------------------------------------+
|                       GATEWAY                        |
|  [ Python Asyncio + WebSockets ]                     |
|  - Connection Manager (Web <-> Agents)               |
|  - Message Router & JSON RPC                         |
|  - Heartbeat Manager (Ping/Pong)                     |
|  - Stream Manager (Live Screen/Webcam)               |
+------------------------------------------------------+
                           │
                           │ WebSocket (JSON RPC)
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
+---------------+  +---------------+  +---------------+
| Client App A  |  | Client App B  |  | Client App N  |
| (PyQt6 Agent) |  | (PyQt6 Agent) |  | (PyQt6 Agent) |
+---------------+  +---------------+  +---------------+

```

---

# Component Responsibilities

## 1. Web App

Web App là trung tâm điều khiển (Control Panel) dành cho Administrator.
Được chia làm 2 phần: Frontend (Giao diện) và Backend (Logic & Dữ liệu).

### Trách nhiệm:

* Xác thực Administrator qua JWT.
* Lưu trữ cấu hình hệ thống, danh sách Machine và Audit Log (SQLite).
* Cung cấp giao diện Web trực quan (Dashboard).
* Gửi lệnh điều khiển (Commands) sang Gateway.
* Tiếp nhận kết quả và dữ liệu Streaming (hình ảnh, tiến trình) để hiển thị.

### Không chịu trách nhiệm:

* Không kết nối trực tiếp đến Client App (Agent).
* Không xử lý tác vụ phần cứng trên máy Client.

---

## 2. Gateway

Gateway là trạm trung chuyển (Message Broker) xử lý hàng ngàn kết nối đồng thời nhờ kiến trúc bất đồng bộ `asyncio`.

### Trách nhiệm:

* Quản lý và duy trì kết nối WebSocket từ cả Web App và các Client App.
* Định tuyến (Route) thông điệp từ Admin đến đúng Machine ID mục tiêu.
* Quản lý trạng thái Online/Offline qua cơ chế Heartbeat.
* Băng thông rộng để chuyển tiếp dữ liệu luồng (Live Screen, Webcam).

### Không chịu trách nhiệm:

* Không lưu trữ dữ liệu lâu dài (No Database).
* Không chứa Business Logic nghiệp vụ.
* Không có giao diện người dùng.

---

## 3. Client App (Python Agent)

Client App là một ứng dụng Desktop chạy ngầm trên Windows, có giao diện bảo vệ quyền lợi người dùng cuối (End User).

### Trách nhiệm:

* Tự động duy trì kết nối WebSocket tới Gateway.
* Khai thác dữ liệu phần cứng, tiến trình, ứng dụng (thông qua `psutil`, `win32gui`).
* **Hiển thị Popup xin quyền (Quy tắc bảo mật cao nhất).**
* Bật cờ cảnh báo (Đèn đỏ Webcam) khi bị giám sát.
* Sandboxing: Chỉ cho phép thao tác file trong vùng quy định.

### Không chịu trách nhiệm:

* Không chứa thông tin xác thực của Admin.
* Không điều phối các Machine khác.

---

# Internal Modules (Kiến trúc Module)

### Client App Threading Model (PyQt6)

Để Client App không bị đơ giao diện khi xử lý lệnh và mạng, kiến trúc đa luồng (Multi-threading) được áp dụng:

1. **Main Thread (GUI Thread):** Chạy vòng lặp sự kiện PyQt6, hiển thị Popup và Đèn cảnh báo Webcam.
2. **Worker Thread (Network Thread):** Chạy vòng lặp `asyncio`, duy trì WebSocket, parse JSON lệnh. Khi cần xin quyền, Worker Thread bắn `PyQt Signal` lên Main Thread.

---

# Command Flow (Luồng xử lý lệnh)

Hệ thống có 2 luồng xử lý lệnh tùy thuộc vào mức độ nhạy cảm của chức năng.

## 1. Direct Execution Flow (Chức năng bình thường)

*(Ví dụ: Xem danh sách Process, Khởi động Application)*

```text
Admin ──> Web App ──> Gateway ──> Client App 
                                      │
                                [Thực thi ngay]
                                      │
Admin <── Web App <── Gateway <───────┘ (Trả về kết quả & Ghi Audit Log)

```

## 2. User Consent Flow (Chức năng nhạy cảm)

*(Ví dụ: Live Screen, Keylogger, Webcam, Shutdown, File)*

```text
Admin ──> Web App ──> Gateway ──> Client App (Worker Thread)
                                      │
                                      ▼ (Bắn Signal)
                             [Main Thread: Bật Popup xin quyền]
                                      │
       +------------------------------+------------------------------+
       │                              │                              │
[User Accept]                  [User Reject]               [Timeout 15s]
       │                              │                              │
[Thực thi lệnh]               [Hủy thực thi]                 [Hủy thực thi]
       │                              │                              │
       +------------------------------+------------------------------+
                                      │
Admin <── Web App <── Gateway <───────┘ (Gửi phản hồi & Ghi Audit Log)

```

---

# Design Principles & Decisions (Quyết định thiết kế)

## 1. Tại sao dùng Gateway làm trung gian thay vì P2P?

* **Bảo mật:** Web App và Client App không bao giờ biết IP thực của nhau.
* **Vượt NAT/Tường lửa:** Client App chủ động kết nối ra Gateway (Outbound), do đó không cần mở port trên máy tính End User.
* **Dễ mở rộng (Scalability):** Có thể thêm hàng trăm Machine mà không làm quá tải Backend của Web App.

## 2. Tại sao thiết kế Sandboxing cho File Transfer?

Nếu cho phép Admin truy cập toàn bộ ổ cứng (`C:\`), nguy cơ lộ lọt dữ liệu cá nhân của End User là rất cao (Directory Traversal Attack). Việc giới hạn một thư mục Sandbox (VD: `C:\AgentSandbox`) thể hiện tư duy an toàn thông tin khắt khe.

## 3. Single Responsibility Principle (SRP)

* Frontend chỉ lo Render UI.
* Backend chỉ lo Logic Database & JWT Auth.
* Gateway chỉ lo Định tuyến WebSocket.
* Client App chỉ lo Tương tác OS & Người dùng.

---

# Related Documents

* `project_requirements.md`
* `system_specification.md`
* `communication_protocol.md`
* `security_design.md`
* `TECH_STACK.md`

```
