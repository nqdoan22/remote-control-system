# Security Design

## Overview

Tài liệu này mô tả chi tiết các cơ chế bảo mật, mô hình rủi ro và các chốt chặn an toàn được áp dụng trong hệ thống. 

Mục tiêu cốt lõi của thiết kế bảo mật là đảm bảo việc điều khiển từ xa được thực hiện **an toàn, đúng thẩm quyền, tôn trọng quyền riêng tư của End User**, và **lưu vết toàn vẹn (Non-repudiation)** mọi hành động.

---

# Security Principles (Nguyên tắc Bảo mật)

Hệ thống được thiết kế dựa trên 5 nguyên tắc bảo mật tiêu chuẩn:

1. **Authentication trước Authorization:** Mọi kết nối phải được xác thực danh tính trước khi kiểm tra quyền hạn.
2. **Least Privilege (Quyền hạn tối thiểu):** Client App chỉ được cấp quyền truy cập vào một thư mục cụ thể (Sandbox), không có quyền can thiệp vào các tệp tin hệ thống cốt lõi của Windows.
3. **Defense in Depth (Bảo mật nhiều lớp):** Áp dụng bảo vệ ở cả 3 tầng (Web App chặn UI, Gateway chặn Route, Client App chặn thực thi).
4. **Explicit Consent (Minh bạch thông tin):** Mọi hành động xâm phạm quyền riêng tư đều phải được sự đồng ý rõ ràng (Accept) từ người dùng cuối.
5. **Audit Everything (Truy vết toàn diện):** Mọi lệnh điều khiển đều được ghi log bất biến vào cơ sở dữ liệu.

---

# Trust Boundary (Ranh giới Tín nhiệm)

Hệ thống chia làm các vùng tín nhiệm (Trust Zones). Dữ liệu đi qua ranh giới giữa các vùng (Trust Boundary) đều bị coi là "không an toàn" cho đến khi được xác thực và kiểm tra.

```text
 [ Admin User ]
       │ (1) Authenticated UI
       ▼
+------------------------------------------------+
|                   WEB APP                      | (High Trust)
+------------------------------------------------+
       │
       │ (2) JWT / Secure Token via WebSocket
       ▼
================ TRUST BOUNDARY ==================
       │
+------------------------------------------------+
|                   GATEWAY                      | (Medium Trust - Broker)
+------------------------------------------------+
       │
       │ (3) Client ID & Secret Authentication
       ▼
================ TRUST BOUNDARY ==================
       │
+------------------------------------------------+
|                 CLIENT APP                     | (Low Trust - Exists on User PC)
+------------------------------------------------+
       │
       │ (4) Strict OS API Calls & Sandboxing
       ▼
+------------------------------------------------+
|           WINDOWS OPERATING SYSTEM             |
+------------------------------------------------+

```

---

# Authentication (Xác thực)

## 1. Administrator Authentication (Web App)

* Quản trị viên phải đăng nhập bằng Username và Password.
* Mật khẩu lưu trong cơ sở dữ liệu (SQLite) **bắt buộc phải được băm (hash) bằng thuật toán Bcrypt**, tuyệt đối không lưu dạng plain-text.
* Đăng nhập thành công, hệ thống cấp một **JWT (JSON Web Token)** có thời hạn.
* Mọi API hoặc luồng WebSocket từ Web App gửi đi đều phải đính kèm JWT này để Gateway kiểm chứng.

## 2. Client App Authentication (Agent)

* Mỗi máy cài Client App được cấp một cặp khóa cấu hình sẵn trong `config.py`:
* `CLIENT_ID` (Định danh máy)
* `CLIENT_SECRET` (Mã bí mật kết nối)


* Gateway sử dụng cặp thông tin này để xác thực Client App khi mở kết nối WebSocket ban đầu. Nếu sai Secret, Gateway đóng kết nối (Force Close) ngay lập tức.

---

# Authorization (Phân quyền truy cập)

Gateway hoạt động như một chốt chặn kiểm soát luồng đi của Message (JSON RPC).

* **Từ Web App (Admin):** Chỉ được phép gửi các thông điệp loại `Command` (Yêu cầu thực thi) và nhận `Event/Response`. Tuyệt đối không được gửi lệnh giả mạo `Heartbeat`.
* **Từ Client App (Agent):** Chỉ được phép gửi thông điệp loại `Response` (Kết quả trả về), `Stream` (Hình ảnh), và `Heartbeat`. **Client App không được phép gửi Command điều khiển chéo sang một Client App khác.**

---

# User Consent & Privacy (Bảo vệ Quyền riêng tư)

Đây là cơ chế bảo mật quan trọng nhất phía End User. Các chức năng: **Live Screen, Webcam, Keylogger, Power Control** bị khóa mặc định.

## Luồng cấp quyền (Consent Flow):

