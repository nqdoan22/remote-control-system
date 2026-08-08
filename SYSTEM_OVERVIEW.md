# SYSTEM OVERVIEW: HỆ THỐNG ĐIỀU KHIỂN VÀ GIÁM SÁT MÁY TÍNH TỪ XA QUAN MẠNG LAN

---

## 1. TỔNG QUAN VÀ MỤC TIÊU DỰ ÁN (PROJECT OVERVIEW & GOALS)

### 1.1. Bối cảnh & Mục tiêu cốt lõi
Dự án **Hệ thống điều khiển và giám sát máy tính từ xa qua mạng LAN** được thiết kế nhằm xây dựng một giải pháp quản trị tập trung (Centralized Management System)[cite: 1, 4]. Hệ thống cho phép Quản trị viên (Administrator) theo dõi và thực thi các lệnh điều khiển trên nhiều máy tính Windows Client đồng thời thông qua giao diện Web[cite: 1, 4].

Khác biệt với các ứng dụng điều khiển từ xa truyền thống (như TeamViewer, UltraViewer), hệ thống này được thiết kế theo triết lý **Bảo vệ quyền riêng tư người dùng cuối (Privacy-First / Explicit Consent)**[cite: 1, 2, 4, 5]. Mọi thao tác can thiệp sâu hoặc xâm phạm quyền riêng tư (xem màn hình, theo dõi webcam, ghi phím, tắt máy) **bắt buộc phải có sự đồng ý trực tiếp (Accept)** từ người dùng đang ngồi trước máy bị điều khiển[cite: 1, 2, 4, 5].

### 1.2. Các mục tiêu chính của Đồ án
1. **Quản trị tập trung (Centralized Management):** Giám sát hàng loạt máy tính Client trong mạng nội bộ (LAN) từ giao diện trình duyệt Web mà không cần cài đặt phần mềm điều khiển trên máy Admin[cite: 1, 4].
2. **Thời gian thực (Real-time Communication):** Đảm bảo truyền nhận dữ liệu và phản hồi lệnh với độ trễ thấp (< 500ms) thông qua công nghệ WebSocket[cite: 1, 4, 7].
3. **An toàn & Minh bạch (Security & Transparency):** Bảo vệ quyền riêng tư người dùng qua cơ chế xin quyền (Popup Always-on-Top), giới hạn vùng truy cập tệp (Directory Sandboxing) và ghi nhật ký truy vết chống chối bỏ (Audit Logging)[cite: 1, 2, 4, 5].
4. **Kiến trúc phần mềm chuẩn mực (3-Tier Architecture):** Thể hiện rõ tư duy thiết kế phần mềm linh hoạt, phân tách trách nhiệm giữa Web App, Gateway Broker và Client Agent[cite: 1, 3, 5].

### 1.3. Phạm vi Hệ thống (System Scope)
* **Môi trường vận hành:** Mạng nội bộ (Local Area Network - LAN)[cite: 1, 4, 5].
* **Hệ điều hành hỗ trợ:** 
  * Web App & Gateway Server: Chạy đa nền tảng (Windows, Linux, macOS) hỗ trợ Python[cite: 1].
  * Client App (Agent): **Bắt buộc chạy trên hệ điều hành Windows (Windows 10/11)** do khai thác các API hệ thống đặc thụ của Windows (`win32gui`, `psutil`, `pynput`)[cite: 1, 4, 5].
* **Giới hạn phạm vi (Out of Scope):** Không hỗ trợ NAT Traversal/STUN/TURN để đi qua Internet, không hỗ trợ thao tác chuột/bàn phím tương tác trực tiếp lên màn hình Client (Remote Desktop đầy đủ), và không phân quyền đa cấp độ cho Admin[cite: 1].

---

## 2. KIẾN TRÚC HỆ THỐNG VÀ LUỒNG XỬ LÝ (SYSTEM ARCHITECTURE & FLOWS)

Hệ thống được thiết kế theo mô hình **3-Tier Architecture** (3 lớp) tách biệt rõ ràng trách nhiệm[cite: 1, 3, 5].

### 2.1. Sơ đồ Kiến trúc Tổng thể (High-level Architecture)

