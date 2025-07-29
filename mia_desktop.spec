# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mia_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui_assets/*', 'ui_assets'),
        ('ar_ui/*', 'ar_ui'),
        ('mia_assistant/*', 'mia_assistant'),
        ('gesture_control/*', 'gesture_control'),
        ('server/*', 'server'),
    ],
    hiddenimports=[
        'mia_hud',
        'mia_assistant.voice_activation',
        'mia_assistant.mood_detection',
        'mia_assistant.tts_response',
        'mia_assistant.hud_overlay',
        'mia_assistant.combo_controller',
        'mia_assistant.command_parser',
        'mia_assistant.voice_command',
        'mia_assistant.voice_control',
        'gesture_control.main',
        'gesture_control.utils',
        'server.api',
    ],
    excludes=['PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebEngineCore', 'PyQt5.QtWebEngine'],
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
    name='mia_desktop',
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
