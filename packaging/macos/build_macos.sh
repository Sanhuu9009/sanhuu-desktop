#!/bin/bash
# 三虎 Sanhuu —— macOS 一键构建:生成 dist/Sanhuu-1.0.0.dmg
# 需要:Python 3.10+;建议先 brew install sevenzip(用于内置 rar 解压)
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m pip install -r requirements.txt pyinstaller dmgbuild
mkdir -p vendor
if command -v 7zz >/dev/null 2>&1; then cp -L "$(command -v 7zz)" vendor/7zz
else echo "警告:没找到 7zz(brew install sevenzip),安装包将不内置 rar 解压"; fi
python3 -m PyInstaller --noconfirm packaging/sanhuu.spec
# 本地临时签名;正式分发请换成 Developer ID 并做公证(notarize)
codesign --force --deep -s - dist/Sanhuu.app
rm -f dist/Sanhuu-1.0.0.dmg
python3 -m dmgbuild -s packaging/macos/dmg_settings.py "三虎 Sanhuu" dist/Sanhuu-1.0.0.dmg
echo "完成:dist/Sanhuu-1.0.0.dmg"
