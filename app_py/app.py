# -*- coding: utf-8 -*-
"""三虎桌宠 v3 · 原生 PyQt6 主程序

无 HTML / 无 WebView：QWidget + QPainter 原生渲染，PyInstaller 打包双平台。
"""
import json
import os
import sys
import time

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap

from pet import PetWindow
import panels

APP_NAME = "三虎桌宠 Sanhuu Pet"


def data_dir():
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    os.makedirs(base, exist_ok=True)
    return base


class App:
    def __init__(self, qapp):
        self.qapp = qapp
        self.base = data_dir()
        self.settings = self._load_json("settings.json", {
            "size": 220, "speed": 1.0, "name": "三虎",
            "autostart": False, "city": ""
        })
        self.mouse_pos = qapp.primaryScreen() and qapp.primaryScreen().geometry().center() or None
        self.pet = None
        self.panels = {}
        self._build_tray()
        self.pet = PetWindow(self)
        # 下雨预警
        from weather import RainWatcher
        self.rain_watcher = RainWatcher(self)
        self.rain_watcher.start()
        # 定时任务
        from tasks import TaskScheduler
        self.scheduler = TaskScheduler(self)
        self.scheduler.start()

    # ---------- 存储 ----------
    def _load_json(self, name, default):
        try:
            p = os.path.join(self.base, name)
            if os.path.exists(p):
                return json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
        return default

    def save_json(self, name, data):
        try:
            json.dump(data, open(os.path.join(self.base, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception as e:
            print("save_json fail", e)

    # ---------- 基础 ----------
    def now_ms(self):
        return int(time.time() * 1000)

    def mouse_x(self):
        return self.mouse_pos.x() if self.mouse_pos else 0

    def mouse_y(self):
        return self.mouse_pos.y() if self.mouse_pos else 0

    def save_settings(self):
        self.save_json("settings.json", self.settings)
        if self.pet:
            self.pet.anim.speed = self.settings["speed"]
            self.pet.scale = self.settings["size"] / 160
            self.pet.setFixedSize(int(160 * self.pet.scale), int(160 * self.pet.scale))

    # ---------- 托盘 ----------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(self._icon(), self.qapp)
        self.tray.setToolTip(APP_NAME)
        menu = QMenu()
        menu.addAction("打开工具栏", lambda: self.open_panel("tools"))
        menu.addAction("待办", lambda: self.open_panel("todo"))
        menu.addAction("天气", lambda: self.open_panel("weather"))
        menu.addSeparator()
        menu.addAction("退出", self.qapp.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self.open_panel("tools") if r == QSystemTrayIcon.ActivationReason.Trigger else None
        )
        self.tray.show()

    def _icon(self):
        """像素风图标：用第一帧精灵（idle 01）"""
        from animator import find_assets_dir
        import os
        pm = QPixmap(os.path.join(find_assets_dir(), "idle", "01.png"))
        if not pm.isNull():
            return QIcon(pm)
        return QIcon()

    # ---------- 面板 ----------
    def open_panel(self, name):
        if name not in self.panels or not self.panels[name].isVisible():
            cls = panels.get_panel(name)
            if cls:
                self.panels[name] = cls(self)
        p = self.panels.get(name)
        if p:
            p.show()
            p.raise_()
            p.activateWindow()


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    ctx = App(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
