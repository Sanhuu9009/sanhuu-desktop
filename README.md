# 三虎桌宠 · Sanhuu Desktop Pet

以「三虎 Sanhuu」为主角的像素风桌面宠物。**100% 原生 Python + PyQt6 实现——无 HTML、无 WebView**，QWidget/QPainter 直接渲染，Windows / macOS 双平台安装包由 GitHub Actions 自动构建。

## 功能

- 🐾 **完整动画**：idle / walk / happy / rain / jump 五套状态（76 帧，视频抽帧制作），乒乓往返播放消除跳变，跳跃抛物线+落地压扁
- 📸 **截图 / 录屏**：全屏或窗口（鼠标移动到目标窗口即出现待选框），录屏输出 GIF
- 🔄 **格式转换**：图片 → png/jpg/webp/ico；txt/md/csv → PDF；视频 → GIF
- 🗜 **压缩 / 解压**：zip（支持 AES 密码）、7z（支持密码）压缩；zip/7z/rar 解压
- ⏰ **定时任务**：提醒、定时关机 / 睡眠 / 重启（可每天重复）
- ✅ **待办清单**：优先级 + 截止日期 + 完成状态，像素风 UI
- 🌧 **天气雨警**：每 30 分钟检查一次；未来 3 小时有雨 → 三虎自动播放下雨动画并提醒
- 🖱 **鼠标交互**：点击卖萌、双击溜达、拖拽跳跃、视线跟随、75 秒无操作打盹（Zzz）
- 🧩 **托盘常驻 + 置顶 + 透明穿透**，设置里可一键开启开机自启

## 下载安装

安装包见仓库 **Releases**（Windows `.exe` 安装器 / macOS `.dmg`）：

- Windows：运行安装器，自动创建桌面/开始菜单快捷方式并注册开机自启
- macOS：打开 dmg 把「三虎桌宠.app」拖入 Applications；开机自启在应用「设置」里开启

## 从源码运行

```bash
pip install PyQt6 Pillow requests pyzipper py7zr imageio imageio-ffmpeg fpdf2
python app_py/app.py
```

## 打包

- Windows / macOS 安装包由 `.github/workflows/build.yml` 自动构建（PyInstaller + NSIS / hdiutil）
- 推送 `v*` 标签即触发发布

## 版权声明

**美术素材版权 © 三虎 Sanhuu，保留所有权利。未经许可，禁止商用、二次修改、转载传播。**

代码部分可按需参考，请保留版权声明与原作者署名。

## 技术说明

| 层 | 技术 |
|---|---|
| UI | Python + PyQt6（QWidget/QPainter/QSS），无任何 HTML/JS/WebView |
| 动画 | 帧序列 + 状态机（乒乓往返 / 一次性 / 缓动） |
| 截图录屏 | QScreen.grabWindow + 平台窗口枚举（Win32 / Quartz / X11） |
| 压缩 | pyzipper（AES）/ py7zr / zipfile |
| 天气 | Open-Meteo 免费 API + IP 定位 |
| 打包 | PyInstaller + NSIS（Win）/ hdiutil（macOS） |
