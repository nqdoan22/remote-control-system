# Hướng dẫn Build & Release

Tài liệu này mô tả cách tạo **bản chạy (release)** cho hệ thống và cách công bố lên **GitHub Release** + **Google Drive** để người dùng/giảng viên có thể tải về chạy ngay.

---

## 1. Build Client App thành file `.exe`

Client App (Agent) là ứng dụng Python PyQt6. Có thể đóng gói thành **một file `.exe`** để chạy trên Windows mà **không cần cài Python**.

### Cách nhanh nhất (script tự động)

```powershell
cd client-app
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

Script sẽ tự động:
1. Cài `requirements.txt` + `pyinstaller`.
2. Build theo [client-app/client-app.spec](../client-app/client-app.spec).
3. Đóng gói kèm `.env.example` + `README.txt`.
4. Nén sẵn thành `dist/RemoteControlClient-win64.zip`.

Kết quả:

```
client-app/dist/
├── RemoteControlClient/
│   ├── RemoteControlClient.exe   ← bản chạy
│   ├── .env.example              ← đổi tên thành .env rồi sửa cấu hình
│   └── README.txt                ← hướng dẫn chạy nhanh
└── RemoteControlClient-win64.zip ← file upload lên GitHub Release
```

### Cách thủ công (nếu không dùng script)

```powershell
cd client-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt pyinstaller
pyinstaller client-app.spec --noconfirm
```

> **Lưu ý:** Nên build trên đúng Windows đích (x64) vì PyInstaller không cross-compile. File `.exe` một-file khi chạy lần đầu có thể bị Windows SmartScreen cảnh báo (do chưa ký số) — bấm *More info → Run anyway*.

---

## 2. Đóng gói mã nguồn (Source code)

Tạo file zip mã nguồn sạch (bỏ `node_modules`, `.venv`, `__pycache__`, `dist`, `build`, `*.db`) để đính kèm Release và upload Google Drive:

```powershell
# Chay tai thu muc goc remote-control-system
git archive --format=zip --output=remote-control-system-src.zip HEAD
```

`git archive` chỉ đóng gói các file được Git theo dõi nên tự động loại bỏ file rác/nặng.

---

## 3. Tạo GitHub Release

### Bằng giao diện web
1. Vào repo trên GitHub → tab **Releases** → **Draft a new release**.
2. **Choose a tag**: nhập `v1.0.0` → *Create new tag*.
3. **Release title**: `Remote Control System v1.0.0`.
4. Dán mô tả (tính năng chính, hướng dẫn chạy nhanh, link Google Drive).
5. Kéo thả **2 file** vào phần *Attach binaries*:
   - `RemoteControlClient-win64.zip` (bản chạy client)
   - `remote-control-system-src.zip` (mã nguồn)
6. **Publish release**.

### Bằng GitHub CLI (nhanh hơn)

```powershell
# Can cai GitHub CLI: https://cli.github.com/  va chay: gh auth login
gh release create v1.0.0 `
  client-app/dist/RemoteControlClient-win64.zip `
  remote-control-system-src.zip `
  --title "Remote Control System v1.0.0" `
  --notes-file docs/RELEASE_NOTES.md
```

---

## 4. Upload Google Drive & lấy link

1. Upload `remote-control-system-src.zip` (và/hoặc file `.exe`) lên Google Drive.
2. Chuột phải file → **Share** → **General access** → **Anyone with the link** → **Viewer**.
3. **Copy link** và dán vào [README.md](../README.md) mục *Release & Source code* + mô tả GitHub Release.

> Nhớ kiểm tra link ở chế độ ẩn danh (Incognito) để chắc chắn ai cũng mở được.

---

## 5. Checklist trước khi nộp

- [ ] `build_exe.ps1` chạy ra `RemoteControlClient.exe` và mở được.
- [ ] Đã tạo tag + GitHub Release, đính kèm bản chạy + mã nguồn.
- [ ] Đã có link Google Drive (đã test mở ẩn danh).
- [ ] [README.md](../README.md) có mục **Release & Source code** với 2 link.
- [ ] README hướng dẫn chạy đủ 3 thành phần (Gateway → Backend → Frontend → Client).
