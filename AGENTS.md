# AGENTS.md —— 给接手本项目的 AI Agent / 开发者

## 0. 不可违反的硬约束(用户已多次锁定)

1. 角色名是 **三虎 / Sanhuu**。任何文案、界面、文件名、注释、变量名都只能用这个名字,**不得改用任何其他称呼**(包括按毛色起的叫法)。
2. **纯原生桌面应用。禁止 HTML / JS / CSS 网页技术与任何 WebView**(QtWebEngine、Electron、Tauri、pywebview、QML WebView 一律不行)。
   - 界面只用 Qt Widgets 与 QPainter 自绘。样式用 QSS(Qt 原生样式表)。
   - 不要调用 `setHtml`、不要在 QLabel 里写富文本标签;所有 QLabel 经 `widgets.label()` 创建,已强制 `Qt.PlainText`。
   - 依赖用 `PySide6-Essentials`(不含 WebEngine);`packaging/sanhuu.spec` 的 `excludes` 不要删。
3. 版权声明原文必须出现在 README、关于页、首次启动介绍页、安装程序,且**一字不改**:
   > 美术素材版权 © 三虎 Sanhuu,保留所有权利。未经许可,禁止商用、二次修改、转载传播。 代码部分可按需参考使用,请保留版权声明与原作者署名。

   代码里唯一来源是 `sanhuu/__init__.py: COPYRIGHT`。
4. 动画必须是**逐帧**的:新增动作要在骨架里按姿势重画每一帧,不允许对整张图做平移/旋转/缩放来冒充动画。
5. 画风:16 位像素、硬边色块、整数倍最近邻放大。不要抗锯齿,不要非整数缩放。
6. 必备状态:idle / walk / happy / rain / jump(现有 25 组,只增不减)。

## 1. 运行与测试

```bash
pip install -r requirements.txt
python run.py                                   # 运行
QT_QPA_PLATFORM=offscreen python tests/smoke_test.py   # 无头冒烟测试,应输出 ALL OK
python tools/gen_sprites.py                     # 重新生成精灵表(需 numpy + Pillow)
python tools/gen_art.py                         # 重新生成图标与安装程序插图
```

测试里等待后台线程请用真正的事件循环(`QEventLoop` + `QTimer`),不要用 `QTest.qWait`——它不释放 GIL,线程池任务不会执行。

## 2. 架构

| 模块 | 职责 |
| --- | --- |
| `sanhuu/app.py` | 装配:菜单、托盘、截图/录屏/文件处理流程、天气与定时回调 |
| `sanhuu/pet.py` | 桌宠窗口与状态机。循环态 `idle/sleep/walk/drag/work`,一次性动作走 `act(name, on_done)` |
| `sanhuu/sprites.py` | 读 `assets/sprites/sprites.json`,切帧并按整数倍放大、缓存 |
| `sanhuu/bubble.py` | 自绘对话气泡;`pet.say(text, ms, on_click)` |
| `sanhuu/weather.py` | Open-Meteo 拉取、`parse()`、`kind_of()`、`upcoming_change()`(未来 3 小时变天判断) |
| `sanhuu/scheduler.py` | 定时任务;`next_fire()` 计算下次触发;`power()` 执行关机/睡眠/重启 |
| `sanhuu/capture.py` | `Picker`(窗口高亮 / 框选层)、`Recorder`(FFmpeg 录屏) |
| `sanhuu/winlist.py` | 窗口枚举:Windows 用 ctypes + DWM,macOS 用 Quartz;含物理/逻辑坐标换算 |
| `sanhuu/convert.py` | 格式转换;`targets_for(paths)` 决定可选目标格式 |
| `sanhuu/archive.py` | 压缩/解压;`NeedPassword`、`ToolMissing` 两个异常驱动界面流程 |
| `sanhuu/panel.py` `dialogs.py` `widgets.py` `theme.py` | 主面板六个页面、对话框、通用控件、配色与 QSS |
| `sanhuu/jobs.py` | `run_async(fn, on_done, on_fail)`;失败回调收到的是异常对象 |
| `sanhuu/store.py` | 设置 / 待办 / 任务的 JSON 持久化(`%APPDATA%\Sanhuu`、`~/Library/Application Support/Sanhuu`) |

## 3. 美术管线

- `tools/rig.py`:96×96 画布,脚底基线 `G=86`,中心 `CX=48`。`draw_front(P)` 正面、`draw_side(P)` 侧面(朝左)。
  姿势字典 `P` 的字段见 `default_pose()`(手的位置、腿型 `stand/sit/dangle`、眼睛 `half/wide/closed/sleep/happy/squeeze`、嘴型、耳朵、尾巴、伞、墨镜、围巾……)。
- 每个部件画在独立 `Layer` 上,`comp()` 合成时自动描边:外轮廓深色,压在已有色块上的内轮廓用柔和灰。
- `tools/gen_sprites.py`:每个 `a_xxx()` 返回帧列表;在 `build()` 里登记 `(名字, 函数, fps, 是否循环)`。
  天气动画固定 80 帧 × 8 fps = 10 秒;粒子的周期都取 80 帧的约数,保证循环无缝。
- 新增动作步骤:写 `a_new()` → 在 `build()` 登记 → `python tools/gen_sprites.py` → 运行时 `pet.act('new')`。
- 调色板集中在 `rig.py` 的 `C`;界面配色集中在 `theme.py`,二者同源(白毛 / 深灰虎纹 / 橙眼 / 金铃铛 / 粉肉垫)。
- 待机有 9 张表 `idle_{gx+1}{gy+1}`,`pet._poll()` 按光标方位切换实现视线跟随,切换时保留帧序号。

## 4. 打包

- `packaging/sanhuu.spec`:PyInstaller onedir;macOS 额外生成 `Sanhuu.app`(`LSUIElement`,不占 Dock)。
- Windows:`packaging/windows/installer.iss`(Inno Setup 6,文件须保持 **UTF-8 带 BOM**)。城市页把输入写到 `%APPDATA%\Sanhuu\installer_city.txt`,应用首次启动时 `Store.city_hint` 读取并自动搜索。
- macOS:`packaging/macos/dmg_settings.py`(dmgbuild)。正式分发需把 `codesign -s -` 换成 Developer ID 并公证。
- `vendor/` 由构建脚本放入 7-Zip 可执行文件,运行时 `archive.find_7z()` 优先使用。

## 5. 当前状态(如实)

- 已在 Linux 无头环境验证:全部界面可渲染、状态机、天气解析与提醒、定时、zip/7z 加解密、图片/文档/视频转换、PyInstaller 打包后可启动。
- **尚未在真实 Windows / macOS 上运行过**。首次上机请重点验证:`winlist.py` 的窗口矩形与高亮是否对齐(多屏、缩放比例不同的屏)、`capture.Recorder` 的 FFmpeg 采集参数(Windows `ddagrab` → 失败自动回退 `gdigrab`;macOS `avfoundation` 设备号解析)、透明窗口的点击穿透、`installer.iss` 编译、DMG 布局。
- 未实现:创建 rar 的内置支持(格式专有,只能调用外部 WinRAR)、窗口被移动时的跟随录制、录制系统声音。
