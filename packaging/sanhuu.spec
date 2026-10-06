# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置(Windows / macOS 通用):pyinstaller --noconfirm packaging/sanhuu.spec
import os, sys
from PyInstaller.utils.hooks import collect_data_files

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
datas = [(os.path.join(ROOT, 'assets', 'sprites'), 'assets/sprites'),
         (os.path.join(ROOT, 'assets', 'icon.png'), 'assets'),
         (os.path.join(ROOT, 'COPYRIGHT.txt'), '.')]
datas += collect_data_files('imageio_ffmpeg')      # 内置 FFmpeg
datas += collect_data_files('docx')                # python-docx 默认模板
binaries = []
vendor = os.path.join(ROOT, 'vendor')              # 构建脚本放进来的 7-Zip
if os.path.isdir(vendor):
    binaries += [(os.path.join(vendor, f), 'vendor') for f in os.listdir(vendor) if not f.startswith('.')]

# 明确排除一切网页 / QML 相关模块:本应用只用 Qt Widgets
excludes = ['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick', 'PySide6.QtWebChannel',
            'PySide6.QtWebSockets', 'PySide6.QtWebView', 'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
            'tkinter', 'matplotlib', 'IPython', 'numpy']

a = Analysis([os.path.join(ROOT, 'run.py')], pathex=[ROOT], binaries=binaries, datas=datas,
             hiddenimports=['py7zr', 'pyzipper', 'pypdf', 'pypdfium2', 'docx'], excludes=excludes, noarchive=False)
pyz = PYZ(a.pure)
icon = os.path.join(ROOT, 'assets', 'icon.icns' if sys.platform == 'darwin' else 'icon.ico')
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Sanhuu', console=False, icon=icon, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name='Sanhuu', upx=False)

if sys.platform == 'darwin':
    app = BUNDLE(coll, name='Sanhuu.app', icon=icon, bundle_identifier='com.sanhuu.pet', info_plist={
        'CFBundleName': 'Sanhuu', 'CFBundleDisplayName': '三虎 Sanhuu', 'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0', 'LSUIElement': True, 'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSHumanReadableCopyright': '美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。',
        'NSAppleEventsUsageDescription': '三虎需要此权限来执行你设置的定时关机 / 重启。',
        'NSCameraUsageDescription': '三虎不会使用摄像头;录屏组件在枚举屏幕设备时系统会要求此说明。',
        'NSMicrophoneUsageDescription': '三虎不会录制麦克风声音。',
    })
