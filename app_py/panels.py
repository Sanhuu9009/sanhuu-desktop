# -*- coding: utf-8 -*-
"""三虎桌宠 v3 · 像素风功能面板（QSS 原生，无 HTML）"""
import os
import sys
import threading
import time

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QListWidget, QListWidgetItem, QDateTimeEdit, QFileDialog, QMessageBox,
    QGroupBox, QSlider, QScrollArea, QFrame
)

QSS = """
QDialog, QWidget { background:#14161c; color:#e8e6df; font-family:"PingFang SC","Microsoft YaHei",sans-serif; font-size:13px; }
QLabel { color:#e8e6df; }
QLabel[dim="1"] { color:#9aa0ab; }
QLabel[title="1"] { color:#e8a33d; font-size:16px; font-weight:bold; letter-spacing:2px; }
QPushButton { background:#1c2028; color:#e8e6df; border:2px solid #2c313d; border-radius:0; padding:8px 14px; }
QPushButton:hover { background:#262b36; border-color:#e8a33d; }
QPushButton:pressed { background:#e8a33d; color:#14161c; }
QPushButton[accent="1"] { background:#e8a33d; color:#14161c; border-color:#e8a33d; font-weight:bold; }
QPushButton[danger="1"] { background:#5a2f2a; border-color:#8a4a3d; }
QLineEdit, QComboBox, QSpinBox, QDateTimeEdit { background:#1c2028; color:#e8e6df; border:2px solid #2c313d; padding:6px 8px; selection-background-color:#e8a33d; }
QLineEdit:focus, QComboBox:focus { border-color:#e8a33d; }
QComboBox QAbstractItemView { background:#1c2028; color:#e8e6df; selection-background-color:#3a4252; }
QListWidget { background:#1c2028; border:2px solid #2c313d; }
QListWidget::item { padding:6px; border-bottom:1px solid #232832; }
QListWidget::item:selected { background:#3a4252; color:#f0c25f; }
QCheckBox { color:#e8e6df; spacing:8px; }
QCheckBox::indicator { width:14px; height:14px; border:2px solid #2c313d; background:#1c2028; }
QCheckBox::indicator:checked { background:#e8a33d; border-color:#e8a33d; }
QSlider::groove:horizontal { height:6px; background:#1c2028; border:1px solid #2c313d; }
QSlider::handle:horizontal { width:16px; margin:-6px 0; background:#e8a33d; border:2px solid #2c313d; }
QScrollArea { border:none; }
QFrame[card="1"] { background:#1c2028; border:2px solid #2c313d; }
"""


def _label(text, dim=False, title=False):
    l = QLabel(text)
    l.setProperty("dim", "1" if dim else "")
    l.setProperty("title", "1" if title else "")
    return l


def _btn(text, accent=False, danger=False, on=None):
    b = QPushButton(text)
    if accent:
        b.setProperty("accent", "1")
    if danger:
        b.setProperty("danger", "1")
    if on:
        b.clicked.connect(on)
    return b


class BasePanel(QDialog):
    """面板基类：像素风 QSS + 固定大小"""
    TITLE = "面板"

    def __init__(self, app):
        super().__init__(None)
        self.app = app
        self.setWindowTitle(self.TITLE)
        self.setStyleSheet(QSS)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedWidth(360)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(14, 14, 14, 14)
        self.root.setSpacing(10)
        head = QHBoxLayout()
        head.addWidget(_label(self.TITLE, title=True))
        head.addStretch()
        head.addWidget(_btn("✕", on=self.close))
        self.root.addLayout(head)


