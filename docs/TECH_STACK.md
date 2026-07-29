# TECH_STACK.md

# Tech Stack & Implementation Details

## Overview

Tài liệu này mô tả chi tiết công nghệ, thư viện, quy ước lập trình, mô hình bảo mật và thiết kế hệ thống điều khiển/giám sát máy tính từ xa trong mạng nội bộ (LAN).

Hệ thống được thiết kế theo mô hình **3-Tier Architecture** gồm **Web App (Admin Panel)**, **Gateway Server (WS Broker)**, và **Client Agent (Python PyQt6)**. Dự án tuân thủ nghiêm ngặt nguyên tắc **Minh bạch thông tin (User Consent)** và **Phân quyền truy cập an toàn (Sandboxing & Audit Logging)**.

---

## 1. Technology Stack

| Thành phần | Công nghệ / Framework | Vai trò |
| --- | --- | --- |
| **Frontend Admin** | ReactJS + Vite | Giao diện điều khiển dành cho Quản trị viên (Browser-based) |
| **Backend REST API** | FastAPI (Python 3.10+) | Xử lý xác thực, cấp phát Token, lưu trữ Audit Log & quản lý Database |
| **Gateway Server** | Python `asyncio` + `websockets` | Trạm trung chuyển dữ liệu WebSocket thời gian thực giữa Web App và Agent |
| **Client Agent** | Python 3.10+ (PyQt6) | Ứng dụng chạy trên máy bị điều khiển, xử lý lệnh và hiển thị popup xin quyền |
| **Database** | SQLite + SQLAlchemy ORM | Lưu trữ tài khoản Admin, danh sách máy Client, và nhật ký thao tác (Audit Logs) |
| **Giao thức truyền tin** | WebSocket (JSON RPC format) | Truyền nhận dữ liệu thời gian thực hai chiều giữa các thành phần |

---

## 2. Main Libraries & Dependencies

### Backend & Gateway (Python)

* **FastAPI & Uvicorn:** Framework Web API hiệu năng cao, hỗ trợ sinh Swagger Docs tự động.
* **websockets & asyncio:** Xử lý hàng nghìn kết nối WebSocket đồng thời không nghẽn.
* **SQLAlchemy & Pydantic:** Quản lý ORM cơ sở dữ liệu và validate dữ liệu đầu vào/đầu ra.
* **PyJWT & Passlib (Bcrypt):** Mã hóa mật khẩu Admin và xác thực Session bằng JWT (JSON Web Token).

### Client App (Python Agent)

* **PyQt6:** Xây dựng giao diện ứng dụng Agent (Cửa sổ trạng thái, Popup xin quyền người dùng, Đèn đỏ cảnh báo Webcam).
* **websockets:** Kết nối duy trì (Persistent WebSocket Client) gửi heartbeat và nhận lệnh từ Gateway.
* **psutil:** Truy xuất danh sách tiến trình (Processes), ứng dụng (Applications), đo lường %CPU và %RAM real-time.
* **opencv-python (cv2):** Truy cập Webcam, chụp ảnh/stream luồng video từ camera.
* **mss & Pillow (PIL):** Chụp ảnh màn hình tốc độ cao (Screenshot) và mã hóa JPEG phục vụ Live Screen.
* **pynput:** Lắng nghe sự kiện bàn phím (Keylogger) phục vụ ghi nhận thao tác khi được cấp phép.

---

## 3. Kiến trúc 8 Chức năng Cốt lõi (Core Modules)

