# Gateway

Gateway là lớp trung gian WebSocket của hệ thống điều khiển máy tính từ xa. Thành phần này không xử lý business logic; nhiệm vụ chính là xác thực, định tuyến message và quản lý kết nối giữa Web App và Client App.

## Vai trò

- Nhận kết nối từ Client App tại `/client`.
- Nhận kết nối từ Web App tại `/webapp`.
- Kiểm tra xác thực ban đầu bằng message `auth.client` và `auth.webapp`.
- Định tuyến message giữa Web App và Client App theo giao thức JSON over WebSocket.
- Theo dõi heartbeat của máy client, trạng thái online/offline và timeout lệnh.
- Xử lý luồng xin quyền cho các tính năng nhạy cảm như live screen, webcam, keylogger và power control.

## Cổng và điểm kết nối

- Host mặc định: `0.0.0.0`
- Port mặc định: `8765`
- WebSocket endpoints:
  - `ws://<host>:8765/client`
  - `ws://<host>:8765/webapp`

## Giao thức

Gateway sử dụng envelope JSON chuẩn `WSMessage` với cấu trúc:

- `messageId`
- `type`
- `timestamp`
- `source`
- `destination`
- `payload`

Các message quan trọng:

- `auth.client`: client gửi `machineId`, `machineSecret`, `hostname`, `ipAddress`
- `auth.webapp`: web app gửi JWT token
- `heartbeat`: client giữ kết nối sống
- `response` / `error`: phản hồi từ client
- `permission.response`: phản hồi xin quyền từ người dùng cuối

## Các lệnh được định tuyến

Gateway chấp nhận các loại message điều khiển từ Web App sau:

- `machine.list`
- `application.list`, `application.start`, `application.stop`
- `process.list`, `process.kill`
- `screen.screenshot`, `screen.live.start`, `screen.live.stop`
- `webcam.start`, `webcam.stop`
- `keylogger.start`, `keylogger.stop`
- `file.list`, `file.upload`, `file.download`
- `power.lock`, `power.restart`, `power.shutdown`, `power.sleep`

Các message nhạy cảm sẽ đi qua bước xin quyền trước khi forward xuống client.

Một số loại message (`machine.list`, heartbeat, `permission.response`) được Gateway xử lý trực tiếp thay vì forward xuống Client App.

## Bảo vệ chống brute-force

Gateway giới hạn số lần xác thực thất bại (`core/rate_limiter.py`): quá `AUTH_MAX_ATTEMPTS` lần trong một cửa sổ thời gian sẽ tạm khóa kết nối đó trong `AUTH_LOCKOUT_SECONDS` giây.

## Cấu hình môi trường

Tạo file `.env` trong thư mục `gateway/` nếu muốn override giá trị mặc định:

```env
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8765
JWT_SECRET=your-jwt-secret
REGISTERED_MACHINES=client-app-01:secret-01,client-app-02:secret-02
HEARTBEAT_TIMEOUT=45
COMMAND_TIMEOUT=15
AUTH_MAX_ATTEMPTS=5
AUTH_LOCKOUT_SECONDS=60
PERMISSION_TIMEOUT=30
```

## Cài đặt

Tạo và kích hoạt môi trường ảo Python trước khi cài dependencies:

```bash
cd gateway
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Nếu dùng PowerShell thì kích hoạt bằng:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Chạy ứng dụng

```bash
cd gateway
python main.py
```

## File chính

- [main.py](main.py): entrypoint khởi động WebSocket server, định tuyến theo path kết nối
- [config.py](config.py): cấu hình môi trường và hằng số hệ thống
- [core/](core): `connection_manager.py`, `heartbeat_manager.py`, `permission_manager.py`, `auth_manager.py`, `machine_registry.py`, `command_tracker.py`, `rate_limiter.py`
- [handlers/](handlers): `client_handler.py`, `webapp_handler.py`, `message_handler.py`, `message_router.py` (xử lý client/webapp và định tuyến message)
- [models/message.py](models/message.py): helper tạo response/error theo schema WSMessage
- [schemas/protocol.py](schemas/protocol.py): schema giao thức WSMessage

## Ghi chú

- Gateway mặc định lắng nghe trên `8765`.
- Client và Web App đều phải gửi message auth đầu tiên ngay sau khi kết nối.
- `REGISTERED_MACHINES` là danh sách máy client được phép kết nối.
- Kết nối tới path không hợp lệ (khác `/client`, `/webapp`) sẽ bị đóng với close code `4004`.
