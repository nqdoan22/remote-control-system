# System Architecture

## Overview

Tài liệu này mô tả kiến trúc tổng thể của hệ thống, trách nhiệm của từng thành phần và luồng xử lý chính.

Hệ thống được thiết kế theo mô hình **3-tier architecture**, gồm ba thành phần độc lập:

- Web App
- Gateway
- Agent

Mỗi thành phần có một trách nhiệm riêng và giao tiếp thông qua giao thức WebSocket.

---

# High-level Architecture

```text
                     Administrator
                           │
                           │ HTTPS
                           ▼
+------------------------------------------------+
|                  Web App                       |
|------------------------------------------------|
| - Authentication                              |
| - Business Logic                              |
| - Dashboard                                   |
| - Machine Management                          |
| - Command Service                             |
+------------------------------------------------+
                           │
                    WebSocket (Authenticated)
                           │
                           ▼
+------------------------------------------------+
|                   Gateway                      |
|------------------------------------------------|
| - Authentication Manager                      |
| - Connection Manager                          |
| - Machine Registry                            |
| - Message Router                              |
| - Heartbeat Manager                           |
| - Stream Manager                              |
+------------------------------------------------+
                           │
                    WebSocket (Authenticated)
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
+---------------+  +---------------+  +---------------+
|    Agent A    |  |    Agent B    |  |    Agent N    |
+---------------+  +---------------+  +---------------+
```

---

# Component Responsibilities

## Web App

Web App là thành phần mà Administrator sử dụng để quản lý hệ thống.

### Responsibilities

- Xác thực Administrator.
- Hiển thị giao diện quản trị.
- Quản lý danh sách Machine.
- Gửi lệnh điều khiển.
- Hiển thị kết quả.
- Ghi nhận Audit Log.

### Không chịu trách nhiệm

- Quản lý kết nối tới Agent.
- Thực thi lệnh trên Machine.
- Xử lý dữ liệu Streaming.

---

## Gateway

Gateway là trung tâm giao tiếp của toàn bộ hệ thống.

### Responsibilities

- Quản lý kết nối WebSocket.
- Xác thực Backend và Agent.
- Lưu danh sách Agent đang Online.
- Định tuyến Message.
- Quản lý Heartbeat.
- Chuyển tiếp dữ liệu Streaming.
- Theo dõi trạng thái kết nối.

### Không chịu trách nhiệm

- Business Logic.
- Giao diện người dùng.
- Thực thi lệnh trên Machine.

---

## Agent

Agent chạy trên từng Machine.

### Responsibilities

- Kết nối tới Gateway.
- Thực thi Command.
- Thu thập thông tin hệ thống.
- Gửi kết quả về Gateway.
- Xin xác nhận của End User khi cần.
- Gửi Heartbeat định kỳ.

### Không chịu trách nhiệm

- Xác thực Administrator.
- Điều phối nhiều Machine.
- Quản lý giao diện.

---

# Internal Modules

## Web App

- Authentication
- Dashboard
- Machine Management
- Command Service
- Audit Log

---

## Gateway

- Authentication Manager
- Connection Manager
- Machine Registry
- Message Router
- Heartbeat Manager
- Stream Manager

---

## Agent

- Gateway Client
- Command Dispatcher
- Permission Manager
- Application Module
- Process Module
- Screen Module
- Webcam Module
- File Module
- Power Module
- Logger

---

# Connection Lifecycle

```text
Agent Start
      │
      ▼
Connect Gateway
      │
      ▼
Authenticate
      │
      ▼
Register Machine
      │
      ▼
Online
      │
      ▼
Heartbeat
      │
      ▼
Receive Command
      │
      ▼
Execute Command
      │
      ▼
Send Result
      │
      ▼
Disconnect
      │
      ▼
Reconnect
```

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
Agent
      │
Execute Command
      │
      ▼
Gateway
      │
      ▼
Web App
```

---

# Design Principles

## Single Responsibility

Mỗi thành phần chỉ đảm nhiệm một nhóm chức năng chính.

---

## Low Coupling

Các thành phần giao tiếp thông qua protocol thay vì phụ thuộc trực tiếp vào implementation của nhau.

---

## High Cohesion

Các chức năng liên quan được nhóm trong cùng một module.

---

## Scalability

Gateway có thể quản lý đồng thời nhiều Agent.

Kiến trúc cho phép bổ sung thêm Machine mà không cần thay đổi Web App.

---

## Maintainability

Các module được tách biệt rõ ràng, giúp dễ bảo trì và mở rộng.

---

# Design Decisions

## Tại sao sử dụng Gateway?

Gateway đóng vai trò là điểm trung gian duy nhất giữa Web App và Agent.

Lợi ích:

- Giảm coupling giữa các thành phần.
- Web App chỉ cần quản lý một kết nối.
- Dễ mở rộng nhiều Machine.
- Tập trung quản lý kết nối và trạng thái Agent.

---

## Tại sao Agent chủ động kết nối?

Agent luôn chủ động kết nối tới Gateway thay vì Gateway kết nối trực tiếp tới Agent.

Lợi ích:

- Không cần mở cổng trên Machine.
- Dễ xử lý khi Agent mất kết nối.
- Đơn giản hóa quá trình triển khai.

---

## Tại sao sử dụng WebSocket?

WebSocket hỗ trợ giao tiếp hai chiều theo thời gian thực.

Phù hợp cho:

- Heartbeat
- Live Screen
- Webcam Streaming
- Command & Response

---

# Assumptions

- Tất cả Machine đều chạy Windows.
- Agent đã được cài đặt trước.
- Các thành phần hoạt động trong cùng mạng LAN.

---

# Related Documents

- project_requirements.md
- system_specification.md
- communication_protocol.md
- security_design.md
- tech_stack.md
