# -*- coding: utf-8 -*-
"""定时任务：提醒 / 关机 / 睡眠 / 重启（跨平台电源控制）"""
import subprocess
import sys
import threading
import time


def power_action(action, delay_sec=10):
    """执行系统电源动作；Windows 用 shutdown，macOS 用 osascript"""
    if sys.platform == "win32":
        if action == "shutdown":
            subprocess.Popen(["shutdown", "/s", "/t", str(delay_sec)])
        elif action == "restart":
            subprocess.Popen(["shutdown", "/r", "/t", str(delay_sec)])
        elif action == "sleep":
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    elif sys.platform == "darwin":
        verbs = {"shutdown": "shut down", "restart": "restart", "sleep": "sleep"}
        if action in verbs:
            subprocess.Popen(["osascript", "-e",
                              f'tell application "System Events" to {verbs[action]}'])
    else:
        import os
        if action == "shutdown":
            os.system("systemctl poweroff &" if os.path.exists("/run/systemd/system") else "shutdown -h now &")
        elif action == "restart":
            os.system("systemctl reboot &" if os.path.exists("/run/systemd/system") else "shutdown -r now &")


class TaskScheduler:
    """持久化定时任务：{id,type(remind/power),action,at_ts,repeat_daily,text}"""

    def __init__(self, app):
        self.app = app
        self.tasks = app._load_json("tasks.json", [])
        self.last_check = 0

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def save(self):
        self.app.save_json("tasks.json", self.tasks)

    def add(self, task):
        self.tasks.append(task)
        self.save()

    def remove(self, task_id):
        self.tasks = [t for t in self.tasks if t.get("id") != task_id]
        self.save()

    def _loop(self):
        while True:
            now = time.time()
            for t in list(self.tasks):
                if now >= t.get("at_ts", 0):
                    self._fire(t)
                    if t.get("repeat_daily"):
                        t["at_ts"] += 86400
                        self.save()
                    else:
                        self.remove(t["id"])
            time.sleep(10)

    def _fire(self, t):
        try:
            if t["type"] == "remind":
                self.app.pet.say(f"⏰ {t.get('text','提醒时间到！')}", 6)
            elif t["type"] == "power":
                power_action(t["action"])
        except Exception as e:
            print("task fire fail", e)
