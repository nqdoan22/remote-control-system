# Security Design

## Overview

Tài liệu này mô tả các cơ chế bảo mật được áp dụng trong hệ thống nhằm đảm bảo việc điều khiển từ xa được thực hiện an toàn, đúng quyền và có khả năng truy vết.

Các mục tiêu chính:

- Chỉ cho phép các thành phần hợp lệ tham gia hệ thống.
- Chỉ cho phép người dùng được xác thực thực hiện thao tác điều khiển.
- Bảo vệ quyền riêng tư của End User.
- Ghi nhận toàn bộ hoạt động để phục vụ kiểm tra và truy vết.

---

# Security Principles

Hệ thống được thiết kế theo các nguyên tắc sau:

- Authentication trước Authorization.
- Least Privilege.
- Defense in Depth.
- Secure by Default.
- Audit Everything.

---

# Trust Boundary

Hệ thống được chia thành các vùng tin cậy như sau:

```text
+-----------------------------------------+
| Administrator                           |
+-----------------------------------------+
                ▼

            Gateway

                ▼

            Client App

+-----------------------------------------+
| Gateway                                |
+-----------------------------------------+

============= Trust Boundary =============

+-----------------------------------------+
| Client App                             |
+-----------------------------------------+
                 │
                 ▼
+-----------------------------------------+
| Windows Operating System               |
+-----------------------------------------+
```

Mỗi Trust Boundary yêu cầu cơ chế xác thực riêng trước khi cho phép truy cập.

---

# Authentication

## Administrator Authentication

Administrator phải đăng nhập trước khi sử dụng hệ thống.

Sau khi xác thực thành công:

- Được phép truy cập Dashboard.
- Được phép gửi Command.
- Được phép xem Audit Log.

---

## Web App Authentication

Gateway chỉ chấp nhận kết nối từ Web App đã được xác thực.

Các kết nối không hợp lệ sẽ bị từ chối.

---

## Client App Authentication

Mỗi Client App có:

- machineId
- machineSecret

Gateway sử dụng hai thông tin này để xác thực Client App trước khi cho phép đăng ký vào hệ thống.

---

# Authorization

Sau khi xác thực thành công, Gateway sẽ kiểm tra quyền của từng Message.

Gateway chỉ cho phép:

### Web App

- Gửi Command.
- Nhận Response.
- Nhận Event.

---

### Client App

- Gửi Heartbeat.
- Gửi Response.
- Gửi Streaming Data.
- Gửi Event.

Client App không được phép gửi Command tới Client App khác hoặc Web App.

---

# Permission Confirmation

Các chức năng sau yêu cầu sự đồng ý của End User:

- Live Screen
- Webcam
- Key Logger
- Power Management

Luồng xử lý:

```text
Administrator

↓

Web App

↓

Gateway

↓

Client App

↓

Permission Dialog

↓

Accept / Reject

↓

Execute Command
```

Nếu End User từ chối:

- Không thực hiện Command.
- Trả về lỗi cho Administrator.

---

# File Sandbox

Client App chỉ được phép truy cập thư mục đã cấu hình.

Ví dụ:

```text
C:\RemoteControl\
```

Mọi yêu cầu truy cập ngoài thư mục này đều bị từ chối.

Điều này giúp hạn chế việc truy cập trái phép vào dữ liệu trên máy người dùng.

---

# Privacy Protection

Để bảo vệ quyền riêng tư của End User:

- Webcam phải hiển thị chỉ báo đang hoạt động.
- Live Screen phải được người dùng xác nhận.
- Key Logger phải được người dùng xác nhận.
- Power Control phải được người dùng xác nhận.

Người dùng luôn biết khi một chức năng nhạy cảm đang được sử dụng.

---

# Connection Security

Gateway giám sát trạng thái kết nối của Client App thông qua Heartbeat.

Nếu Heartbeat không được nhận trong khoảng thời gian quy định:

- Machine được đánh dấu Offline.
- Administrator được cập nhật trạng thái.
- Client App sẽ tự động kết nối lại khi có thể.

---

# Audit Logging

Mọi thao tác điều khiển đều được ghi nhận.

Thông tin bao gồm:

- Timestamp
- Administrator
- Machine
- Command
- Result
- Error (nếu có)

Audit Log phục vụ:

- Kiểm tra hoạt động.
- Truy vết sự cố.
- Phân tích bảo mật.

---

# Security Threats

## Giả mạo Administrator

Mitigation

- Authentication.

---

## Giả mạo Client App

Mitigation

- machineId.
- machineSecret.

---

## Command trái phép

Mitigation

- Authorization.
- Permission Checking.

---

## Truy cập trái phép vào tệp

Mitigation

- File Sandbox.

---

## Xâm phạm quyền riêng tư

Mitigation

- Permission Confirmation.
- Webcam Indicator.

---

## Client App mất kết nối

Mitigation

- Heartbeat.
- Auto Reconnect.

---

# Security Assumptions

Hệ thống giả định rằng:

- Gateway là thành phần đáng tin cậy.
- Administrator sử dụng tài khoản hợp lệ.
- Client App được cài đặt bởi người quản trị.
- Các thành phần hoạt động trong cùng mạng LAN.

---

# Design Decisions

## Tại sao Gateway kiểm tra quyền?

Để tránh Client App phải tự xử lý Authorization và giúp việc quản lý quyền tập trung hơn.

---

## Tại sao End User phải xác nhận?

Nhằm bảo vệ quyền riêng tư và đáp ứng yêu cầu của đồ án.

---

## Tại sao sử dụng File Sandbox?

Giới hạn phạm vi truy cập tệp giúp giảm thiểu rủi ro nếu Client App nhận được yêu cầu không hợp lệ.

---

## Tại sao ghi Audit Log?

Mọi thao tác đều có thể được kiểm tra và truy vết khi xảy ra sự cố.

---

# Related Documents

- project_requirements.md
- system_specification.md
- system_architecture.md
- communication_protocol.md
- tech_stack.md
