# System Specification

## Overview

Tài liệu này mô tả chi tiết các chức năng, yêu cầu kinh doanh và các ràng buộc phi chức năng mà hệ thống phải đáp ứng.

Mục tiêu của tài liệu là xác định rõ **hệ thống cần làm gì (What to do)**, đảm bảo tính toàn vẹn của dữ liệu và quyền riêng tư của End User, không mô tả cách hệ thống được triển khai kỹ thuật.

---

# System Objectives

Hệ thống phải đáp ứng các mục tiêu sau:

- Cung cấp một Web App tập trung cho phép Administrator quản lý và giám sát nhiều máy tính (Machine) trong mạng LAN.
- Theo dõi trạng thái kết nối và tài nguyên phần cứng của từng Machine theo thời gian thực.
- Cho phép thực hiện các thao tác điều khiển từ xa một cách mượt mà và độ trễ thấp.
- **Tôn trọng quyền riêng tư:** Đảm bảo các chức năng can thiệp sâu (nhạy cảm) phải được sự đồng ý rõ ràng của End User.
- **Tính minh bạch và truy vết:** Ghi nhận toàn bộ thao tác của Administrator vào hệ thống Audit Log chống chối bỏ.

---

# System Components

Hệ thống hoạt động dựa trên sự tương tác của ba thành phần chính:

- **Web App:** Giao diện điều khiển dành cho Administrator.
- **Gateway:** Trạm trung chuyển thông điệp thời gian thực (WebSocket).
- **Client App (Agent):** Ứng dụng chạy ngầm trên máy bị điều khiển, xử lý lệnh và tương tác với End User.

*(Chi tiết thiết kế của từng thành phần được mô tả trong `system_architecture.md`)*

---

# User Roles

## 1. Administrator (Quản trị viên)
Là người vận hành hệ thống thông qua Web App.
- Đăng nhập bảo mật vào hệ thống.
- Xem danh sách, tìm kiếm và lọc trạng thái các Machine.
- Gửi yêu cầu điều khiển/giám sát đến một hoặc nhiều Machine.
- Xem kết quả thực hiện và theo dõi nhật ký hoạt động (Audit Log).

## 2. End User (Người dùng cuối)
Là người đang trực tiếp sử dụng Machine (máy tính cài Client App).
- Nhận thông báo (Popup) khi Administrator yêu cầu sử dụng các tính năng giám sát.
- **Quyền quyết định:** Có quyền Chấp nhận (Accept) hoặc Từ chối (Reject) các yêu cầu nhạy cảm.
- Nhận biết trực quan khi các thiết bị ghi hình (Webcam) đang hoạt động.

---

# Functional Specification (Yêu cầu chức năng)

## 1. Machine Management (Quản lý Máy tính)
Hệ thống phải cho phép Administrator:
- Hiển thị danh sách toàn bộ các Machine đã từng kết nối.
- Cập nhật trạng thái thời gian thực: `Online` hoặc `Offline`.
- Hiển thị thông tin cơ bản: Hostname, Địa chỉ IP (LAN), OS Version.
- Hiển thị thời điểm kết nối (Last seen).
- Tìm kiếm/Lọc Machine theo Tên hoặc IP.

## 2. Permission Management & Consent (Quản lý Cấp quyền)
*Đây là module cốt lõi đảm bảo an toàn thông tin.*
- Mọi chức năng thuộc nhóm Nhạy cảm phải kích hoạt Popup xin quyền trên màn hình End User.
- **Popup Always-on-Top:** Cửa sổ xin quyền phải hiển thị nổi lên trên cùng để đảm bảo End User nhìn thấy.
- **Timeout Mechanism:** Nếu End User không phản hồi trong vòng **15 giây**, hệ thống mặc định coi là Từ chối (Timeout = Auto Reject) và báo lỗi về Web App.

## 3. Application Management (Quản lý Ứng dụng)
Hệ thống phải cho phép Administrator:
- Liệt kê các ứng dụng có giao diện đang chạy trên Machine.
- Hiển thị mức sử dụng CPU (%) của từng ứng dụng.
- Khởi động một ứng dụng mới (Start).
- Buộc dừng một ứng dụng đang chạy (Stop/Kill).

## 4. Process Management (Quản lý Tiến trình)
Hệ thống phải cho phép Administrator:
- Liệt kê toàn bộ tiến trình (Background & Foreground processes).
- Hiển thị thông số chi tiết: Process ID (PID), %CPU, %RAM sử dụng.
- Tìm kiếm tiến trình theo tên.
- Kết thúc một tiến trình cụ thể (Kill Process).

## 5. Screen Monitoring (Giám sát Màn hình)
Hệ thống phải hỗ trợ 2 chế độ giám sát và **cả 2 đều yêu cầu End User xác nhận**:
- **Screenshot:** Chụp và tải về một bức ảnh màn hình hiện tại của Machine.
- **Live Screen:** Truyền phát trực tiếp (Stream) màn hình của Machine về Web App.
  - Cho phép Administrator thay đổi chất lượng ảnh/tốc độ khung hình (FPS) để tối ưu băng thông mạng LAN.
  - Administrator có quyền chủ động ngắt stream bất cứ lúc nào.