```text
                     Administrator (Admin User)
                                 │
                                 │ HTTP / REST API (Authentication)
                                 ▼
+------------------------------------------------------------------+
|                     WEB APP (Admin Panel)                        |
|                                                                  |
|  [ ReactJS Frontend ]  ◄──────►  [ FastAPI Backend ]             |
|  - Dashboard UI                   - JWT Authentication           |
|  - Machine & Module Controls      - REST Endpoints               |
|  - Real-time Stream Viewer        - SQLite Database (models.py)  |
+------------------------------------------------------------------+
                                 │
                                 │ WebSocket (JSON RPC + JWT Auth)
                                 ▼
+------------------------------------------------------------------+
|                      GATEWAY SERVER                              |
|  [ Python Asyncio + websockets ] (Port 8765)                     |
|  - Connection Manager (Quản lý Socket kết nối)                   |
|  - Message Router (Định tuyến lệnh theo machineId)               |
|  - Heartbeat & Health Check Manager                              |
+------------------------------------------------------------------+
                                 │
                                 │ WebSocket (JSON RPC)
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
+---------------+        +---------------+        +---------------+
| Client App A  |        | Client App B  |        | Client App N  |
| (PyQt6 Agent) |        | (PyQt6 Agent) |        | (PyQt6 Agent) |
+---------------+        +---------------+        +---------------+

```

*(Chức năng chi tiết từng khối được định nghĩa tại `system_architecture.md`)*

### 2.2. Trách nhiệm của từng thành phần (Component Responsibilities)

1. **Web App (Frontend + Backend + Database):**
* **Frontend (ReactJS + Vite):** Cung cấp giao diện trực quan cho Admin xem danh sách máy, chọn chức năng, và hiển thị video/ảnh truyền về.


* **Backend (FastAPI + SQLite):** Xác thực Admin qua JWT, lưu danh sách máy, ghi Audit Log bất biến vào SQLite.


* **Không chịu trách nhiệm:** Không kết nối trực tiếp tới máy Client, không xử lý lệnh hệ thống trên máy Client.




2. **Gateway Server (WebSocket Broker):**
* Đóng vai trò làm trạm trung chuyển thông điệp (Message Broker) cực nhanh nhờ kiến trúc bất đồng bộ `asyncio`.


* Quản lý trạng thái kết nối Online/Offline qua Heartbeat.


* Định tuyến thông điệp từ Web App đến đúng máy Client đích.


* **Không chịu trách nhiệm:** Không có Database, không xử lý Business Logic, không lưu/giải mã dữ liệu stream.




3. **Client App (Python Agent):**
* Lớp ứng dụng chạy ngầm trên máy bị điều khiển, sử dụng `PyQt6` cho giao diện người dùng.


* Duy trì kết nối WebSocket tới Gateway.


* Thực thi các lệnh hệ thống (xem ứng dụng, tiến trình, chụp ảnh, quay camera, ghi phím).


* **Hiển thị Popup xin quyền bắt buộc** và chớp đỏ cảnh báo khi webcam bật.





### 2.3. Mô hình Đa luồng (Threading Model) tại Client App

Để ứng dụng Client không bị đơ/treo giao diện (UI Freeze) khi truyền nhận dữ liệu mạng nặng hoặc chờ người dùng phản hồi, kiến trúc đa luồng được áp dụng:

* **Main Thread (GUI Thread):** Chạy vòng lặp sự kiện `PyQt6`, chịu trách nhiệm hiển thị Popup xin quyền (Always-on-Top) và Đèn báo Webcam nhấp nháy.


* **Worker Thread (Network Thread - `QThread` + `asyncio`):** Duy trì socket kết nối Gateway, nhận/gửi JSON message. Khi nhận lệnh cần xin quyền, Worker Thread phát `PyQt Signal` truyền thông tin lên Main Thread để bật Popup.



### 2.4. Quy trình Xử lý Lệnh (Command Execution Flow)

Hệ thống phân tách làm 2 luồng xử lý tùy theo mức độ nhạy cảm của chức năng:

#### Luồng 1: Direct Execution Flow (Chức năng Tiêu chuẩn)

*(Áp dụng cho: Xem ứng dụng, Xem tiến trình, Kill tiến trình, Chạy ứng dụng)*

```text
Admin ──> Web App ──> Gateway ──> Client App (Thực thi ngay) ──> Gateway ──> Web App (Trả kết quả & Ghi Log)
```[cite: 3]

