# -*- coding: utf-8 -*-
"""本地 JSON 存储:设置、待办、定时任务。"""
import json, os, threading, uuid
from .paths import data_dir, default_output_dir

DEFAULTS = {
    'city': None,              # {'name','lat','lon','admin','country'}
    'scale': 3,
    'auto_wander': True,
    'night_sleep': True,
    'weather_remind_min': 60,
    'record_fps': 'native',    # native / 60 / 30
    'output_dir': None,
    'onboarded': False,
    'pos': None,
}


class Store:
    def __init__(self):
        self.path = os.path.join(data_dir(), 'sanhuu.json')
        self._lock = threading.Lock()
        self.data = {'settings': dict(DEFAULTS), 'todos': [], 'tasks': []}
        self.load()

    def load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as fh:
                d = json.load(fh)
            self.data['settings'].update(d.get('settings', {}))
            self.data['todos'] = d.get('todos', [])
            self.data['tasks'] = d.get('tasks', [])
        except Exception:
            pass
        # 安装程序里填写的城市(首次启动时读取)
        hint = os.path.join(data_dir(), 'installer_city.txt')
        self.city_hint = None
        if os.path.exists(hint):
            try:
                with open(hint, 'r', encoding='utf-8-sig') as fh:
                    self.city_hint = fh.read().strip() or None
            except Exception:
                pass

    def save(self):
        with self._lock:
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump(self.data, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)

    def get(self, key):
        return self.data['settings'].get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self.data['settings'][key] = value
        self.save()

    def output_dir(self):
        d = self.get('output_dir') or default_output_dir()
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def new_id():
        return uuid.uuid4().hex[:10]

    @property
    def todos(self):
        return self.data['todos']

    @property
    def tasks(self):
        return self.data['tasks']
