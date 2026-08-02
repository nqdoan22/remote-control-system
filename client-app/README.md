# Client App

Client App là agent Windows chạy trên máy trạm. Ứng dụng có giao diện PyQt6, kết nối WebSocket tới Gateway, nhận lệnh điều khiển từ xa và thực thi các module trên máy cục bộ.

## Vai trò

- Kết nối tới Gateway bằng WebSocket.
- Gửi heartbeat định kỳ để báo trạng thái online.
- Nhận lệnh từ Gateway và điều phối tới các module thực thi.
- Hiển thị giao diện minh bạch cho người dùng cuối với trạng thái kết nối, CPU/RAM và nhật ký hoạt động.
- Xin quyền người dùng cho các chức năng nhạy cảm như live screen, webcam, keylogger và power control.
- Chạy trong system tray để tiếp tục hoạt động khi đóng cửa sổ.

## Yêu cầu hệ thống

- Windows.
- Python 3.10+.
- Quyền đủ để dùng một số thao tác hệ thống như khóa màn hình, tắt máy hoặc hook keylogger.

## Cấu trúc chính

- [main.py](main.py): điểm khởi chạy ứng dụng.
- [config.py](config.py): cấu hình agent và các biến môi trường.
- [core/](core): gateway service, permission service và command dispatcher.
- [modules/](modules): các module thực thi lệnh trên máy client.
- [ui/](ui): [main_window.py](ui/main_window.py) (giao diện chính), [permission_popup.py](ui/permission_popup.py) (popup xin quyền), [red_indicator.py](ui/red_indicator.py) (đèn báo webcam).

## Các module hỗ trợ

- Applications: liệt kê, mở và đóng ứng dụng GUI.
- Processes: liệt kê và kết thúc tiến trình.
- Screenshot: chụp ảnh màn hình và trả về base64.
- Live Screen: stream màn hình liên tục.
- Keylogger: ghi nhật ký phím bấm theo buffer.
- File Manager: duyệt, tải lên, tải xuống và xóa file trong sandbox.
- Webcam: stream camera và bật đèn báo đỏ khi đang hoạt động.
- Power Control: khóa màn hình, restart, shutdown và sleep.

## Cấu hình môi trường

Client App đọc cấu hình từ [config.py](config.py) và file `.env` trong thư mục `client-app/`.

Ví dụ:

```env
GATEWAY_WS_URL=ws://127.0.0.1:8765/client
RECONNECT_INTERVAL_SECONDS=5
HEARTBEAT_INTERVAL_SECONDS=5
CLIENT_ID=client-my-pc
CLIENT_SECRET=DEFAULT_SECRET_KEY_123
PERMISSION_TIMEOUT_SECONDS=15
SANDBOX_DIR=C:/AgentSandbox
RED_INDICATOR_ENABLED=true
SCREEN_FPS=10
WEBCAM_FPS=15
JPEG_QUALITY=60
```

Lưu ý:

- `CLIENT_SECRET` phải khớp với secret đã đăng ký ở Gateway.
- `SANDBOX_DIR` là thư mục an toàn cho thao tác file.
- `GATEWAY_WS_URL` cần khớp với endpoint WebSocket thực tế của Gateway — Gateway chỉ lắng nghe path `/client` cho Client App (xem `gateway/main.py`), không phải `/ws/client`.

## Cài đặt

Tạo và kích hoạt môi trường ảo Python trước khi cài dependencies:

```bash
cd client-app
python -m venv .venv
.\.venv\Scripts\activate
```

Nếu dùng PowerShell thì kích hoạt bằng:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Cài package

```bash
pip install -r requirements.txt
```

## Chạy ứng dụng

**Điều kiện tiên quyết:** Gateway phải đang chạy trước (xem `gateway/README.md`), vì Client App tự kết nối ra ngoài (outbound) tới `GATEWAY_WS_URL` ngay khi khởi động — không tự khởi động Gateway giúp bạn.

1. Đảm bảo `GATEWAY_WS_URL` trong `.env` (hoặc mặc định `ws://127.0.0.1:8765/client`) trỏ đúng địa chỉ Gateway đang chạy.
2. Nếu Gateway giới hạn danh sách machine (`REGISTERED_MACHINES` trong `gateway/.env`), đảm bảo `CLIENT_ID`/`CLIENT_SECRET` của Client App khớp với một entry đã đăng ký, nếu không sẽ bị Gateway từ chối `AUTHENTICATION_FAILED`.
3. Chạy ứng dụng:

```bash
cd client-app
.\.venv\Scripts\activate   # nếu dùng virtualenv
python main.py
```

Ứng dụng sẽ mở cửa sổ chính, tự kết nối tới Gateway và tiếp tục chạy trong system tray (đóng cửa sổ không thoát ứng dụng — dùng icon khay hệ thống hoặc Ctrl+C ở terminal để thoát hẳn).

> **Chạy với quyền Administrator** nếu cần test các chức năng như `power.shutdown`/`power.restart`, hoặc đóng (kill) các tiến trình chạy với quyền cao hơn — nếu không, các lệnh này có thể trả lỗi `INTERNAL_ERROR`/`AccessDenied`.

## Luồng hoạt động

1. Ứng dụng khởi động PyQt6 và đọc cấu hình từ `.env`.
2. `GatewayService` tạo kết nối WebSocket tới Gateway.
3. Client gửi `auth.client` để đăng ký máy.
4. Sau đó client gửi heartbeat định kỳ và chờ lệnh điều khiển.
5. `CommandDispatcher` gọi module tương ứng để thực thi và trả `response` hoặc `error` về Gateway.

## Dữ liệu và bảo mật

- File chỉ được thao tác trong `SANDBOX_DIR`.
- Các chức năng nhạy cảm sẽ hiển thị popup xin quyền cho người dùng.
- Webcam bật sẽ hiển thị đèn báo đỏ ở góc màn hình.
- Ứng dụng hỗ trợ tự reconnect khi mất kết nối Gateway.

## Ghi chú

- Client App này là bản Python GUI, không phải project `.NET`.
- Thư mục `RemoteControlClient/` hiện chỉ chứa `bin/` và `obj/`, không phải điểm chạy chính của ứng dụng hiện tại.
