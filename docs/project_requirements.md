# Project Requirements

## Overview

Dự án xây dựng một hệ thống điều khiển và giám sát nhiều máy tính Windows thông qua trình duyệt web trong cùng mạng LAN.

Hệ thống cho phép quản trị viên theo dõi trạng thái của các máy tính và thực hiện một số thao tác điều khiển từ xa một cách an toàn. Các chức năng nhạy cảm phải có cơ chế xác nhận từ người dùng trên máy được điều khiển nhằm đảm bảo quyền riêng tư và an toàn thông tin.

---

## Project Goals

- Điều khiển nhiều máy tính từ một giao diện duy nhất.
- Giám sát trạng thái hoạt động của từng máy theo thời gian thực.
- Thực hiện các thao tác quản trị từ xa.
- Đảm bảo các chức năng nhạy cảm luôn được bảo vệ.
- Thể hiện tư duy thiết kế phần mềm, kiến trúc hệ thống và bảo mật.

---

## System Scope

Hệ thống chỉ hoạt động trong môi trường mạng LAN.

Kiến trúc gồm ba thành phần độc lập:

- Web App
- Gateway
- Client App

Trong đó:

- **Web App** là giao diện dành cho Administrator.
- **Gateway** là trung gian quản lý toàn bộ kết nối giữa Web App và Client App.
- **Client App** chạy trên từng máy được điều khiển và thực thi các lệnh.

---

## General Requirements

- Web App hoạt động trên trình duyệt.
- Backend bắt buộc sử dụng Python.
- Toàn bộ hệ thống chạy trên Windows.
- Hỗ trợ điều khiển đồng thời nhiều máy.
- Giao tiếp thời gian thực bằng WebSocket.
- Client App chủ động kết nối tới Gateway.
- Gateway là điểm kết nối duy nhất giữa Web App và Client App.

---

## Functional Requirements

### Machine Management

- Hiển thị danh sách máy.
- Hiển thị trạng thái Online/Offline.
- Cho phép chọn máy để điều khiển.

### Application Management

- Liệt kê các ứng dụng đang chạy.
- Hiển thị mức sử dụng CPU.
- Khởi động ứng dụng.
- Dừng ứng dụng.

### Process Management

- Liệt kê toàn bộ tiến trình.
- Hiển thị CPU.
- Hiển thị RAM.
- Kết thúc tiến trình.

### Screen Monitoring

#### Screenshot

- Chụp ảnh màn hình.

#### Live Screen

- Xem màn hình trực tiếp.

Chức năng Live Screen yêu cầu người dùng trên máy xác nhận trước khi bắt đầu.

### Webcam

- Bật webcam.
- Tắt webcam.

Chức năng này yêu cầu người dùng xác nhận.

Khi webcam hoạt động phải hiển thị chỉ báo để người dùng biết webcam đang được sử dụng.

### Key Logger

- Bắt đầu ghi nhận thao tác bàn phím.
- Dừng ghi nhận.

Chức năng này yêu cầu người dùng xác nhận trước khi sử dụng.

### File Transfer

- Upload tệp.
- Download tệp.

Chỉ được phép thao tác trong thư mục đã cấu hình.

### Power Management

- Lock Screen.
- Restart.
- Shutdown.
- Sleep.

Chức năng này yêu cầu người dùng xác nhận.

---

## Security Requirements

Hệ thống phải đảm bảo các yêu cầu sau:

- Administrator phải đăng nhập trước khi sử dụng.
- Gateway chỉ chấp nhận các kết nối hợp lệ.
- Client App phải được xác thực trước khi tham gia hệ thống.
- Các chức năng nhạy cảm yêu cầu sự đồng ý của End User.
- Ghi nhận toàn bộ thao tác điều khiển để phục vụ kiểm tra.
- Không cho phép truy cập tệp ngoài thư mục được cấp quyền.

---

## Non-functional Requirements

- Hỗ trợ nhiều Client App hoạt động đồng thời.
- Hoạt động ổn định trong môi trường mạng LAN.
- Kiến trúc dễ mở rộng.
- Các module độc lập và dễ bảo trì.
- Hỗ trợ giao tiếp thời gian thực.

---

## Deliverables

Nhóm cần nộp:

- Source code.
- Video demo có thuyết minh.
- Báo cáo thiết kế phần mềm bằng tiếng Việt.
- Nhật ký làm việc với AI.
- Hệ thống phải chạy được khi giảng viên kiểm tra.

---

## Out of Scope

Những nội dung sau không nằm trong phạm vi của dự án:

- Điều khiển máy tính qua Internet.
- NAT Traversal.
- Remote Desktop hoàn chỉnh.
- Hệ thống đa người dùng.
- Đồng bộ dữ liệu giữa nhiều Gateway.

---

## Related Documents

- system_specification.md
- system_architecture.md
- communication_protocol.md
- security_design.md
- tech_stack.md