class ToolsPanel(BasePanel):
    TITLE = "三虎 · 工具栏"

    def __init__(self, app):
        super().__init__(app)
        grid = QGridLayout()
        grid.setSpacing(8)
        items = [
            ("capture", "截图/录屏", "capture"), ("files", "格式转换", "convert"),
            ("zip", "压缩/解压", "zip"), ("timer", "定时任务", "timer"),
            ("todo", "待办", "todo"), ("weather", "天气", "weather"),
            ("settings", "设置", "settings"), ("about", "关于", "about"),
        ]
        for i, (key, label, panel) in enumerate(items):
            b = _btn(label, accent=(key == "todo"))
            b.setMinimumHeight(54)
            b.clicked.connect(lambda _=False, p=panel: self._open(p))
            grid.addWidget(b, i // 2, i % 2)
        self.root.addLayout(grid)
        self.root.addWidget(_label("点击桌宠也能打开本面板", dim=True))

    def _open(self, name):
        self.app.open_panel(name)


class CapturePanel(BasePanel):
    TITLE = "截图 / 录屏"

    def __init__(self, app):
        super().__init__(app)
        from screenshot import grab_screen, save_pixmap, WindowPicker
        self.grab_screen = grab_screen
        self.save_pixmap = save_pixmap
        self.WindowPicker = WindowPicker
        shots = QGroupBox("截图")
        sv = QVBoxLayout(shots)
        sv.addWidget(_btn("全屏截图 (PNG)", accent=True, on=self.shot_full))
        sv.addWidget(_btn("窗口截图（鼠标移动到窗口即选中）", on=self.shot_window))
        self.root.addWidget(shots)
        rec = QGroupBox("录屏 (GIF)")
        rv = QVBoxLayout(rec)
        rrow = QHBoxLayout()
        rrow.addWidget(_label("范围：", dim=True))
        self.rec_mode = QComboBox()
        self.rec_mode.addItems(["全屏", "窗口"])
        rrow.addWidget(self.rec_mode)
        rrow.addWidget(_label("时长(秒)：", dim=True))
        self.rec_sec = QSpinBox()
        self.rec_sec.setRange(3, 30)
        self.rec_sec.setValue(6)
        rrow.addWidget(self.rec_sec)
        rv.addLayout(rrow)
        self.rec_btn = _btn("开始录制", accent=True, on=self.rec_start)
        rv.addWidget(self.rec_btn)
        rv.addWidget(_label("窗口录制：录制开始后鼠标移动到目标窗口即可", dim=True))
        self.root.addWidget(rec)
        self.recorder = None

    def shot_full(self):
        out = os.path.join(os.path.expanduser("~"), "Desktop", f"三虎截图_{int(time.time())}.png")
        if not os.path.isdir(os.path.dirname(out)):
            out = os.path.join(os.path.expanduser("~"), f"三虎截图_{int(time.time())}.png")
        self.save_pixmap(self.grab_screen(), out)
        self._done(f"已保存：{out}")

    def shot_window(self):
        def pick(win):
            pm = self.grab_screen((win["x"], win["y"], win["w"], win["h"]))
            out = os.path.join(os.path.expanduser("~"), "Desktop", f"三虎窗口_{int(time.time())}.png")
            if not os.path.isdir(os.path.dirname(out)):
                out = os.path.join(os.path.expanduser("~"), f"三虎窗口_{int(time.time())}.png")
            self.save_pixmap(pm, out)
            self._done(f"已保存：{out}")
        self.WindowPicker(pick)

    def rec_start(self):
        from screenshot import ScreenRecorder
        if self.recorder:
            self.recorder.stop()
            self.rec_btn.setText("开始录制")
            self.recorder = None
            return
        rect = None
        if self.rec_mode.currentText() == "窗口":
            def pick(win):
                rect2 = (win["x"], win["y"], win["w"], win["h"])
                self._rec(rect2)
            self.WindowPicker(pick)
            return
        self._rec(None)

    def _rec(self, rect):
        out = os.path.join(os.path.expanduser("~"), "Desktop", f"三虎录屏_{int(time.time())}.gif")
        if not os.path.isdir(os.path.dirname(out)):
            out = os.path.join(os.path.expanduser("~"), f"三虎录屏_{int(time.time())}.gif")
        from screenshot import ScreenRecorder
        self.recorder = ScreenRecorder(rect, out, self.rec_sec.value())
        self.rec_btn.setText("停止录制")
        self.recorder.start(lambda p: (self._done(f"已保存：{p}") if p else self._done("录制失败")) and None)

    def _done(self, text):
        self.recorder = None
        self.rec_btn.setText("开始录制")
        QMessageBox.information(self, "完成", text)


class ConvertPanel(BasePanel):
    TITLE = "格式转换"

    def __init__(self, app):
        super().__init__(app)
        from fileops import IMG_FORMATS
        self.IMG_FORMATS = IMG_FORMATS
        row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择要转换的文件…")
        row.addWidget(self.file_edit)
        row.addWidget(_btn("浏览", on=self.pick))
        self.root.addLayout(row)
        frow = QHBoxLayout()
        frow.addWidget(_label("目标格式：", dim=True))
        self.fmt = QComboBox()
        self.fmt.addItems(["图片 → png/jpg/webp/ico", "txt/md/csv → pdf", "视频 → gif"])
        frow.addWidget(self.fmt)
        self.root.addLayout(frow)
        self.root.addWidget(_btn("开始转换", accent=True, on=self.convert))
        self.root.addWidget(_label("视频转 GIF 需系统安装 ffmpeg；图片支持 png/jpg/webp/bmp/gif/ico", dim=True))

    def pick(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if p:
            self.file_edit.setText(p)

    def convert(self):
        src = self.file_edit.text().strip()
        if not src or not os.path.exists(src):
            QMessageBox.warning(self, "提示", "请先选择文件")
            return
        kind = self.fmt.currentIndex()
        try:
            if kind == 0:
                ext = os.path.splitext(src)[1].lower().lstrip(".")
                if ext not in ("png", "jpg", "jpeg", "webp", "bmp", "gif", "ico"):
                    raise RuntimeError("该文件不是图片")
                out = self._conv_img(src)
            elif kind == 1:
                out = self._conv_pdf(src)
            else:
                out = self._conv_gif(src)
            QMessageBox.information(self, "完成", f"转换完成：\n{out}")
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))

    def _conv_img(self, src):
        from fileops import convert_image
        target = self.IMG_FORMATS  # 保持源格式按后缀
        ext = os.path.splitext(src)[1].lower().lstrip(".")
        return convert_image(src, ext if ext != "jpeg" else "jpg")

    def _conv_pdf(self, src):
        from fileops import convert_text_pdf
        return convert_text_pdf(src)

    def _conv_gif(self, src):
        from fileops import convert_video_gif
        out = convert_video_gif(src)
        if not out:
            raise RuntimeError("视频转 GIF 失败，请确认 ffmpeg 已安装")
        return out