#### Luồng 2: User Consent Flow (Chức năng Nhạy cảm)
*(Áp dụng cho: Live Screen, Webcam, Input Audit Log, Power Control, File Transfer)*[cite: 1, 2, 3, 6]
```text
Admin ──> Web App ──> Gateway ──> Client App (Worker Thread)
                                      │
                                      ▼ (Bắn PyQt Signal)
                             [Main Thread: Popup Xin quyền (15s Timeout)]
                                      │
       ┌──────────────────────────────┼──────────────────────────────┐
       ▼                              ▼                              ▼
[User Bấm Accept]              [User Bấm Reject]             [Hết 15s Timeout]
       │                              │                              │
[Thực thi lệnh]               [Hủy thực thi]                 [Hủy thực thi]
       │                              │                              │
       └──────────────────────────────┴──────────────────────────────┘
                                      │
Admin <── Web App <── Gateway <───────┘ (Gửi phản hồi Error/Success & Ghi Audit Log)
```[cite: 2, 3]

---

## 3. THIẾT KẾ BẢO MẬT VÀ NGUYÊN TẮC AN TOÀN (SECURITY & SAFETY DESIGN)

Bảo mật là điểm nhấn ăn điểm lớn nhất của đồ án, thể hiện tư duy rủi ro nghiêm ngặt[cite: 1, 2, 5].

### 3.1. Các Nguyên tắc Bảo mật Cốt lõi
1. **Authentication trước Authorization:** Xác thực danh tính người dùng/thiết bị trước khi cấp quyền điều khiển[cite: 2].
2. **Quyền hạn tối thiểu (Least Privilege & Sandboxing):** Client App chỉ cho phép truy cập tệp trong vùng Sandbox chỉ định[cite: 2, 5, 6].
3. **Cơ chế Xin quyền rõ ràng (Explicit Consent):** Mọi hành vi xâm phạm quyền riêng tư phải qua Popup xác nhận[cite: 1, 2, 5].
4. **Truy vết toàn diện (Audit Everything):** Ghi nhận lịch sử thao tác bất biến vào Database[cite: 1, 2, 5].

### 3.2. Ranh giới Tín nhiệm (Trust Boundary)
* **High Trust Zone:** Web App (Backend) – Nơi thực hiện các thao tác quản trị chính chủ[cite: 2].
* **Medium Trust Zone (Broker):** Gateway Server – Trạm trung chuyển không lưu trữ dữ liệu[cite: 2, 3].
* **Low Trust Zone:** Client App – Nơi ứng dụng chạy trên máy người dùng, có nguy cơ bị can thiệp hoặc giả mạo[cite: 2].

### 3.3. Cơ chế Xác thực (Authentication)
* **Admin Auth:** Admin đăng nhập bằng Username/Password[cite: 2]. Mật khẩu lưu trong DB SQLite được **băm bằng thuật toán Bcrypt (Salted)**[cite: 2, 5]. Sau đăng nhập, Backend cấp **JWT (JSON Web Token)** để đính kèm vào các Request[cite: 2, 5, 6].
* **Client Auth:** Client kết nối tới Gateway qua mã định danh `CLIENT_ID` và `CLIENT_SECRET` cấu hình sẵn trong `config.py`[cite: 2, 5, 6]. Nếu sai Secret, Gateway chủ động đóng kết nối ngay lập tức[cite: 2, 7].

