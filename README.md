# 三虎桌宠 (Sanhuu Desktop Pet)

以「三虎 Sanhuu」为主角的像素风桌面宠物。真正独立的 Windows / macOS 桌面应用（Tauri 2），安装即用，开机自启、托盘常驻、窗口置顶。另附单文件 HTML 版（浏览器免安装体验）。

支持：截图/录屏（全屏或窗口）、文件格式转换、ZIP 压缩（可设密码）/解压（含 7z/RAR）、定时提醒与电源控制、待办清单、天气查询与下雨主动提示、鼠标交互。

## 下载安装

桌面应用安装包由 GitHub Actions 自动构建，见仓库 **Releases**（推送 `v*` 标签即可发布）：

- **Windows**：`Sanhuu.Pet_1.0.0_x64-setup.exe`（NSIS 一键安装，自动创建桌面 + 开始菜单快捷方式；安装时可选开机自启）
- **macOS**：`Sanhuu.Pet_1.0.0_aarch64.dmg`（拖入 Applications；开机自启与置顶在应用内「设置」开启）

安装后：

- 托盘常驻：左键单击托盘图标显示/隐藏三虎；右键菜单可「显示 / 隐藏」「打开设置」「退出」
- 关闭窗口不会退出，三虎会藏到托盘
- 顶部状态栏可拖动移动窗口，「—」隐藏到托盘

> 尚未发布正式 Release 时，可在 Actions 页面的最新构建产物（Artifacts）中下载对应平台的安装包测试。

### 免安装体验（HTML 版）

直接用浏览器打开 `三虎桌宠.html` 即可（截图/录屏使用浏览器屏幕选择器，功能完整；电源控制改为生成系统脚本）。

## 本地开发 / 构建

```bash
cd app
npm install            # 安装 Tauri CLI
npm run tauri dev      # 开发调试（需 Rust 工具链 + 系统 WebView 依赖）
npm run tauri build    # 构建安装包
```

- 前端：`app/src/`（index.html + styles.css + main.js + overlay.html），纯原生 JS，无构建步骤
- 后端：`app/src-tauri/`（Rust：截图/录屏/窗口选择/电源/自启/托盘/保存对话框）
- CI：`.github/workflows/build.yml` 在 Windows / macOS 上自动构建并上传安装包

## 文件结构

```
app/                         Tauri 2 桌面应用工程
  src/                       前端（桌宠本体逻辑 + overlay 高亮框）
  src-tauri/                 Rust 侧（原生能力 + 图标 + 权限配置）
assets/                      完整逐帧动画图集（idle/walk/happy/rain/jump 每状态 6 帧，160×160 透明 PNG）
  anim/                       各状态帧目录 + atlas-manifest.json + previews/ 动画预览 GIF
三虎桌宠.html                 单文件 HTML 版（浏览器免安装）
index.html                   介绍页（GitHub Pages 首页）
pack/                        HTML 版一键安装脚本（旧方案，保留）
使用说明.md                   使用说明
```

## 功能

| 功能 | 说明 |
|---|---|
| 截图 / 录屏 | 全屏或窗口；桌面版窗口选择：鼠标移到目标窗口出现红色选框，截 PNG / 录 GIF |
| 格式转换 | 图片→PNG/JPEG/WebP；文本(txt/md/csv)→PDF；视频→GIF |
| 压缩 / 解压 | ZIP 压缩（可设密码）/解压；7z/RAR 解压（联网加载 7-Zip WASM） |
| 定时任务 | 定时提醒（可每天重复）；桌面版支持一键关机 / 睡眠 / 重启 |
| 待办清单 | 优先级、截止日期、筛选，像素风 UI |
| 天气 | 城市/定位查询；未来 3 小时将下雨自动提示并表演下雨动画 |
| 鼠标交互 | 跟随鼠标、点击反应、双击跑步、拖拽移动（松手跳跃） |

## 完整逐帧动画（v1.1.0）

桌宠动画参照经典像素宠物实现方式，每个状态均为**完整逐帧动画**（非单帧位移/缩放）：

| 状态 | 帧数 | 动画内容 | 触发 |
|---|---|---|---|
| idle 待机 | 6 | 深呼吸→换气→歪头眨眼→尾巴摆动→回正→呼吸起伏 | 默认 |
| walk 行走 | 6 | 迈左腿→过渡→迈右腿→过渡→迈左腿→并步 | 双击 |
| happy 开心 | 6 | 挥手→欢呼→腾空→落地→握拳雀跃→站定 | 单击 |
| rain 下雨 | 6 | 抱膝坐下→抬头望天→发抖→埋膝缩紧→叹气→等雨停 | 未来 3 小时有雨自动触发 |
| jump 跳跃 | 6 | 蹲下蓄力→腾空→最高点→下落→落地缓冲→还原 | 拖拽移动后松手 |

帧组织：`assets/anim/<state>/NN.png`（160×160 透明 RGBA）+ `atlas-manifest.json` 清单；每状态 8fps 循环播放。

## 技术说明

- 桌面版截图/录屏/窗口选择/电源控制为 Tauri + xcap 原生能力；数据保存在本机应用数据目录。
- 开源组件：JSZip、pdf-lib（本地/按需加载）、gifenc、7-Zip WASM（联网加载）；天气数据源 Open-Meteo。
- 视频仅支持转 GIF/抽帧；rar/7z 只解压不压缩。

## 版权声明

> **美术素材版权 © 三虎 Sanhuu，保留所有权利。**
> 本仓库中的美术素材（含精灵图、立绘等 `assets/`、`pack/` 图标与内嵌于 HTML/应用的角色图像）版权归 **三虎 Sanhuu** 所有，**未经许可，禁止商用、二次修改、转载传播**。
> 代码部分（HTML/CSS/JS/Rust）可按需参考使用，使用请保留本版权声明与原作者署名。