class ZipPanel(BasePanel):
    TITLE = "压缩 / 解压"

    def __init__(self, app):
        super().__init__(app)
        comp = QGroupBox("压缩")
        cv = QVBoxLayout(comp)
        r1 = QHBoxLayout()
        self.arc_edit = QLineEdit()
        self.arc_edit.setPlaceholderText("文件或文件夹…")
        r1.addWidget(self.arc_edit)
        r1.addWidget(_btn("浏览", on=self.pick_src))
        cv.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(_label("格式：", dim=True))
        self.zip_fmt = QComboBox()
        self.zip_fmt.addItems(["zip", "7z"])
        r2.addWidget(self.zip_fmt)
        r2.addWidget(_label("密码：", dim=True))
        self.zip_pwd = QLineEdit()
        self.zip_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        r2.addWidget(self.zip_pwd)
        cv.addLayout(r2)
        cv.addWidget(_btn("开始压缩", accent=True, on=self.compress))
        cv.addWidget(_label("zip 支持 AES 密码；rar/7z 压缩不支持（7z 可设密码）", dim=True))
        self.root.addWidget(comp)
        ex = QGroupBox("解压")
        ev = QVBoxLayout(ex)
        r3 = QHBoxLayout()
        self.ex_edit = QLineEdit()
        self.ex_edit.setPlaceholderText("选择压缩包…")
        r3.addWidget(self.ex_edit)
        r3.addWidget(_btn("浏览", on=self.pick_arc))
        ev.addLayout(r3)
        r4 = QHBoxLayout()
        r4.addWidget(_label("密码：", dim=True))
        self.ex_pwd = QLineEdit()
        self.ex_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        r4.addWidget(self.ex_pwd)
        r4.addStretch()
        ev.addLayout(r4)
        ev.addWidget(_btn("解压到所选目录", accent=True, on=self.extract))
        ev.addWidget(_label("rar 解压需系统安装 7-Zip 或 unrar", dim=True))
        self.root.addWidget(ex)

    def pick_src(self):
        p = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if p:
            self.arc_edit.setText(p)
            return
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件")
        if files:
            self.arc_edit.setText(";".join(files))

    def pick_arc(self):
        p, _ = QFileDialog.getOpenFileName(self, "选择压缩包", "", "压缩包 (*.zip *.7z *.rar)")
        if p:
            self.ex_edit.setText(p)

    def compress(self):
        from fileops import make_zip, make_7z
        src = self.arc_edit.text().strip()
        if not src:
            QMessageBox.warning(self, "提示", "请选择文件或文件夹")
            return
        paths = src.split(";") if ";" in src else [src]
        out, _ = QFileDialog.getSaveFileName(self, "保存压缩包", os.path.basename(src) + "." + self.zip_fmt.currentText(),
                                             "压缩包 (*.zip *.7z)")
        if not out:
            return
        pwd = self.zip_pwd.text() or None
        try:
            if self.zip_fmt.currentText() == "zip":
                make_zip(paths, out, pwd)
            else:
                make_7z(paths, out, pwd)
            QMessageBox.information(self, "完成", f"已压缩：{out}")
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))

    def extract(self):
        from fileops import extract_archive
        arc = self.ex_edit.text().strip()
        if not arc:
            QMessageBox.warning(self, "提示", "请选择压缩包")
            return
        out_dir = QFileDialog.getExistingDirectory(self, "解压到")
        if not out_dir:
            return
        try:
            extract_archive(arc, out_dir, self.ex_pwd.text() or None)
            QMessageBox.information(self, "完成", f"已解压到：{out_dir}")
        except Exception as e:
            QMessageBox.warning(self, "失败", str(e))