### 3.4. Cảnh báo Trực quan & Sandboxing
* **Cảnh báo Webcam (Red Indicator):** Khi webcam đang quay, một cửa sổ chớp đỏ nhấp nháy hiển thị cố định ở góc màn hình End User và không thể bị ẩn[cite: 1, 2, 5].
* **Cô lập Tệp (Directory Sandboxing):** Thao tác Upload/Download file chỉ được thực hiện trong thư mục `C:\AgentSandbox\`[cite: 1, 2, 5, 6]. Mọi nỗ lực truy xuất ký tự điều hướng như `../`, `..\` hoặc đường dẫn hệ thống (`C:\Windows`) đều bị chặn đứng với mã lỗi `INVALID_PATH`[cite: 2, 5, 6, 7].

### 3.5. Bảng Ma trận Rủi ro & Biện pháp Phòng chống (Threat Matrix)

| Rủi ro / Tấn công (Threat) | Biện pháp phòng chống (Mitigation) |
| :--- | :--- |
| **Giả mạo Admin ra lệnh** | Xác thực JWT cho mọi kết nối WebSocket từ Web App[cite: 2, 6, 7]. |
| **Client App giả kết nối** | Xác thực cặp `CLIENT_ID` / `CLIENT_SECRET` tĩnh tại Gateway[cite: 2, 6, 7]. |
| **Lộ mật khẩu Database** | Băm mật khẩu Admin bằng Bcrypt[cite: 2, 5]. |
| **Directory Traversal (Tấn công file)** | Giới hạn Sandbox `C:\AgentSandbox\` + Làm sạch đường dẫn đầu vào[cite: 2, 5, 6, 7]. |
| **Xâm phạm riêng tư ngầm** | Bắt buộc Popup xin quyền + Timeout 15s + Đèn đỏ nhấp nháy Webcam[cite: 1, 2, 5, 6]. |
| **Mất kết nối đột ngột** | Kiểm tra Ping/Pong Heartbeat mỗi 5s + Tự động Auto-reconnect[cite: 2, 4, 6, 7]. |

*(Chi tiết về mô hình rủi ro xem thêm tại `security_design.md`)*[cite: 2]

---

## 4. CHI TIẾT 8 CHỨC NĂNG CỐT LÕI VÀ GIAO THỨC TRUYỀN THÔNG (MODULES & PROTOCOL)

### 4.1. Bảng tổng hợp 8 Module Chức năng

| # | Module | Thư viện chính | Yêu cầu Xin quyền? | Cơ chế An toàn & Kỹ thuật triển khai |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **Applications** | `psutil`, `win32gui` | Không[cite: 6] | Liệt kê ứng dụng có giao diện (`MainWindowHandle != 0`), đo %CPU, hỗ trợ Start/Stop app[cite: 5, 6]. |
| **2** | **Processes** | `psutil` | Không[cite: 6] | Liệt kê toàn bộ tiến trình hệ thống (PID, %CPU, %RAM), hỗ trợ gửi lệnh `kill`[cite: 5, 6]. |
| **3** | **Screenshot** | `mss`, `Pillow` | Có[cite: 6] | Bật Popup xin quyền -> Chụp màn hình -> Nén JPEG base64 gửi về Web[cite: 5, 6]. |
| **4** | **Live Screen** | `mss`, `cv2` | Có[cite: 6] | Bật Popup xin quyền -> Stream chuỗi ảnh JPEG nén (base64) liên tục qua WebSocket[cite: 5, 6, 7]. |
| **5** | **Input Audit Log** | `pynput` | Có[cite: 6] | Bắt phím bấm & Tên cửa sổ ứng dụng -> Đóng gói gửi về Web mỗi 2s hoặc 50 phím[cite: 5, 6]. |
| **6** | **File Transfer** | `os`, `shutil` | Có[cite: 6] | Liệt kê, Upload, Download file. Giới hạn nghiêm ngặt trong `C:\AgentSandbox\`[cite: 2, 5, 6]. |
| **7** | **Webcam** | `cv2` | Có[cite: 6] | Mở Camera stream hình ảnh + Hiển thị khung tròn chớp đỏ nhấp nháy công khai[cite: 1, 2, 5, 6]. |
| **8** | **Power Control**| `os.system` | Có[cite: 6] | Thực hiện các lệnh hệ thống: Khóa màn hình, Restart, Shutdown, Sleep[cite: 5, 6]. |

*(Định nghĩa chi tiết các thông điệp JSON RPC xem tại `API Contract` - `API_CONTRACT.md`)*[cite: 6]

### 4.2. Đặt tính Giao thức Truyền thông (Communication Protocol)
* **Định dạng dữ liệu:** Mọi thông điệp trao đổi qua WebSocket đều là chuỗi **JSON (JSON RPC-like)**[cite: 6, 7].
* **Cấu trúc JSON chuẩn:**
```json
{
  "messageId": "550e8400-e29b-41d4-a716-446655440000",
  "type": "process.list",
  "timestamp": 1710000000,
  "source": "webapp",
  "destination": "client-app-01",
  "payload": {}
}
```[cite: 6, 7]
* **Truyền dữ liệu Nhị phân (Binary Data):** Do giao thức thống nhất dùng dạng Text JSON, các dữ liệu nhị phân (Ảnh Screenshot, Khung hình Live Stream, Nội dung File) **bắt buộc được mã hóa dưới dạng chuỗi Base64** trong trường `payload`[cite: 6, 7].

### 4.3. Mã Lỗi Chuẩn (Standard Error Codes)
Hệ thống quy định các mã lỗi chuẩn để Web App xử lý giao diện phù hợp[cite: 6, 7]:
* `USER_REJECTED`: Người dùng bấm "Reject" trên Popup[cite: 6, 7].
* `CONSENT_TIMEOUT`: Quá 15 giây người dùng không phản hồi[cite: 6, 7].
* `INVALID_PATH`: Cố tình truy cập file nằm ngoài thư mục Sandbox[cite: 6, 7].
* `AUTHENTICATION_FAILED`: Token không hợp lệ hoặc sai Secret[cite: 6, 7].
* `MACHINE_OFFLINE`: Máy Client bị ngắt kết nối hoặc rớt Heartbeat[cite: 6, 7].

---

## 5. CÔNG NGHỆ SỬ DỤNG VÀ CẤU TRÚC THƯ MỤC (TECH STACK & STRUCTURE)

### 5.1. Bảng Công nghệ Sử dụng (Tech Stack)

| Thành phần | Công nghệ / Framework | Vai trò trong hệ thống |
| :--- | :--- | :--- |
| **Frontend Web** | ReactJS + Vite | Giao diện điều khiển Admin trên trình duyệt[cite: 5] |
| **Backend REST API** | FastAPI (Python 3.10+) | API Xác thực Admin, Cấp JWT, Quản lý Audit Log[cite: 5] |
| **Gateway Server** | Python `asyncio` + `websockets` | Server WebSocket trung chuyển dữ liệu thời gian thực[cite: 5] |
| **Client Agent** | Python 3.10+ (PyQt6) | Ứng dụng chạy trên máy Client, thực thi lệnh & xin quyền[cite: 5] |
| **Database** | SQLite + SQLAlchemy ORM | Cơ sở dữ liệu lưu Users, Machines, Audit Logs[cite: 5] |

*(Xem chi tiết phiên bản thư viện tại `TECH_STACK.md`)*[cite: 5]

### 5.2. Cấu trúc Cơ sở Dữ liệu (SQLite Schema)
Cơ sở dữ liệu được khởi tạo tại `web-app/backend/sql_app.db` gồm 3 bảng chính[cite: 5]:
* **`users`**: Lưu tài khoản Admin (`id`, `username`, `hashed_password`, `role`)[cite: 5].
* **`machines`**: Lưu danh sách máy tính Client (`machine_id`, `hostname`, `ip_address`, `status`, `last_seen`)[cite: 5, 6].
* **`audit_logs`**: Nhật ký truy vết thao tác (`id`, `timestamp`, `admin_id`, `machine_id`, `action`, `status`, `details`)[cite: 5].

### 5.3. Cấu trúc Thư mục Dự án Chuẩn (Project Directory Structure)

```text
project_root/
│
├── web-app/                     # Thành phần giao diện quản trị và Backend
│   ├── backend/                 # FastAPI (Python)
│   │   ├── main.py              # Entry point của Backend
│   │   ├── init_db.py           # Script chạy 1 lần để tạo file CSDL sql_app.db
│   │   ├── requirements.txt     # fastapi, uvicorn, sqlalchemy, pyjwt, websockets
│   │   ├── db/                  # Quản lý Database (SQLite)
│   │   │   ├── database.py      # Engine & SessionLocal
│   │   │   └── models.py        # Các bảng: User, Machine, AuditLog
│   │   ├── routers/             # Các REST API Endpoints (auth, machines, modules)
│   │   ├── core/                # Cấu hình SECRET_KEY, JWT, gateway_client
│   │   └── schemas/             # Pydantic models validate dữ liệu
│   │
│   └── frontend/                # React + Vite (Giao diện Admin)
│       ├── package.json
│       └── src/
│           ├── pages/           # LoginPage, DashboardPage, MachinePage
│           ├── components/      # UI Components & 8 Module Chức năng
│           └── services/        # Axios API & WebSocket Client
│
├── gateway/                     # Trạm trung chuyển WebSocket (Broker)
│   ├── main.py                  # Khởi chạy Server WebSocket (port 8765)
│   ├── requirements.txt         # websockets
│   ├── core/
│   │   └── connection_manager.py# Quản lý danh sách kết nối (webapp, agents)
│   └── handlers/
│       └── message_handler.py   # Định tuyến tin nhắn theo JSON RPC
│
└── client-app/                  # Agent chạy trên máy bị điều khiển (Python)
    ├── main.py                  # Entry point: Khởi tạo QThread & PyQt6 GUI
    ├── requirements.txt         # PyQt6, websockets, psutil, opencv-python, mss, pynput
    ├── config.py                # Cấu hình GATEWAY_WS_URL, CLIENT_ID, CLIENT_SECRET
    ├── core/
    │   ├── gateway_service.py   # Duy trì WebSocket & Heartbeat gửi về Gateway
    │   └── permission_service.py# Quản lý trạng thái phân quyền & Timeout 15s
    ├── modules/                 # 8 Module xử lý chức năng lõi trên Windows
    │   ├── applications.py
    │   ├── processes.py
    │   ├── screenshot.py
    │   ├── live_screen.py
    │   ├── input_audit_logger.py
    │   ├── file_manager.py      # Giới hạn trong thư mục Sandbox C:\AgentSandbox\
    │   ├── webcam.py            # Chạy camera & bật đèn cảnh báo
    │   └── power_control.py
    └── ui/                      # Giao diện PyQt6 bảo vệ quyền lợi End User
        ├── main_window.py       # Hiển thị trạng thái kết nối của Agent
        ├── permission_popup.py  # Popup xin quyền bắt buộc (Accept/Reject)
        └── red_indicator.py     # Cửa sổ chấm đỏ chớp nhấp nháy khi mở Webcam
