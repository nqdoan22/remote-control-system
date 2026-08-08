<#
===============================================================================
FILE : client-app/build_exe.ps1
MỤC ĐÍCH : Đóng gói Client App (Agent) thành 1 file RemoteControlClient.exe
           để tạo bản Release chạy không cần cài Python.
CÁCH DÙNG:
    Mở PowerShell tại thư mục client-app/ rồi chạy:
        powershell -ExecutionPolicy Bypass -File build_exe.ps1

KẾT QUẢ: dist/RemoteControlClient/
           ├─ RemoteControlClient.exe   (bản chạy)
           ├─ .env.example               (mẫu cấu hình -> đổi tên thành .env)
           └─ README.txt                 (hướng dẫn chạy nhanh)
         Đồng thời nén sẵn thành dist/RemoteControlClient-win64.zip để upload Release.
===============================================================================
#>

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " BUILD REMOTE CONTROL CLIENT (Agent) -> Windows .exe" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1) Chọn Python launcher
$python = "python"
if (Get-Command py -ErrorAction SilentlyContinue) { $python = "py" }
Write-Host "[1/5] Python: $((& $python --version) 2>&1)"

# 2) Cài dependencies + PyInstaller
Write-Host "[2/5] Cai dat dependencies + PyInstaller ..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip | Out-Null
& $python -m pip install -r requirements.txt
& $python -m pip install pyinstaller

# 3) Dọn build cũ
Write-Host "[3/5] Don build cu ..." -ForegroundColor Yellow
foreach ($d in @("build", "dist")) {
    if (Test-Path $d) { Remove-Item -Recurse -Force $d }
}

# 4) Build theo spec
Write-Host "[4/5] Dang build (co the mat 1-3 phut) ..." -ForegroundColor Yellow
& $python -m PyInstaller client-app.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build that bai (exit $LASTEXITCODE)" }

# 5) Đóng gói kèm .env.example + hướng dẫn, rồi nén zip
Write-Host "[5/5] Dong goi Release ..." -ForegroundColor Yellow
$exe = "dist\RemoteControlClient.exe"
if (-not (Test-Path $exe)) { throw "Khong tim thay $exe sau khi build." }

$outDir = "dist\RemoteControlClient"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Move-Item -Force $exe $outDir

if (Test-Path ".env.example") { Copy-Item -Force ".env.example" "$outDir\.env.example" }

@"
REMOTE CONTROL CLIENT (Agent) - Huong dan chay nhanh
=====================================================
1. Doi ten file  .env.example  thanh  .env
2. Mo .env, sua GATEWAY_WS_URL tro toi Gateway dang chay
   (mac dinh: ws://127.0.0.1:8765/client) va CLIENT_ID / CLIENT_SECRET
   khop voi Gateway (REGISTERED_MACHINES).
3. Dam bao Gateway va Web App backend da chay truoc.
4. Chay RemoteControlClient.exe (chay Run as Administrator neu can
   dung power.shutdown / power.restart hoac kill process quyen cao).

Ung dung se ket noi Gateway va chay ngam o System Tray.
"@ | Out-File -Encoding utf8 "$outDir\README.txt"

$zip = "dist\RemoteControlClient-win64.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path "$outDir\*" -DestinationPath $zip

Write-Host "==================================================================" -ForegroundColor Green
Write-Host " BUILD XONG!" -ForegroundColor Green
Write-Host "   - Thu muc chay : $outDir" -ForegroundColor Green
Write-Host "   - File .exe    : $outDir\RemoteControlClient.exe" -ForegroundColor Green
Write-Host "   - Zip Release  : $zip  (upload file nay len GitHub Release)" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