class TimerPanel(BasePanel):
    TITLE = "定时任务"

    def __init__(self, app):
        super().__init__(app)
        row = QHBoxLayout()
        row.addWidget(_label("类型：", dim=True))
        self.kind = QComboBox()
        self.kind.addItems(["提醒", "关机", "睡眠", "重启"])
        row.addWidget(self.kind)
        self.root.addLayout(row)
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("提醒内容（提醒类型）")
        self.root.addWidget(self.text_edit)
        drow = QHBoxLayout()
        drow.addWidget(_label("时间：", dim=True))
        self.dt = QDateTimeEdit()
        self.dt.setCalendarPopup(True)
        self.dt.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        drow.addWidget(self.dt)
        self.root.addLayout(drow)
        self.repeat = QCheckBox("每天重复")
        self.root.addWidget(self.repeat)
        self.root.addWidget(_btn("添加任务", accent=True, on=self.add))
        self.list = QListWidget()
        self.root.addWidget(self.list)
        self.root.addWidget(_btn("删除选中", danger=True, on=self.del_one))
        self.refresh()

    def refresh(self):
        self.list.clear()
        for t in self.app.scheduler.tasks:
            text = t.get("text") or {"remind": "提醒", "power": t.get("action", "")}[t.get("type")]
            when = time.strftime("%m-%d %H:%M", time.localtime(t.get("at_ts", 0)))
            rep = " ·每天" if t.get("repeat_daily") else ""
            self.list.addItem(QListWidgetItem(f"[{when}]{rep} {text}"))

    def add(self):
        kind = self.kind.currentText()
        at_ts = self.dt.dateTime().toSecsSinceEpoch()
        task = {"id": int(time.time() * 1000), "type": "remind" if kind == "提醒" else "power",
                "action": {"提醒": "", "关机": "shutdown", "睡眠": "sleep", "重启": "restart"}[kind],
                "at_ts": at_ts, "repeat_daily": self.repeat.isChecked(),
                "text": self.text_edit.text().strip() or "时间到！"}
        self.app.scheduler.add(task)
        self.refresh()

    def del_one(self):
        idx = self.list.currentRow()
        if idx >= 0:
            self.app.scheduler.remove(self.app.scheduler.tasks[idx]["id"])
            self.refresh()