1. Khi có lệnh nhạy cảm, Client App (Main Thread) bật một **Popup PyQt6 (Always-on-Top)** trên chính giữa màn hình người dùng.
2. Popup mô tả rõ: *"Admin đang yêu cầu tính năng [Webcam/Screen]. Bạn có đồng ý không?"*
3. **Timeout Mechanism (Bảo vệ chống treo):** Nếu End User không bấm `Accept` hoặc `Reject` trong vòng **15 giây**, Client App tự động đánh giá là **TIMEOUT (Tương đương REJECT)** và đóng cửa sổ, chặn luồng thực thi.

## Cảnh báo Trực quan (Visual Indicators):

* **Webcam:** Bất cứ khi nào ống kính Camera đang được sử dụng để stream, một cửa sổ (Red Indicator) chứa chấm đỏ nhấp nháy sẽ hiển thị ở góc màn hình End User và **không thể bị ẩn đi (Un-hideable)**.

---

# File Sandboxing (Cô lập hệ thống tệp)

Chức năng File Transfer tiềm ẩn rủi ro rất lớn liên quan đến việc đánh cắp hoặc phá hoại dữ liệu (Directory Traversal Attack).

 * **Quy tắc Sandbox:** Client App chỉ được phép liệt kê, upload và download các tệp nằm gọn trong thư mục sandbox (cấu hình trong `config.py`, mặc định `~/AgentSandbox`).
* **Sanitize Input (Làm sạch đầu vào):** Mọi đường dẫn do Admin gửi xuống đều được Client App kiểm tra. Các ký tự điều hướng ngược như `../`, `..\`, hoặc đường dẫn tuyệt đối ra ngoài Sandbox (`C:\Windows`) sẽ bị module `file_manager.py` **từ chối ngay lập tức**.

---

# Audit Logging (Nhật ký Truy vết)

Mọi lệnh điều khiển (Command) từ lúc phát đi đến khi có kết quả đều phải lưu vào bảng `audit_logs` tại Backend.

Thông tin lưu trữ bao gồm:

* **Timestamp:** Thời gian chính xác (ISO 8601).
* **Admin ID:** Định danh người ra lệnh.
* **Machine ID:** Đích đến của lệnh.
* **Action:** Tên hành động (VD: `webcam.start`, `process.kill`).
* **Status:** Kết quả (`Success`, `User_Denied`, `Timeout`, `Failed`).

> **Nguyên tắc:** Log là bất biến (Immutable). Không cung cấp API xóa hoặc sửa log trên Web App.

---

# Threat Model & Mitigations (Các rủi ro và Biện pháp phòng chống)

| Rủi ro / Các kiểu tấn công (Threat) | Biện pháp phòng chống (Mitigation) |
| --- | --- |
| **Giả mạo Admin ra lệnh (Spoofing)** | Bắt buộc xác thực bằng JWT cho mọi kết nối từ Web App. Token hết hạn sẽ bị loại bỏ. |
| **Giả mạo Client App kết nối** | Xác thực bằng `CLIENT_ID` và `CLIENT_SECRET` tĩnh tại Gateway. |
| **Lộ mật khẩu Database** | Băm mật khẩu (Hash) bằng thuật toán Bcrypt có Salt. |
| **Directory Traversal (Truy cập file trái phép)** | Áp dụng File Sandboxing, loại bỏ ký tự `../` tại Client App. |
| **Xâm phạm đời tư ngầm (Spying)** | Buộc phải qua Popup xin quyền. Có Timeout 15s. Có chấm đỏ cảnh báo Webcam. |
| **Mất kết nối đột ngột (Availability)** | Triển khai Ping/Pong Heartbeat mỗi 5s. Tự động kết nối lại (Auto-Reconnect) từ Client. |

---

# Design Decisions (Quyết định thiết kế)

## 1. Tại sao để Client App tự quyết định Timeout (15s)?

Nếu Gateway giữ Timeout, có thể xảy ra độ trễ mạng khiến lệnh "Hủy" về trễ, dẫn đến việc cửa sổ Popup treo trên màn hình End User. Xử lý Timeout trực tiếp tại vòng lặp `asyncio` của Client App đảm bảo tính tức thời và giải phóng tài nguyên GUI ngay lập tức.

## 2. Tại sao Backend Web App lại ghi log thay vì Gateway?

Gateway được thiết kế là một Broker cực nhanh và nhẹ (Stateless). Nếu Gateway phải lo việc ghi vào SQLite, nó có thể bị thắt nút cổ chai (Bottleneck) khi có hàng ngàn message. Do đó, Gateway chỉ "chuyển tiếp" kết quả về Backend của Web App, và Backend sẽ chịu trách nhiệm ghi Database.

---

# Related Documents

* `project_requirements.md`
* `system_specification.md`
* `system_architecture.md`
* `communication_protocol.md`
* `TECH_STACK.md`

```
