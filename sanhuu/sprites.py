# -*- coding: utf-8 -*-
"""精灵表加载:按整数倍最近邻放大,保持像素硬边。"""
import json
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap
from .paths import resource


class Sprites:
    def __init__(self):
        with open(resource('assets', 'sprites', 'sprites.json'), 'r', encoding='utf-8') as fh:
            self.meta = json.load(fh)
        self.size = self.meta['size']
        self.ground = self.meta['ground']
        self.grab = self.meta['grab']
        self._sheets = {}
        self._cache = {}

    def info(self, name):
        return self.meta['anims'][name]

    def has(self, name):
        return name in self.meta['anims']

    def frames(self, name, scale):
        key = (name, scale)
        if key not in self._cache:
            a = self.meta['anims'][name]
            if name not in self._sheets:
                self._sheets[name] = QPixmap(resource('assets', 'sprites', a['file']))
            sheet, s, out = self._sheets[name], self.size, []
            for i in range(a['frames']):
                fr = sheet.copy(QRect((i % a['cols']) * s, (i // a['cols']) * s, s, s))
                out.append(fr.scaled(s * scale, s * scale, Qt.KeepAspectRatio, Qt.FastTransformation))
            self._cache[key] = out
        return self._cache[key]

    def portrait(self, px=96, anim='idle_11', frame=0):
        """头像:裁出头部并整数倍放大。"""
        a = self.meta['anims'][anim]
        if anim not in self._sheets:
            self._sheets[anim] = QPixmap(resource('assets', 'sprites', a['file']))
        s = self.size
        fr = self._sheets[anim].copy(QRect((frame % a['cols']) * s, (frame // a['cols']) * s, s, s))
        head = fr.copy(QRect(self.meta['cx'] - 22, self.ground - 54, 44, 38))
        k = max(1, px // 44)
        return head.scaled(44 * k, 38 * k, Qt.KeepAspectRatio, Qt.FastTransformation)