class TodoPanel(BasePanel):
    TITLE = "待办"

    def __init__(self, app):
        super().__init__(app)
        self.todos = app._load_json("todo.json", [])
        row = QHBoxLayout()
        self.todo_edit = QLineEdit()
        self.todo_edit.setPlaceholderText("添加待办…")
        row.addWidget(self.todo_edit)
        self.prio = QComboBox()
        self.prio.addItems(["高", "中", "低"])
        row.addWidget(self.prio)
        self.root.addLayout(row)
        drow = QHBoxLayout()
        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("截止日期（可选，如 10-31）")
        drow.addWidget(self.date_edit)
        drow.addWidget(_btn("添加", accent=True, on=self.add))
        self.root.addLayout(drow)
        self.list = QListWidget()
        self.list.itemChanged.connect(self.toggle)
        self.root.addWidget(self.list)
        brow = QHBoxLayout()
        brow.addWidget(_btn("删除选中", danger=True, on=self.del_one))
        brow.addWidget(_btn("清空已完成", on=self.clear_done))
        self.root.addLayout(brow)
        self.refresh()

    def refresh(self):
        self.list.blockSignals(True)
        self.list.clear()
        for t in self.todos:
            it = QListWidgetItem()
            it.setText(f"[{t.get('prio','中')}] {t['text']}" + (f" ·{t.get('date','')}" if t.get("date") else ""))
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked if t.get("done") else Qt.CheckState.Unchecked)
            if t.get("done"):
                it.setForeground(Qt.GlobalColor.gray)
            it.setData(Qt.ItemDataRole.UserRole, id(t))
            self.list.addItem(it)
        self.list.blockSignals(False)

    def toggle(self, item):
        idx = self.list.row(item)
        if 0 <= idx < len(self.todos):
            self.todos[idx]["done"] = item.checkState() == Qt.CheckState.Checked
            item.setForeground(Qt.GlobalColor.gray if self.todos[idx]["done"] else Qt.GlobalColor.white)
            self.save()

    def save(self):
        self.app.save_json("todo.json", self.todos)

    def add(self):
        text = self.todo_edit.text().strip()
        if not text:
            return
        self.todos.append({"text": text, "prio": self.prio.currentText(),
                           "date": self.date_edit.text().strip(), "done": False})
        self.todo_edit.clear()
        self.save()
        self.refresh()

    def del_one(self):
        idx = self.list.currentRow()
        if 0 <= idx < len(self.todos):
            del self.todos[idx]
            self.save()
            self.refresh()

    def clear_done(self):
        self.todos = [t for t in self.todos if not t.get("done")]
        self.save()
        self.refresh()


class WeatherPanel(BasePanel):
    TITLE = "天气"

    def __init__(self, app):
        super().__init__(app)
        self.out = QLabel("点击查询当前天气")
        self.out.setWordWrap(True)
        self.out.setMinimumHeight(80)
        self.root.addWidget(self.out)
        self.root.addWidget(_btn("查询天气（自动定位）", accent=True, on=self.query))
        self.root.addWidget(_btn("模拟下雨预警（测试动画）", on=self.test_rain))
        self.root.addWidget(_label("未来 3 小时有雨时，三虎会自动播放下雨动画提醒（每 30 分钟检查一次）", dim=True))

    def query(self):
        self.out.setText("查询中…")
        def run():
            from weather import get_weather, locate_ip
            lat, lon, city = locate_ip()
            if lat is None:
                self.out.setText("定位失败，请检查网络")
                return
            w = get_weather(lat, lon)
            rain = "⚠ 未来 3 小时有雨！" if w["rain_soon"] else "未来 3 小时无雨"
            self.out.setText(
                f"📍 {city or '当前位置'}\n🌡 {w['temp']}°C · {w['desc']}\n💧 湿度 {w['humidity']}% · 风速 {w['wind']} km/h\n{rain}")
        threading.Thread(target=run, daemon=True).start()

    def test_rain(self):
        self.app.pet.trigger_rain_alert("测试：要下雨啦！")


