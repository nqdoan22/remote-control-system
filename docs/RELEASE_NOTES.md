# Remote Control System v1.0.0

Hệ thống điều khiển máy tính từ xa gồm 3 thành phần: **Gateway** (WebSocket), **Web App** (FastAPI + React) và **Client App** (Agent PyQt6 trên Windows).

## Tính năng chính

- Đăng nhập admin (JWT), dashboard danh sách máy, audit logs.
- 8 module điều khiển: Applications, Processes, Screenshot, Live Screen, Keylogger, File Transfer, Webcam, Power Control.
- Popup xin quyền phía Client cho các tính năng nhạy cảm (live screen, webcam, keylogger, power).
- Heartbeat theo dõi online/offline, tự reconnect, chống brute-force ở Gateway.

## Nội dung bản phát hành

| File | Mô tả |
|------|-------|
| `RemoteControlClient-win64.zip` | Bản chạy Client App (Windows x64), không cần cài Python. |
| `remote-control-system-src.zip` | Toàn bộ mã nguồn. |

## Chạy nhanh Client (bản đóng gói)

1. Giải nén `RemoteControlClient-win64.zip`.
2. Đổi tên `.env.example` → `.env`, sửa `GATEWAY_WS_URL`, `CLIENT_ID`, `CLIENT_SECRET`.
3. Đảm bảo Gateway + Web App backend đang chạy.
4. Chạy `RemoteControlClient.exe` (Run as Administrator nếu cần power control).

## Chạy từ mã nguồn

Xem [README.md](../README.md) và [docs/RELEASE_GUIDE.md](RELEASE_GUIDE.md).

## Source code (Google Drive)

> Dán link Google Drive tại đây: `https://drive.google.com/...`
