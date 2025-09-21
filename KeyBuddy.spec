# -*- mode: python ; coding: utf-8 -*-

# Optimerad version - bara nödvändiga PySide6 moduler
datas = [('assets', 'assets'), ('data', 'data'), ('src', 'src'), ('version.json', '.')]
binaries = []
hiddenimports = [
    # Bara nödvändiga PySide6 moduler
    'PySide6.QtCore',
    'PySide6.QtWidgets', 
    'PySide6.QtGui',
    'PySide6.QtPrintSupport',
    # Standard library
    'sqlite3',
    # Dina moduler
    'src.ui.main_window',
    'src.core.database',
    'src.core.app_manager', 
    'src.core.version_manager',
    'src.core.license_manager',
    'src.ui.copyable_message_box',
    'src.ui.login_window',
    'src.ui.styles'
]


block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='KeyBuddy',
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
    icon=['assets\\Kaybuddy_ikon.ico'],
)