## 6. Webcam Monitoring
Hệ thống phải hỗ trợ:
- Gửi yêu cầu bật Webcam trên Machine để truyền luồng hình ảnh về Web App.
- **Ràng buộc an toàn:** Bắt buộc End User phải xác nhận trước khi sử dụng.
- **Chỉ báo trực quan:** Khi Webcam đang truyền dữ liệu, Machine **bắt buộc** phải hiển thị một khung cảnh báo (Chấm đỏ nhấp nháy) trên màn hình End User.

## 7. Key Logger
Hệ thống phải hỗ trợ:
- Bắt đầu ghi nhận các phím bấm và cửa sổ ứng dụng đang được thao tác.
- Truyền dữ liệu phím bấm về Web App (Real-time hoặc theo đợt).
- Dừng ghi nhận.
- **Ràng buộc an toàn:** Bắt buộc End User phải xác nhận mới được phép kích hoạt.

## 8. File Transfer (Truyền tải Tệp tin)
Hệ thống phải hỗ trợ:
- Liệt kê danh sách các File/Folder hiện có.
- Upload File (Từ Web App sang Machine).
- Download File (Từ Machine về Web App).
- **Ràng buộc Sandboxing:** Mọi thao tác truy xuất, tải lên, tải xuống chỉ được phép thực hiện trong thư mục sandbox (cấu hình trong `config.py`, mặc định `~/AgentSandbox`). Bất kỳ truy cập nào ra ngoài thư mục này đều bị hệ thống chặn đứng.

## 9. Power Management (Quản lý Nguồn)
Hệ thống phải cho phép gửi các lệnh hệ thống:
- Lock Screen (Khóa màn hình).
- Restart (Khởi động lại).
- Shutdown (Tắt máy).
- Sleep (Chế độ ngủ).
- **Ràng buộc an toàn:** Bắt buộc End User phải xác nhận trước khi thực hiện để tránh làm mất dữ liệu người dùng đang làm việc.

## 10. System Audit Log (Nhật ký Hệ thống)
Hệ thống phải lưu trữ lịch sử mọi thao tác điều khiển:
- Thời gian thực hiện (Timestamp).
- Thông tin Administrator thực hiện lệnh.
- ID của Machine nhận lệnh.
- Loại thao tác (Ví dụ: `Request_Screenshot`, `Kill_Process`).
- Kết quả thực hiện (`Success`, `User_Denied`, `Timeout`, `Failed`).
- Administrator có thể xem, tìm kiếm và lọc Audit Log theo thời gian hoặc theo Machine.

---

# Non-functional Requirements (Yêu cầu Phi chức năng)

## 1. Security (Bảo mật)
- Giao diện Web App phải yêu cầu đăng nhập (Authentication) thông qua JSON Web Token (JWT).
- Mật khẩu của Administrator phải được mã hóa (Bcrypt) trong cơ sở dữ liệu.
- Các yêu cầu từ Web App tới Gateway phải đính kèm Token hợp lệ.

## 2. Performance (Hiệu năng)
- Hệ thống thiết kế cho mạng LAN, yêu cầu độ trễ truyền lệnh (từ lúc click đến lúc hiện Popup) **dưới 500ms**.
- Gateway phải có khả năng duy trì kết nối đồng thời với tối thiểu **50 Machine** mà không suy giảm hiệu năng.
- Quá trình Live Screen và Live Webcam phải tối ưu hóa bộ nhớ, không làm %CPU của máy Client tăng quá 20%.

## 3. Reliability & Resilience (Độ tin cậy)
- Gateway và Client App sử dụng cơ chế **Heartbeat (Ping/Pong)** mỗi 5-10 giây để kiểm tra kết nối.
- Tự động phát hiện Machine mất mạng và đổi trạng thái sang `Offline` sau 3 lần rớt Heartbeat.
- Client App tự động thực hiện reconnect (kết nối lại) ngầm khi Gateway hoặc mạng LAN hoạt động trở lại.

## 4. Maintainability (Tính bảo trì)
- Kiến trúc xử lý lệnh (Message Handler) cần được thiết kế dạng Module. Khi cần thêm một chức năng mới (VD: Micro monitoring), nhà phát triển chỉ cần cắm thêm module vào Backend/Client mà không phá vỡ logic cũ.

---

# Assumptions (Giả định)

- Toàn bộ Machine bị điều khiển sử dụng hệ điều hành **Windows (10/11)**.
- Các Machine và Gateway nằm trong cùng một mạng LAN (Local Area Network) ổn định.
- Client App (Agent) đã được cấp quyền khởi chạy và được cấu hình đúng địa chỉ IP của Gateway trước khi đưa vào vận hành.

---

# Out of Scope (Ngoài phạm vi tài liệu)

Tài liệu này KHÔNG mô tả:
- Kiến trúc mạng chi tiết hoặc cách cấu hình Router/Switch LAN.
- Chi tiết API Endpoints hay Payload JSON của Web Socket.
- Cách cài đặt ngôn ngữ lập trình, cấu trúc thư mục (Xem `TECH_STACK.md`).
- Các bản vá lỗi hệ điều hành Windows.

*(Các nội dung trên được mô tả trong các tài liệu thiết kế kỹ thuật tương ứng).*

---

# Related Documents

- `project_requirements.md`
- `system_architecture.md`
- `communication_protocol.md`
- `security_design.md`
- `TECH_STACK.md`

```