| # | Module | Thư viện chính | Mô tả chức năng & Cơ chế an toàn |
| --- | --- | --- | --- |
| **1** | **Applications** | `psutil`, `win32gui` | Liệt kê các ứng dụng có giao diện đang chạy, đo CPU%, cho phép Khởi chạy (Start) hoặc Đóng (Stop) ứng dụng. |
| **2** | **Processes** | `psutil` | Quản lý toàn bộ tiến trình hệ thống, theo dõi %CPU, %RAM chi tiết, hỗ trợ gửi lệnh kết thúc tiến trình (`kill`). |
| **3** | **Screenshot** | `mss`, `Pillow` | Chụp ảnh màn hình máy Client theo thời gian thực. **Yêu cầu người dùng bấm Accept trên Popup trước khi chụp.** |
| **4** | **Live Screen** | `mss`, `cv2` | Stream màn hình máy Client trực tiếp lên Web App dạng chuỗi ảnh JPEG nén qua WebSocket. **Yêu cầu xin quyền người dùng.** |
| **5** | **Keylogger** | `pynput` | Ghi nhận các phím bấm và ứng dụng đang được thao tác. **Bắt buộc có sự xác nhận của người dùng mới kích hoạt.** |
| **6** | **File Transfer** | `os`, `shutil` | Tải lên (Upload) / Tải về (Download) tập tin. **Chỉ được phép truy cập trong thư mục Sandbox cấu hình trước (Tránh Directory Traversal).** |
| **7** | **Webcam** | `cv2` | Mở camera thu hình ảnh. **Bắt buộc có xác nhận người dùng. Xuất hiện chấm đỏ nhấp nháy trên màn hình máy bị điều khiển khi đang quay.** |
| **8** | **Power Control** | `os.system` | Thực hiện các lệnh hệ thống: Khóa màn hình (`Lock`), Khởi động lại (`Restart`), Tắt máy (`Shutdown`), Ngủ (`Sleep`). **Yêu cầu xác nhận.** |

---

## 4. Mô hình Bảo mật & Quản lý Rủi ro (Security & Safety Design)

Dự án chú trọng khía cạnh tư duy rủi ro và an toàn thông tin bằng cách áp dụng các cơ chế bảo vệ nghiêm ngặt:

### 4.1. Cơ chế Xin quyền Chủ động (User Explicit Consent)

* Các chức năng nhạy cảm (**Screen, Keylogger, Webcam, Power, File**) không được tự ý kích hoạt ngầm.
* Khi Admin gửi yêu cầu, Client App sẽ bật **Popup PyQt6 luôn nằm trên cùng (Always on Top)** xin phép End-User.
* Nếu người dùng bấm **Reject** hoặc **hết thời gian chờ (Timeout - 15s)**, hệ thống sẽ tự động hủy lệnh và báo lỗi về Web App.

### 4.2. Cảnh báo Trực quan (Visual Indicators)

* Khi chức năng Webcam hoạt động, một cửa sổ giao diện nhỏ chứa **chấm tròn đỏ nhấp nháy** sẽ xuất hiện ở góc màn hình Client, thông báo công khai cho người dùng biết Camera đang mở.

### 4.3. Giới hạn Vùng truy cập File (Directory Sandboxing)

 * Module quản lý File giới hạn quyền truy cập trong thư mục sandbox (cấu hình trong `config.py`, mặc định `~/AgentSandbox`).
* Mọi hành vi cố tình sử dụng đường dẫn tương đối như `../` hoặc truy cập các thư mục hệ thống (`C:\Windows`, `C:\System32`) đều bị chặn ngay tại Client.

### 4.4. Truy vết & Nhật ký Hệ thống (Audit Logging)

* Mọi hành động gửi lệnh từ Admin, trạng thái chấp nhận/từ chối của End-User, và kết quả thực thi đều được ghi lại trong bảng `audit_logs` của cơ sở dữ liệu.

---

## 5. Database Schema (SQLite)

Cơ sở dữ liệu lưu trữ tại `web-app/backend/sql_app.db` gồm 3 bảng chính:

