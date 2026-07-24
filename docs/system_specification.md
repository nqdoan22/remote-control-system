# System Specification

## Overview

Tài liệu này mô tả các chức năng và yêu cầu mà hệ thống phải đáp ứng.

Mục tiêu của tài liệu là xác định rõ **hệ thống cần làm gì**, không mô tả cách hệ thống được triển khai.

---

# System Objectives

Hệ thống phải đáp ứng các mục tiêu sau:

- Cho phép Administrator quản lý nhiều máy tính từ một giao diện duy nhất.
- Cung cấp khả năng giám sát trạng thái của từng Machine theo thời gian thực.
- Cho phép thực hiện các thao tác điều khiển từ xa trên Machine.
- Đảm bảo các chức năng nhạy cảm luôn được sự đồng ý của End User.
- Ghi nhận toàn bộ thao tác phục vụ kiểm tra và truy vết.

---

# System Components

Hệ thống gồm ba thành phần chính:

- Web App
- Gateway
- Client App

Chi tiết thiết kế của từng thành phần được mô tả trong `system_architecture.md`.

---

# User Roles

## Administrator

Administrator có thể:

- Đăng nhập hệ thống.
- Xem danh sách Machine.
- Theo dõi trạng thái Machine.
- Gửi yêu cầu điều khiển.
- Xem kết quả thực hiện.

---

## End User

End User là người đang sử dụng Machine.

End User có quyền:

- Đồng ý hoặc từ chối các yêu cầu sử dụng chức năng nhạy cảm.
- Nhận biết khi Webcam đang hoạt động.

---

# Sensitive Feature Policy

> **Single source:** Danh sách đầy đủ các chức năng nhạy cảm và message types tương ứng được định nghĩa tại `api_contract.md` — **Sensitive Feature List**.

Nguyên tắc chung:

- Mọi chức năng trong Sensitive Feature List đều yêu cầu End User xác nhận **trước** khi thực hiện.
- Nếu End User từ chối hoặc không phản hồi trong 30 giây, lệnh bị hủy và Administrator nhận thông báo lỗi.
- Các chức năng không có trong danh sách đó **không** yêu cầu xác nhận.

---

# Functional Specification

## Machine Management

Hệ thống phải cho phép:

- Hiển thị danh sách Machine.
- Hiển thị trạng thái Online hoặc Offline.
- Hiển thị Hostname.
- Hiển thị địa chỉ IP.
- Hiển thị thời điểm kết nối gần nhất.

---

## Application Management

Hệ thống phải cho phép:

- Liệt kê các ứng dụng đang chạy.
- Hiển thị mức sử dụng CPU của từng ứng dụng.
- Khởi động ứng dụng.
- Dừng ứng dụng.

---

## Process Management

Hệ thống phải cho phép:

- Liệt kê toàn bộ tiến trình.
- Hiển thị mức sử dụng CPU.
- Hiển thị mức sử dụng RAM.
- Kết thúc tiến trình.

---

## Screen Monitoring

Hệ thống phải hỗ trợ:

### Screenshot

- Chụp ảnh màn hình hiện tại.
- Không yêu cầu xác nhận của End User.

### Live Screen

- Xem trực tiếp màn hình của Machine.
- Yêu cầu xác nhận của End User (xem **Sensitive Feature Policy**).

---

## Webcam

Hệ thống phải hỗ trợ:

- Bật Webcam.
- Tắt Webcam.

Yêu cầu:

- End User phải xác nhận trước khi sử dụng (xem **Sensitive Feature Policy**).
- Machine phải hiển thị chỉ báo webcam đang hoạt động trong suốt thời gian sử dụng.

---

## Key Logger

Hệ thống phải hỗ trợ:

- Bắt đầu ghi thao tác bàn phím.
- Dừng ghi.

Yêu cầu:

- End User phải xác nhận trước khi sử dụng (xem **Sensitive Feature Policy**).

---

## File Transfer

Hệ thống phải hỗ trợ:

- Upload File.
- Download File.
- Liệt kê nội dung thư mục sandbox.

Ràng buộc:

- Chỉ được phép thao tác trong sandbox folder (mặc định: `C:\RemoteControl\`).
- Kích thước file tối đa: **50 MB**.
- Truy cập ngoài sandbox trả về lỗi `INVALID_PATH`.

---

## Power Management

Hệ thống phải hỗ trợ:

- Lock Screen.
- Restart.
- Shutdown.
- Sleep.

Yêu cầu:

- End User phải xác nhận trước khi thực hiện (xem **Sensitive Feature Policy**).

---

## Audit Log

Hệ thống phải lưu lại:

- Thời gian thực hiện.
- Administrator thực hiện.
- Machine được điều khiển.
- Loại thao tác (message type).
- Kết quả thực hiện (success / failed).
- Mã lỗi nếu thất bại.

Audit Log do Web App backend ghi vào SQLite. Schema chi tiết xem tại `security_design.md`.

---

# Non-functional Requirements

## Security

Hệ thống phải:

- Chỉ cho phép người dùng đã xác thực sử dụng.
- Bảo vệ các chức năng nhạy cảm.
- Ghi nhận đầy đủ nhật ký hoạt động.

---

## Performance

Hệ thống phải:

- Phản hồi nhanh trong môi trường LAN.
- Hỗ trợ nhiều Machine hoạt động đồng thời.

---

## Reliability

Hệ thống phải:

- Tự phát hiện Machine mất kết nối.
- Khôi phục kết nối khi có thể.

---

## Maintainability

Hệ thống phải:

- Có kiến trúc dễ mở rộng.
- Cho phép bổ sung chức năng mới mà ít ảnh hưởng tới các thành phần hiện có.

---

# Assumptions

Các giả định của hệ thống:

- Toàn bộ Machine sử dụng Windows.
- Các Machine nằm trong cùng mạng LAN.
- Client App đã được cài đặt trên Machine trước khi sử dụng.

---

# Out of Scope

Tài liệu này không mô tả:

- Kiến trúc hệ thống.
- Giao thức truyền thông.
- Cơ chế bảo mật.
- Công nghệ triển khai.

Các nội dung trên được mô tả trong các tài liệu liên quan.

---

# Related Documents

- project_requirements.md
- system_architecture.md
- communication_protocol.md
- security_design.md
- TECH_STACK.md
- **api_contract.md** — Sensitive Feature List, message payload spec
