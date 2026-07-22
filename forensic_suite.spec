# -*- mode: python ; coding: utf-8 -*-
"""
ForensicSuite - PyInstaller spec para Windows
Genera forensic_suite.exe y fs.exe con todas las dependencias empaquetadas.

Uso en Windows (con Python 3.9+ instalado):
    pip install pyinstaller
    pyinstaller forensic_suite.spec --clean

Salida:
    dist/forensic_suite/forensic_suite.exe
    dist/forensic_suite/fs.exe
"""

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import sys
import os

sys.setrecursionlimit(5000)

block_cipher = None

PROJECT_ROOT = os.path.abspath(SPECPATH)

# Archivos de datos que deben incluirse en el ejecutable
DATA_FILES = [
    # Configuraciones de perfiles de Scalpel
    ("forensic_suite/configs/*.conf", "forensic_suite/configs"),
    # Documentación incluida (opcional)
    ("docs", "docs"),
    # README y licencia
    ("README.md", "."),
    ("LICENSE", ".") if os.path.exists("LICENSE") else None,
]

# Filtrar entradas None
datas = [d for d in DATA_FILES if d]

# Para Windows, usar forensic_suite_windows/win_main.py como punto de entrada.
# En Linux, el punto de entrada sigue siendo forensic_suite/__main__.py
if sys.platform.startswith("win"):
    ENTRY_POINT = os.path.join(PROJECT_ROOT, "forensic_suite_windows", "win_main.py")
else:
    ENTRY_POINT = os.path.join(PROJECT_ROOT, "forensic_suite", "__main__.py")

a = Analysis(
    [ENTRY_POINT],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "forensic_suite",
        "forensic_suite.core",
        "forensic_suite.core.hasher",
        "forensic_suite.core.dispositivo",
        "forensic_suite.core.memoria",
        "forensic_suite.core.perito",
        "forensic_suite_windows",
        "forensic_suite_windows.core.plataforma",
        "forensic_suite.core.cadena_custodia",
        "forensic_suite.core.timestamp",
        "forensic_suite.core.firma_gpg",
        "forensic_suite.core.manifest",
        "forensic_suite.core.scalpel",
        "forensic_suite.shell",
        "forensic_suite.daemon.forensic_blockerd",
        "psutil",
        "cryptography",
        "requests",
        "pkg_resources",
        "volatility3",
        "volatility3.cli",
        "volatility3.framework",
    ],
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
    [],
    exclude_binaries=True,
    name="forensic_suite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="forensic_suite",
)