```
+-------------------+       +--------------------+       +----------------------+
|       users       |       |      machines      |       |      audit_logs      |
+-------------------+       +--------------------+       +----------------------+
| id (PK, Int)      |       | machine_id (PK,Str)|       | id (PK, Int)         |
| username (Unique) |       | hostname (String)  |       | timestamp (DateTime) |
| hashed_password   |       | ip_address (String)|       | admin_id (FK->users) |
| role (Admin)      |       | status (Online/Off)|       | machine_id (FK->mach)|
+-------------------+       | last_seen (Date)   |       | action (String)      |
                            +--------------------+       | status (Succ/Denied) |
                                                         | details (JSON Text)  |
                                                         +----------------------+

```

---

## 6. Luồng Xử lý Bất đồng bộ (Async & UI Architecture in Client)

Do PyQt6 quản lý giao diện trên **Main Thread**, trong khi WebSocket chạy bất đồng bộ với **asyncio**, ứng dụng Client sử dụng mô hình **QThread + PyQt Signals**:

```text
[Gateway WebSocket] 
       │ (JSON Command)
       ▼
[Worker Thread (QThread + asyncio)] ──(PyQt Signal)──► [Main Thread (PyQt6 GUI)]
                                                               │
                                                       (Hiển thị Popup xin quyền)
                                                               │
[Worker Thread] ◄──(Signal trả về kết quả Chấp nhận/Từ chối)───┘
       │
       ▼
[Gateway WebSocket] ──► [Web App Admin]

```

---

## 7. Cấu trúc Thư mục Dự án chuẩn (Project Directory Structure)

```text
project_root/
│
├── web-app/                     # Hệ thống Quản trị Web
│   ├── backend/                 # FastAPI Service
│   │   ├── main.py              # Entry point ứng dụng Backend
│   │   ├── init_db.py           # Script khởi tạo Database
│   │   ├── requirements.txt     # fastapi, uvicorn, sqlalchemy, pyjwt, websockets
│   │   ├── db/                  # Cấu hình SQLite & Models
│   │   │   ├── database.py
│   │   │   └── models.py        # Tables: User, Machine, AuditLog
│   │   ├── routers/             # API Endpoints (auth, machines, modules)
│   │   ├── core/                # Config, Security (JWT), Gateway Client
│   │   └── schemas/             # Pydantic Schemas validate data
│   └── frontend/                # Giao diện ReactJS + Vite
│       ├── package.json
│       └── src/
│           ├── pages/           # LoginPage, DashboardPage, MachinePage
│           ├── components/      # UI Components & 8 Chức năng Điều khiển
│           └── services/        # Axios API & WebSocket Client
│
├── gateway/                     # WebSocket Gateway Broker
│   ├── main.py                  # Server WebSocket trung chuyển (Port 8765)
│   ├── requirements.txt         # websockets
│   ├── core/                    # Connection Manager (Quản lý kết nối Client/Web)
│   └── handlers/                # Message Routing Handler
│
└── client-app/                  # Client Agent (Python PyQt6)
    ├── main.py                  # Entry point: Khởi chạy QThread & PyQt6 App
    ├── requirements.txt         # PyQt6, websockets, psutil, opencv-python, mss, pynput
    ├── config.py                # Cấu hình IP Gateway, Machine ID, Sandbox Path
    ├── core/
    │   ├── gateway_service.py   # Duy trì WebSocket & Heartbeat gửi về Gateway
    │   └── permission_service.py# Quản lý luồng xin quyền & Timeout
    ├── modules/                 # 8 Module xử lý tác vụ trên Windows
    │   ├── applications.py
    │   ├── processes.py
    │   ├── screenshot.py
    │   ├── live_screen.py
    │   ├── keylogger.py
    │   ├── file_manager.py      # Giới hạn trong thư mục Sandbox
    │   ├── webcam.py            # Chạy camera & gọi đèn chớp đỏ
    │   └── power_control.py
    └── ui/                      # Giao diện Client Agent
        ├── main_window.py       # Hiển thị trạng thái kết nối
        ├── permission_popup.py  # Popup xin quyền End-User
        └── red_indicator.py     # Cửa sổ chấm đỏ cảnh báo Webcam

```