class SettingsPanel(BasePanel):
    TITLE = "设置"

    def __init__(self, app):
        super().__init__(app)
        s = app.settings
        r1 = QHBoxLayout()
        r1.addWidget(_label("大小：", dim=True))
        self.size = QSlider(Qt.Orientation.Horizontal)
        self.size.setRange(140, 320)
        self.size.setValue(int(s.get("size", 220)))
        r1.addWidget(self.size)
        self.root.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(_label("速度：", dim=True))
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(50, 200)
        self.speed.setValue(int(s.get("speed", 1.0) * 100))
        r2.addWidget(self.speed)
        self.root.addLayout(r2)
        r3 = QHBoxLayout()
        r3.addWidget(_label("名字：", dim=True))
        self.name = QLineEdit(s.get("name", "三虎"))
        r3.addWidget(self.name)
        self.root.addLayout(r3)
        self.auto = QCheckBox("开机自动启动")
        self.auto.setChecked(bool(s.get("autostart", False)))
        self.root.addWidget(self.auto)
        self.root.addWidget(_btn("保存设置", accent=True, on=self.save))

    def save(self):
        s = self.app.settings
        s["size"] = self.size.value()
        s["speed"] = self.speed.value() / 100
        s["name"] = self.name.text().strip() or "三虎"
        old = s.get("autostart", False)
        s["autostart"] = self.auto.isChecked()
        self.app.save_settings()
        if s["autostart"] != old:
            _set_autostart(s["autostart"])
        QMessageBox.information(self, "完成", "设置已保存")


class AboutPanel(BasePanel):
    TITLE = "关于"

    def __init__(self, app):
        super().__init__(app)
        text = ("三虎桌宠 Sanhuu Pet v3.0\n"
                "纯原生 PyQt6 实现（无 HTML / 无 WebView）\n\n"
                "功能：截图 / 录屏 / 格式转换 / 压缩解压\n"
                "定时任务 / 待办 / 天气雨警 / 鼠标交互\n\n"
                "美术素材版权 © 三虎 Sanhuu，保留所有权利。\n"
                "未经许可，禁止商用、二次修改、转载传播。\n"
                "代码部分可按需参考，请保留版权声明与原作者署名。")
        l = _label(text)
        l.setWordWrap(True)
        self.root.addWidget(l)


def _set_autostart(enable):
    """开机自启：Windows 注册表 Run；macOS LaunchAgent"""
    exe = os.path.abspath(sys.argv[0] if getattr(sys, "frozen", False) else "三虎桌宠")
    if sys.platform == "win32":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, "SanhuuPet", 0, winreg.REG_SZ, f'"{exe}"')
        else:
            try:
                winreg.DeleteValue(key, "SanhuuPet")
            except OSError:
                pass
        winreg.CloseKey(key)
    elif sys.platform == "darwin":
        plist_dir = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(plist_dir, exist_ok=True)
        plist = os.path.join(plist_dir, "com.sanhuu.pet.plist")
        if enable:
            with open(plist, "w") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.sanhuu.pet</string>
<key>ProgramArguments</key><array><string>{exe}</string></array>
<key>RunAtLoad</key><true/>
</dict></plist>""")
        elif os.path.exists(plist):
            os.remove(plist)


def get_panel(name):
    return {
        "tools": ToolsPanel, "capture": CapturePanel, "convert": ConvertPanel,
        "zip": ZipPanel, "timer": TimerPanel, "todo": TodoPanel,
        "weather": WeatherPanel, "settings": SettingsPanel, "about": AboutPanel,
    }.get(name)
