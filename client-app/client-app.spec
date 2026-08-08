# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec cho Client App (Agent).
Đóng gói main.py thành 1 file thực thi Windows duy nhất: RemoteControlClient.exe

Build:  pyinstaller client-app.spec --noconfirm
Hoặc:   powershell -ExecutionPolicy Bypass -File build_exe.ps1
"""

from PyInstaller.utils.hooks import collect_submodules

# pynput (keylogger) và cv2 (webcam) nạp backend theo nền tảng lúc runtime,
# nên phải gom submodule để PyInstaller không bỏ sót.
hidden_imports = []
hidden_imports += collect_submodules("pynput")
hidden_imports += collect_submodules("mss")
hidden_imports += [
    "cv2",
    "PIL",
    "psutil",
    "websockets",
    "pydantic",
    "pydantic_settings",
]

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="RemoteControlClient",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # console=False => ứng dụng GUI (PyQt6), không mở cửa sổ terminal đen.
    # Đổi thành True nếu muốn xem log trực tiếp khi debug.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="app.ico",  # bỏ chú thích nếu có file icon riêng
)
