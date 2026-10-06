#!/bin/bash
# ===== 三虎桌宠 Sanhuu Pet - macOS 一键安装 =====
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"
APP="$HOME/Applications/SanhuuPet.app"
AGENT="$HOME/Library/LaunchAgents/com.sanhuu.pet.plist"

echo "=================================================="
echo "   三虎桌宠  Sanhuu Pet  -  macOS 一键安装"
echo "   美术素材版权 (c) 三虎 Sanhuu，保留所有权利"
echo "=================================================="
echo ""

# 定位桌宠 HTML（排除介绍页 index.html）
HTML=""
for f in "$ROOT"/*.html; do
  n="$(basename "$f")"
  if [ "$n" != "index.html" ]; then HTML="$f"; fi
done
if [ -z "$HTML" ]; then
  echo "[错误] 未找到 三虎桌宠.html，请确认安装包文件完整。"
  read -r -p "按回车关闭…"
  exit 1
fi

echo "  安装目录 : $APP"
echo "  将创建   : 桌面快捷方式、程序（Launchpad 可用）、开机自动启动"
echo ""

# ---------- 组装 .app ----------
if [ -d "$APP" ]; then rm -rf "$APP"; fi
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/assets"
cp "$HTML" "$APP/Contents/Resources/三虎桌宠.html"
cp "$ROOT"/assets/*.png "$APP/Contents/Resources/assets/" 2>/dev/null
ICON="$(dirname "$0")/三虎桌宠图标.icns"
[ -f "$ICON" ] && cp "$ICON" "$APP/Contents/Resources/app.icns"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Sanhuu Pet</string>
  <key>CFBundleDisplayName</key><string>三虎桌宠</string>
  <key>CFBundleIdentifier</key><string>com.sanhuu.pet</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleExecutable</key><string>start</string>
  <key>CFBundleIconFile</key><string>app.icns</string>
  <key>LSMinimumSystemVersion</key><string>10.13</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>LSUIElement</key><false/>
</dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/start" <<'SH'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/.." && pwd)"
URL="file://$DIR/Resources/三虎桌宠.html"
if [ -d "/Applications/Google Chrome.app" ]; then
  open -a "Google Chrome" --args "--app=$URL" --window-size=480,700
elif [ -d "/Applications/Microsoft Edge.app" ]; then
  open -a "Microsoft Edge" --args "--app=$URL" --window-size=480,700
else
  open "$DIR/Resources/三虎桌宠.html"
fi
SH
chmod +x "$APP/Contents/MacOS/start"

# ---------- 桌面快捷方式 ----------
ln -sf "$APP" "$HOME/Desktop/Sanhuu Pet" 2>/dev/null || true
echo "  [OK] 文件已安装，桌面快捷方式已创建"

# ---------- 开机自动启动 ----------
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$AGENT" <<AG
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.sanhuu.pet</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$APP/Contents/MacOS/start</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><false/>
</dict>
</plist>
AG
launchctl unload "$AGENT" 2>/dev/null || true
launchctl load -w "$AGENT" 2>/dev/null || launchctl bootstrap "gui/$(id -u)" "$AGENT" 2>/dev/null || true
echo "  [OK] 已设置开机自动启动"

# ---------- 立即启动 ----------
open "$APP"
echo ""
echo "  =================================================="
echo "   安装完成！"
echo "   应用位置 : ~/Applications/SanhuuPet.app（Launchpad 可见）"
echo "   桌面快捷 : Sanhuu Pet"
echo "   卸载     : 双击 pack/卸载三虎桌宠-macOS.command"
echo "  =================================================="
