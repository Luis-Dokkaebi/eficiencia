# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import sys
import os

block_cipher = None

# Hidden imports for critical dependencies
hidden_imports = [
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan.on',
    'sqlalchemy.dialects.postgresql',
    'pg8000',
    'psycopg2',
    'asyncpg',
    'shapely',
    'shapely.geometry',
    'face_recognition',
    'cv2',
    'numpy',
    'ultralytics',
    'supervision'
]

# Attempt to collect submodules if installed
try:
    hidden_imports += collect_submodules('uvicorn')
    hidden_imports += collect_submodules('fastapi')
    hidden_imports += collect_submodules('sqlalchemy')
    hidden_imports += collect_submodules('ultralytics')
except Exception as e:
    print(f"Warning: Could not collect submodules automatically: {e}")

# Data files to include
datas = [
    ('models/yolov8/yolov8n.pt', 'models/yolov8'),
    ('.env.example', '.'),
    ('src/detection', 'src/detection'),
]

a = Analysis(
    ['src/launcher.py'],
    pathex=[],
    binaries=[],
    datas=datas,
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

# Single Executable Mode
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TrackingSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
