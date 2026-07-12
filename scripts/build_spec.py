# build_spec.py — PyInstaller 打包配置
# 用法：pyinstaller build_spec.py
a = Analysis(
    ['local_pc_agent.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['starlette', 'uvicorn', 'mcp', 'websockets', 'anyio'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'PIL'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RemotePCAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # Windows 下不显示 cmd 窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
