# -*- mode: python ; coding: utf-8 -*-

import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)


a = Analysis(
    ['start_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('image_tool_config.yaml', './'),
        ('.streamlit/config.toml', './.streamlit/'),
        ('image_analyzer_v3.py', './'),
    ],

    hiddenimports=[
        'streamlit',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.runtime.caching',
        'streamlit.elements',
        'yaml',
        'openai',
        'PIL',
        'PIL.Image',
        'concurrent.futures',
        'importlib.metadata',
        'pkg_resources',
        'altair',
        'pandas',
        'numpy',
        'tornado',
        'tornado.web',
        'tornado.ioloop',
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        'click',
        'protobuf',
        'google.protobuf',
        'streamlit.cli',
        'streamlit.web.bootstrap',
        'streamlit.web.server',
    ],
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
    name='主图检测',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/main_detect.ico',
)