```[cite: 5]

---

## 6. DANH MỤC BÀN GIAO VÀ QUY TRÌNH ĐÁNH GIÁ (DELIVERABLES & EVALUATION)

### 6.1. Sản phẩm Bàn giao (Deliverables)
Để hoàn thành môn học Đồ án Mạng máy tính, các thành phần sau bắt buộc phải được đóng gói đầy đủ[cite: 1]:
1. **Source Code hoàn chỉnh:** Mã nguồn sạch của cả 3 thư mục `web-app`, `gateway`, và `client-app`[cite: 1].
2. **Video Demo + Thuyết minh:** Video quay lại quá trình vận hành thực tế hệ thống trong mạng LAN, giải thích rõ luồng xử lý lệnh và cơ chế xin quyền[cite: 1].
3. **Báo cáo Kỹ thuật (File Word):** Báo cáo chi tiết bằng tiếng Việt về thiết kế phần mềm, cấu trúc dữ liệu, luồng xử lý chức năng, giao diện và giải pháp công nghệ[cite: 1].
4. **Nhật ký AI (AI Chat Log):** File log ghi lại quá trình tương tác, hỏi đáp và ứng dụng AI (như Gemini) trong quá trình phát triển dự án[cite: 1].
5. **Chương trình Chạy Thực tế (Live Demo):** Hệ thống sẵn sàng vận hành trực tiếp trước mặt Giảng viên[cite: 1].

### 6.2. Quy trình Đánh giá Đồ án (Evaluation Process)
Giảng viên sẽ chấm điểm đồ án dựa trên các bước nghiêm ngặt[cite: 1]:
1. **Mở File Demo & Báo cáo:** Kiểm tra tính đầy đủ của tài liệu và video demo[cite: 1].
2. **Double Check mã nguồn:** Đánh giá tư duy thiết kế phần mềm, kiểm tra xem mã nguồn có tuân thủ kiến trúc 3 lớp và có đoạn mã độc hại hay không[cite: 1, 3].
3. **Kiểm tra Chạy thực tế (Live Execution):** Mã nguồn bắt buộc phải chạy được mượt mà trên môi trường mạng LAN thực tế[cite: 1].

---

## 7. TÀI LIỆU LIÊN QUAN (RELATED DOCUMENTS)
- `project_requirements.md` – Yêu cầu chi tiết dự án[cite: 1, 2, 3, 4, 5, 6, 7]
- `system_specification.md` – Đặc tả chức năng hệ thống[cite: 1, 2, 3, 4, 5, 6, 7]
- `system_architecture.md` – Kiến trúc hệ thống chi tiết[cite: 1, 2, 3, 4, 5, 6, 7]
- `security_design.md` – Thiết kế bảo mật & Mô hình rủi ro[cite: 1, 2, 3, 4, 5, 6, 7]
- `communication_protocol.md` – Quy chuẩn Giao thức WebSocket[cite: 1, 2, 3, 4, 5, 6, 7]
- `API_CONTRACT.md` – Chi tiết Payload và Message JSON[cite: 6]
- `TECH_STACK.md` – Danh mục công nghệ & Thư viện[cite: 1, 2, 3, 4, 5, 6, 7]

```

---

