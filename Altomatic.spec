# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
PKG_DIR = SRC_DIR / "altomatic"

datas = [
    (str(PKG_DIR / "data"), "altomatic/data"),
    (str(PKG_DIR / "resources"), "altomatic/resources"),
]
datas += collect_data_files("altomatic")


a = Analysis(
    [str(PKG_DIR / "__main__.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Altomatic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(PKG_DIR / "resources" / "altomatic_icon.ico")],
)
