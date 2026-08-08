# Project Requirements

## Overview

Tài liệu này định nghĩa các yêu cầu kỹ thuật và nghiệp vụ (Business & Technical Requirements) của dự án **Hệ thống điều khiển và giám sát máy tính từ xa qua mạng LAN**.

Mục tiêu cốt lõi của dự án là xây dựng một hệ thống quản trị tập trung (Centralized Management) cho phép Administrator theo dõi và điều khiển nhiều máy tính Windows Client cùng lúc. Điểm nổi bật của hệ thống là **cơ chế bảo vệ quyền riêng tư (Privacy-first)**: mọi thao tác nhạy cảm đều phải được sự đồng ý (Explicit Consent) từ người dùng đang ngồi trực tiếp tại máy bị điều khiển.

---

## Project Goals (Mục tiêu dự án)

1. **Quản trị tập trung:** Giám sát và điều khiển hàng loạt máy tính từ một giao diện Web duy nhất, không cần cài đặt phần mềm điều khiển riêng trên máy Admin.
2. **Thời gian thực (Real-time):** Giao tiếp độ trễ thấp thông qua công nghệ WebSocket.
3. **Bảo mật & Quyền riêng tư:** Tôn trọng tuyệt đối End User bằng cơ chế xin quyền (Popup/Timeout) và ghi nhận nhật ký (Audit Log) mọi hành động.
4. **Kiến trúc chuẩn mực:** Thể hiện rõ tư duy thiết kế phần mềm linh hoạt (3-Tier Architecture), phân tách trách nhiệm rõ ràng giữa các module.

---

## System Scope (Phạm vi hệ thống)

- **Môi trường hoạt động:** Mạng nội bộ (LAN).
- **Hệ điều hành:** Server/Gateway chạy trên mọi nền tảng (Windows/Linux/macOS) hỗ trợ Python; Client App (Agent) chỉ hỗ trợ **Windows**.
- **Kiến trúc 3 lớp (3-Tier):**
  - **Web App (React/FastAPI):** Giao diện quản trị viên và xử lý logic lưu trữ, xác thực.
  - **Gateway (Python Asyncio/WebSockets):** Trạm trung chuyển thông điệp tốc độ cao (Broker).
  - **Client App (Python/PyQt6):** Ứng dụng chạy ngầm trên máy End User để thực thi lệnh.

---

## Functional Requirements (Yêu cầu chức năng)

Các chức năng được chia làm 2 nhóm dựa trên mức độ nhạy cảm và yêu cầu bảo mật.

### Nhóm 1: Standard Features (Chức năng tiêu chuẩn - Thực thi ngay)

- **Machine Management (Quản lý thiết bị):**
  - Hiển thị danh sách các máy Client đã kết nối.
  - Cập nhật trạng thái Online/Offline theo thời gian thực (qua Heartbeat).
- **Process & App Management (Quản lý Tiến trình/Ứng dụng):**
  - Liệt kê danh sách các ứng dụng (Apps) và tiến trình (Processes) đang chạy.
  - Hiển thị tài nguyên tiêu thụ: CPU, RAM.
  - Yêu cầu khởi chạy hoặc ép buộc kết thúc (Kill) một ứng dụng/tiến trình.
- **Screen Monitoring (Giám sát màn hình cơ bản):**
  - Chụp ảnh màn hình hiện tại (Screenshot - 1 khung hình tĩnh).
- **Audit Logging (Nhật ký):**
  - Web App tự động ghi lại lịch sử thao tác của Admin (Ai ra lệnh, ra lệnh gì, cho máy nào, vào lúc nào, kết quả ra sao).

### Nhóm 2: Privacy-Sensitive Features (Chức năng nhạy cảm - Yêu cầu xác nhận)

> **Quy tắc bắt buộc:** Khi Admin kích hoạt các chức năng này, Client App phải hiển thị Popup xin quyền. Chỉ khi End User bấm "Accept" (hoặc từ chối/quá 15s Timeout), lệnh mới được xử lý.

- **Live Screen (Màn hình trực tiếp):**
  - Truyền phát liên tục màn hình của End User về Web App.
- **Webcam Control:**
  - Bật/Tắt Webcam để truyền phát hình ảnh.
  - **Ràng buộc:** Phải hiển thị một đèn báo/chỉ báo (Indicator) rõ ràng trên màn hình End User liên tục trong suốt quá trình Webcam mở.
- **Input Audit Log (Ghi phím):**
  - Bắt đầu/Dừng ghi nhận thao tác gõ phím của End User.
- **Power Management (Điều khiển nguồn):**
  - Tắt máy (Shutdown), Khởi động lại (Restart), Khóa màn hình (Lock), Ngủ (Sleep).

### Nhóm 3: Constrained Features (Chức năng bị giới hạn)
- **File Transfer (Quản lý tệp tin):**
  - Upload tệp từ Web lên Client và Download tệp từ Client về Web.
  - **Ràng buộc (Sandboxing):** Chỉ được phép thao tác bên trong một thư mục chỉ định (VD: `C:\AgentSandbox\`). Mọi nỗ lực thoát khỏi thư mục này đều bị từ chối.

---

## Non-functional Requirements (Yêu cầu phi chức năng)

- **Performance (Hiệu năng):**
  - Gateway có khả năng duy trì hàng chục/trăm kết nối WebSocket đồng thời mà không bị nghẽn (Blocking).
  - Client App không được tiêu tốn quá nhiều CPU/RAM khi chạy ngầm (Idle state).
- **Usability (Tính khả dụng):**
  - Web App có giao diện trực quan (Dashboard), dễ điều hướng.
  - Popup xin quyền trên Client App phải luôn nổi lên trên cùng (Always-on-top) để người dùng không bỏ lỡ.
- **Reliability (Độ tin cậy):**
  - Client App tự động kết nối lại (Auto-reconnect) vào Gateway khi rớt mạng hoặc Gateway khởi động lại.
  - Không treo giao diện (GUI) của Client App khi đang chờ mạng hoặc thực thi lệnh nặng.

---

## Deliverables (Sản phẩm bàn giao)

Để hoàn thành đồ án, nhóm cam kết nộp đủ các thành phần sau:
1. **Source Code:** Mã nguồn hoàn chỉnh của cả 3 component (Web, Gateway, Client).
2. **Video Demo:** Video quay lại quá trình vận hành, có thuyết minh giải thích luồng hoạt động.
3. **Report:** Báo cáo thiết kế phần mềm chi tiết bằng tiếng Việt.
4. **AI Log:** Nhật ký (Prompts/Chat history) thể hiện quá trình tương tác và ứng dụng AI trong việc phát triển dự án.
5. **Live System:** Hệ thống có khả năng chạy thực tế trong mạng LAN khi giảng viên kiểm tra.

---

## Out of Scope (Ngoài phạm vi dự án)

Những tính năng/yêu cầu sau sẽ **không** được hỗ trợ trong phiên bản đồ án này nhằm tập trung vào các chức năng cốt lõi:
- Cấu hình NAT Traversal (Port Forwarding, STUN/TURN) để điều khiển qua Internet.
- Remote Desktop hoàn chỉnh (không hỗ trợ Admin click chuột hay gõ phím trực tiếp lên màn hình Client).
- Phân quyền đa cấp độ cho Web App (Chỉ có 1 quyền Admin duy nhất).
- Tính sẵn sàng cao (High Availability) như Clustering hoặc chạy nhiều Gateway cùng lúc.

---

## Related Documents

- `system_specification.md`
- `system_architecture.md`
- `communication_protocol.md`
- `security_design.md`
- `TECH_STACK.md`
