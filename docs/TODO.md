# TODO – Remote Control System

> Danh sách các hạng mục chưa hoàn thiện. Cập nhật khi hoàn thành từng mục.

---

## Web App – Backend

- [ ] Cơ chế xác thực JWT đầy đủ: login, refresh token, middleware bảo vệ route.
- [ ] `gateway_client.py`: implement kết nối Backend ↔ Gateway, định nghĩa kênh điều khiển và kênh stream riêng biệt.

## Gateway

- [ ] `connection_manager.py`: sinh `machine_id` duy nhất, lưu trạng thái kết nối, broadcast sự kiện online/offline.
- [ ] `message_handler.py`: implement điều phối đầy đủ theo toàn bộ bảng message ở `SYSTEM_SPEC.md` mục 4.2.

## Web App – Frontend

- [ ] Kết nối WebSocket cho các module real-time: Live Screen, Key Logger, Webcam.
- [ ] Render dữ liệu stream real-time trên giao diện (frame ảnh, log phím...).

## Client App

- [ ] Implement từng Module theo Win32 API / thư viện tương ứng (xem `TECH_STACK.md` mục 5).
- [ ] `PermissionService`: đọc/ghi cấu hình quyền từ file (JSON hoặc XML) để lưu giữa các lần khởi động.

## Bảo mật

- [ ] Mã hóa kết nối: chuyển toàn bộ WebSocket sang WSS (WebSocket Secure / TLS).
- [ ] Xác thực Client App với Gateway để ngăn máy lạ kết nối vào hệ thống.
