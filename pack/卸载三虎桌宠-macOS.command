#!/bin/bash
# ===== 三虎桌宠 Sanhuu Pet - macOS 卸载 =====
echo "正在卸载三虎桌宠…"
launchctl unload "$HOME/Library/LaunchAgents/com.sanhuu.pet.plist" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.sanhuu.pet" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.sanhuu.pet.plist"
rm -rf "$HOME/Applications/SanhuuPet.app"
rm -f "$HOME/Desktop/Sanhuu Pet"
echo "[OK] 已卸载三虎桌宠。"
read -r -p "按回车关闭…"
