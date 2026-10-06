# -*- coding: utf-8 -*-
import os, sys, subprocess


def resource(*parts):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


def data_dir():
    if sys.platform == 'win32':
        d = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Sanhuu')
    elif sys.platform == 'darwin':
        d = os.path.expanduser('~/Library/Application Support/Sanhuu')
    else:
        d = os.path.expanduser('~/.config/Sanhuu')
    os.makedirs(d, exist_ok=True)
    return d


def default_output_dir():
    home = os.path.expanduser('~')
    for sub in ('Pictures', 'Desktop'):
        if os.path.isdir(os.path.join(home, sub)):
            return os.path.join(home, sub, 'Sanhuu')
    return os.path.join(home, 'Sanhuu')


def unique_path(path):
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{root} ({i}){ext}"):
        i += 1
    return f"{root} ({i}){ext}"


def reveal(path):
    """在系统文件管理器中定位文件。"""
    try:
        if sys.platform == 'win32':
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', path])
        else:
            subprocess.Popen(['xdg-open', path if os.path.isdir(path) else os.path.dirname(path)])
    except Exception:
        pass


def no_window_kwargs():
    """Windows 下启动子进程时不弹出黑色控制台窗口。"""
    if sys.platform == 'win32':
        return {'creationflags': 0x08000000}
    return {}
