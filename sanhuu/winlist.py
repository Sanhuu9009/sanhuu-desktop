# -*- coding: utf-8 -*-
"""枚举桌面上的可见窗口(自上而下的层叠顺序),用于"鼠标移到哪个窗口就高亮哪个"。
返回 [(标题, QRect 逻辑坐标)]。Windows 用 Win32 API,macOS 用 Quartz。"""
import os, sys
from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QGuiApplication


def phys_to_logical(x, y, w, h):
    """Windows 物理像素 → Qt 逻辑坐标(按窗口中心所在屏幕换算)。"""
    cx, cy = x + w / 2, y + h / 2
    for s in QGuiApplication.screens():
        g, r = s.geometry(), s.devicePixelRatio()
        if g.x() <= cx < g.x() + g.width() * r and g.y() <= cy < g.y() + g.height() * r:
            return QRect(int(g.x() + (x - g.x()) / r), int(g.y() + (y - g.y()) / r), int(w / r), int(h / r))
    return QRect(x, y, w, h)


def logical_to_phys(screen, rect):
    """Qt 逻辑矩形 → 该屏幕内的物理像素矩形 (x, y, w, h),x/y 相对屏幕左上角。"""
    g, r = screen.geometry(), screen.devicePixelRatio()
    rect = rect.intersected(g)
    return (int(round((rect.x() - g.x()) * r)), int(round((rect.y() - g.y()) * r)),
            int(round(rect.width() * r)), int(round(rect.height() * r)))


def _windows():
    import ctypes
    from ctypes import wintypes
    user32, dwm = ctypes.windll.user32, ctypes.windll.dwmapi
    me, out = os.getpid(), []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == me:
            return True
        cloaked = wintypes.DWORD()
        dwm.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
        if cloaked.value or (user32.GetWindowLongW(hwnd, -20) & 0x80):
            return True
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, cls, 64)
        if cls.value in ('Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd'):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        if not buf.value:
            return True
        r = wintypes.RECT()
        if dwm.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r)) != 0:
            user32.GetWindowRect(hwnd, ctypes.byref(r))
        w, h = r.right - r.left, r.bottom - r.top
        if w >= 60 and h >= 60:
            out.append((buf.value, phys_to_logical(r.left, r.top, w, h)))
        return True

    user32.EnumWindows(cb, 0)
    return out


def _mac():
    import Quartz
    opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    me, out = os.getpid(), []
    for w in Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or []:
        if w.get('kCGWindowLayer', 0) != 0 or w.get('kCGWindowOwnerPID') == me:
            continue
        b = w.get('kCGWindowBounds') or {}
        ww, hh = int(b.get('Width', 0)), int(b.get('Height', 0))
        if ww < 60 or hh < 60:
            continue
        title = w.get('kCGWindowName') or w.get('kCGWindowOwnerName') or '窗口'
        out.append((str(title), QRect(int(b.get('X', 0)), int(b.get('Y', 0)), ww, hh)))
    return out


def list_windows():
    try:
        if sys.platform == 'win32':
            return _windows()
        if sys.platform == 'darwin':
            return _mac()
    except Exception as e:  # noqa
        print('list_windows failed:', e)
    return []


def window_at(windows, pt: QPoint):
    for title, rect in windows:
        if rect.contains(pt):
            return title, rect
    return None
