"""
===============================================================================
FILE: web-app/backend/admin_entry.py
PURPOSE: Entry point cho RemoteControlAdmin.exe (bản đóng gói PyInstaller).
         Gộp toàn bộ phía Admin vào một exe duy nhất:
           - Phục vụ API FastAPI + static Frontend React (đã build) trên port 8000
           - Tự động khởi động RemoteControlGateway.exe (đặt cạnh exe này)
           - Mở trình duyệt tới http://localhost:8000 khi sẵn sàng

LƯU Ý KIẾN TRÚC:
  Gateway (gateway/) và Web Backend (web-app/backend/) dùng CHUNG tên package
  (core, config, models, schemas) nên không thể chạy chung 1 tiến trình Python.
  => Chạy Gateway như một subprocess riêng, Backend spawn và quản lý nó.
===============================================================================
"""

import atexit
import logging
import os
import subprocess
import sys
import threading
import webbrowser

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("AdminLauncher")


# ---------------------------------------------------------------------------
# Tìm đường dẫn Frontend dist (khi frozen nằm trong sys._MEIPASS)
# ---------------------------------------------------------------------------
def _frontend_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "frontend_dist")
    return os.path.abspath(os.path.join(BACKEND_DIR, "..", "frontend", "dist"))


# ---------------------------------------------------------------------------
# Tìm RemoteControlGateway.exe (đặt cạnh admin exe)
# ---------------------------------------------------------------------------
def _gateway_exe_path() -> str | None:
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.abspath(os.path.join(BACKEND_DIR, "..", "..", "dist"))
    candidate = os.path.join(exe_dir, "RemoteControlGateway.exe")
    if os.path.exists(candidate):
        return candidate
    logger.warning("Không tìm thấy RemoteControlGateway.exe tại: %s", candidate)
    return None


# ---------------------------------------------------------------------------
# Spawn Gateway server (subprocess riêng - tránh xung đột tên module)
# ---------------------------------------------------------------------------
def _spawn_gateway() -> subprocess.Popen | None:
    gw = _gateway_exe_path()
    if not gw:
        logger.warning("Bỏ qua khởi động Gateway - Admin Backend vẫn chạy nhưng máy Client sẽ không kết nối được.")
        return None

    # Chạy Gateway trong console riêng, cwd trỏ tới thư mục exe để load .env
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    try:
        proc = subprocess.Popen([gw], cwd=os.path.dirname(gw), creationflags=flags)
        logger.info("Đã khởi động Gateway Server (PID=%d).", proc.pid)
        atexit.register(lambda: _terminate_gateway(proc))
        return proc
    except Exception as e:
        logger.error("Không thể khởi động Gateway Server: %s", e)
        return None


def _terminate_gateway(proc: subprocess.Popen):
    if proc and proc.poll() is None:
        logger.info("Đang tắt Gateway Server (PID=%d)...", proc.pid)
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Build FastAPI app: import app gốc + mount static Frontend + SPA fallback
# ---------------------------------------------------------------------------
def _build_app():
    from main import app as backend_app
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    fe_dir = _frontend_dir()
    logger.info("Frontend static dir: %s", fe_dir)

    # 1. Static assets (JS/CSS/ảnh) — đăng ký trước, không nuốt /api /ws
    assets_dir = os.path.join(fe_dir, "assets")
    if os.path.isdir(assets_dir):
        backend_app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    else:
        logger.warning("Thiếu thư mục assets trong frontend dist: %s", assets_dir)

    # 2. SPA fallback: mọi path không phải API/WS trả về index.html
    @backend_app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        target = os.path.join(fe_dir, full_path)
        if full_path and os.path.isfile(target):
            return FileResponse(target)
        return FileResponse(os.path.join(fe_dir, "index.html"))

    return backend_app


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 60)
    logger.info("  REMOTE CONTROL ADMIN (RemoteControlAdmin.exe)")
    logger.info("=" * 60)

    # 1. Mở Gateway trước (Backend cần kết nối tới nó)
    gateway_proc = _spawn_gateway()

    # 2. Build FastAPI app (kèm static frontend)
    try:
        app = _build_app()
    except Exception as e:
        logger.critical("Khởi tạo FastAPI app thất bại: %s", e, exc_info=True)
        raise

    # 3. Tự mở trình duyệt sau khi server lắng nghe
    threading.Timer(3.0, lambda: webbrowser.open("http://localhost:8000")).start()

    # 4. Chạy server (chặn tới khi thoát)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

    if gateway_proc and gateway_proc.poll() is None:
        _terminate_gateway(gateway_proc)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Đã dừng Admin.")
        sys.exit(0)
