# -*- coding: utf-8 -*-
"""定时任务:提醒 / 关机 / 睡眠 / 重启,支持每天重复。"""
import subprocess, sys
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, QTimer, Signal
from .paths import no_window_kwargs

KIND_CN = {'remind': '提醒', 'shutdown': '关机', 'sleep': '睡眠', 'restart': '重启'}


def power(kind):
    """执行电源动作。"""
    kw = no_window_kwargs()
    if sys.platform == 'win32':
        cmd = {'shutdown': ['shutdown', '/s', '/t', '0'], 'restart': ['shutdown', '/r', '/t', '0'],
               'sleep': ['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0']}[kind]
    elif sys.platform == 'darwin':
        cmd = {'shutdown': ['osascript', '-e', 'tell application "System Events" to shut down'],
               'restart': ['osascript', '-e', 'tell application "System Events" to restart'],
               'sleep': ['pmset', 'sleepnow']}[kind]
    else:
        cmd = {'shutdown': ['systemctl', 'poweroff'], 'restart': ['systemctl', 'reboot'],
               'sleep': ['systemctl', 'suspend']}[kind]
    subprocess.Popen(cmd, **kw)


def next_fire(task, now=None):
    """计算任务下一次触发时间;一次性任务已过期返回 None。"""
    now = now or datetime.now()
    if task.get('daily'):
        hh, mm = map(int, task['time'].split(':'))
        t = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        last = task.get('last')
        if t <= now and last == now.strftime('%Y-%m-%d'):
            t += timedelta(days=1)
        elif t <= now - timedelta(minutes=2):
            t += timedelta(days=1)
        return t
    try:
        t = datetime.fromisoformat(task['at'])
    except Exception:
        return None
    return None if task.get('last') else t


class Scheduler(QObject):
    fire = Signal(dict)
    changed = Signal()

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.timer = QTimer(self, interval=5000, timeout=self.check)
        self.timer.start()

    def add(self, kind, text='', daily=False, time_hm=None, at=None):
        t = dict(id=self.store.new_id(), kind=kind, text=text, daily=daily, time=time_hm,
                 at=at.isoformat(timespec='seconds') if at else None, enabled=True, last=None)
        self.store.tasks.append(t)
        self.store.save()
        self.changed.emit()
        return t

    def remove(self, tid):
        self.store.data['tasks'] = [t for t in self.store.tasks if t['id'] != tid]
        self.store.save()
        self.changed.emit()

    def check(self):
        now = datetime.now()
        dirty = False
        for t in self.store.tasks:
            if not t.get('enabled', True):
                continue
            nf = next_fire(t, now)
            if nf is None or nf > now:
                continue
            if not t.get('daily') and now - nf > timedelta(minutes=10) and t['kind'] != 'remind':
                t['last'] = 'missed'      # 电脑没开机时错过的关机/重启不再补执行
                dirty = True
                continue
            t['last'] = now.strftime('%Y-%m-%d')
            dirty = True
            self.fire.emit(dict(t))
        if dirty:
            self.store.save()
            self.changed.emit()
