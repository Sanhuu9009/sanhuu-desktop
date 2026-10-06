# -*- coding: utf-8 -*-
"""开机自启:Windows 写注册表 Run 项;macOS 写 LaunchAgent。"""
import os, plistlib, sys

KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
PLIST = os.path.expanduser('~/Library/LaunchAgents/com.sanhuu.pet.plist')


def _cmd():
    if getattr(sys, 'frozen', False):
        return [sys.executable]
    return [sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'run.py')]


def is_enabled():
    try:
        if sys.platform == 'win32':
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY) as k:
                winreg.QueryValueEx(k, 'Sanhuu')
            return True
        if sys.platform == 'darwin':
            return os.path.exists(PLIST)
    except Exception:
        pass
    return False


def set_enabled(on):
    try:
        if sys.platform == 'win32':
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_SET_VALUE) as k:
                if on:
                    winreg.SetValueEx(k, 'Sanhuu', 0, winreg.REG_SZ, ' '.join(f'"{c}"' for c in _cmd()))
                else:
                    try:
                        winreg.DeleteValue(k, 'Sanhuu')
                    except FileNotFoundError:
                        pass
        elif sys.platform == 'darwin':
            if on:
                os.makedirs(os.path.dirname(PLIST), exist_ok=True)
                with open(PLIST, 'wb') as fh:
                    plistlib.dump({'Label': 'com.sanhuu.pet', 'ProgramArguments': _cmd(), 'RunAtLoad': True}, fh)
            elif os.path.exists(PLIST):
                os.remove(PLIST)
        return True
    except Exception:
        return False
