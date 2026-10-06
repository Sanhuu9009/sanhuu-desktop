# -*- coding: utf-8 -*-
"""截图 / 录屏 / 窗口选择（跨平台：QScreen 全屏 + 平台窗口枚举）"""
import os
import sys
import threading

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget, QApplication


# ---------- 窗口枚举（按平台） ----------
def list_windows():
    """返回 [{title, x, y, w, h}] 可见普通窗口"""
    if sys.platform == "win32":
        return _win_windows()
    if sys.platform == "darwin":
        return _mac_windows()
    return _x11_windows()


def _win_windows():
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    results = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        if user32.IsIconic(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n == 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        title = buf.value
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if rect.right - rect.left < 40 or rect.bottom - rect.top < 40:
            return True
        results.append({"title": title, "x": rect.left, "y": rect.top,
                        "w": rect.right - rect.left, "h": rect.bottom - rect.top, "hwnd": hwnd})
        return True

    user32.EnumWindows(cb, 0)
    return results


def _mac_windows():
    try:
        import Quartz
        wins = []
        for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID):
            owner = w.get("kCGWindowOwnerName", "")
            title = w.get("kCGWindowName", "") or owner
            b = w.get("kCGWindowBounds", {})
            if not title:
                continue
            wins.append({"title": f"{title} · {owner}", "x": int(b.get("X", 0)), "y": int(b.get("Y", 0)),
                         "w": int(b.get("Width", 0)), "h": int(b.get("Height", 0)), "wid": w.get("kCGWindowNumber")})
        return wins
    except Exception:
        return []


def _x11_windows():
    import subprocess, re
    try:
        out = subprocess.run(["wmctrl", "-lG"], capture_output=True, text=True).stdout
        wins = []
        for line in out.splitlines():
            parts = line.split(maxsplit=5)
            if len(parts) < 6:
                continue
            wins.append({"title": parts[5], "x": int(parts[2]), "y": int(parts[3]),
                         "w": int(parts[4]), "h": int(parts[5]) if False else int(parts[4].__str__()) if False else 0})
        # 简化：wmctrl 输出列：id desktop x y w h title
        wins = []
        for line in out.splitlines():
            parts = line.split(maxsplit=5)
            if len(parts) < 6:
                continue
            wins.append({"title": parts[5], "x": int(parts[2]), "y": int(parts[3]),
                         "w": int(parts[4]), "h": int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 0})
        return [w for w in wins if w["w"] > 0 and w["h"] > 0]
    except Exception:
        return []


# ---------- 截图 ----------
def grab_screen(rect=None):
    """rect=(x,y,w,h) 或无 = 主屏全屏；返回 QPixmap"""
    screen = QGuiApplication.primaryScreen()
    if rect:
        return screen.grabWindow(0, rect[0], rect[1], rect[2], rect[3])
    return screen.grabWindow(0)


def grab_window(win):
    if "hwnd" in win and sys.platform == "win32":
        return QGuiApplication.primaryScreen().grabWindow(int(win["hwnd"]))
    if "wid" in win and sys.platform == "darwin":
        import subprocess
        out = subprocess.run(["screencapture", "-l", str(win["wid"]), "-x", "/tmp/_sanhuu_win.png"],
                             capture_output=True).returncode
        if out == 0:
            from PyQt6.QtGui import QPixmap
            pm = QPixmap("/tmp/_sanhuu_win.png")
            os.remove("/tmp/_sanhuu_win.png")
            return pm
    # 通用：按几何区域抓屏
    return grab_screen((win["x"], win["y"], win["w"], win["h"]))


def save_pixmap(pm, path):
    pm.save(path)
    return path


# ---------- 窗口选择器（高亮框） ----------
class WindowPicker(QWidget):
    def __init__(self, on_pick):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.on_pick = on_pick
        self.wins = list_windows()
        self.hover = None
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.setMouseTracking(True)
        self.show()
        self.raise_()

    def mouseMoveEvent(self, e):
        g = e.globalPosition().toPoint()
        self.hover = None
        for w in self.wins:
            r = (w["x"], w["y"], w["w"], w["h"])
            if r[0] <= g.x() <= r[0] + r[2] and r[1] <= g.y() <= r[1] + r[3]:
                if self.hover is None or r[2] * r[3] < self.hover[2] * self.hover[3]:
                    self.hover = (w, r)
        self.update()

    def mousePressEvent(self, e):
        if self.hover:
            self.hide()
            self.on_pick(self.hover[0])
        else:
            self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.close()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setPen(QPen(QColor(20, 22, 30, 200), 4))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        if self.hover:
            w, r = self.hover
            p.setPen(QPen(QColor(230, 120, 60), 5))
            p.setBrush(QColor(230, 120, 60, 40))
            p.drawRect(r[0], r[1], r[2], r[3])
            from PyQt6.QtGui import QFont
            f = QFont("PingFang SC, Microsoft YaHei, sans-serif")
            f.setPixelSize(18)
            p.setFont(f)
            p.setPen(QColor(255, 240, 220))
            p.drawText(r[0] + 12, r[1] + 24, w["title"][:40])


# ---------- 录屏（GIF） ----------
class ScreenRecorder:
    def __init__(self, rect, out_path, seconds=6, fps=8):
        self.rect = rect
        self.out = out_path
        self.seconds = seconds
        self.fps = fps
        self.stop_flag = False

    def start(self, on_done):
        def run():
            import time
            import imageio
            frames = []
            screen = QGuiApplication.primaryScreen()
            start = time.time()
            while not self.stop_flag and time.time() - start < self.seconds:
                pm = screen.grabWindow(0, *self.rect) if self.rect else screen.grabWindow(0)
                img = pm.toImage()
                img = img.convertToFormat(img.Format.Format_RGB888)
                frames.append(_qimage_to_bytes(img))
                time.sleep(1 / self.fps)
            if frames:
                imageio.mimsave(self.out, frames, fps=self.fps)
            on_done(self.out if frames else None)
        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        self.stop_flag = True


def _qimage_to_bytes(img):
    w, h = img.width(), img.height()
    ptr = img.bits()
    ptr.setsize(img.sizeInBytes())
    import struct
    return bytes(ptr)
