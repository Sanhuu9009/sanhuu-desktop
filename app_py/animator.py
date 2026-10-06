# -*- coding: utf-8 -*-
"""三虎桌宠 v3 · 原生 PyQt6 动画引擎

动画资产：../assets/anim/<state>/NN.png（160×160 透明 RGBA，视频抽帧制作）
播放策略（参照开源桌宠 clawd-on-desk）：
- idle/walk/happy/rain 乒乓往返播放，消除循环跳变
- jump 一次性播完停留
"""
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap

FRAME_MS = {"idle": 125, "walk": 125, "happy": 125, "rain": 125, "jump": 100}
PING_PONG = {"idle", "walk", "happy", "rain"}
SPRITE_W = 160
SPRITE_H = 160


def find_assets_dir():
    """自动定位 assets/anim：兼容源码运行与 PyInstaller 打包"""
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        cands = [os.path.join(base, "assets", "anim"), os.path.join(base, "anim")]
    else:
        cands = [os.path.join(here, "..", "assets", "anim"), os.path.join(here, "assets", "anim"), "assets/anim"]
    for c in cands:
        if os.path.isdir(c):
            return c
    return cands[0]


def load_frames(base_dir=None):
    """加载全部状态帧为 QPixmap 列表"""
    import os
    if base_dir is None:
        base_dir = find_assets_dir()
    frames = {}
    for st in ["idle", "walk", "happy", "rain", "jump"]:
        d = os.path.join(base_dir, st)
        if not os.path.isdir(d):
            continue
        files = sorted(
            f for f in os.listdir(d)
            if f.lower().endswith((".png", ".apng"))
        )
        frames[st] = [QPixmap(os.path.join(d, f)) for f in files]
    return frames


class Animator:
    """帧序列播放器：负责状态、帧号、往返方向、一次性播放"""

    def __init__(self, frames):
        self.frames = frames          # {state: [QPixmap,...]}
        self.state = "idle"
        self.frame = 0
        self.dir = 1                  # 往返方向 1/-1
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self._acc = 0.0
        self.speed = 1.0              # 动画速度倍率
        self.tick_ms = 16
        self.timer.start(self.tick_ms)

    def _tick(self):
        self._acc += self.tick_ms
        ms = FRAME_MS.get(self.state, 125) / self.speed
        if self._acc < ms:
            return
        self._acc -= ms
        seq = self.frames.get(self.state)
        if not seq:
            return
        n = len(seq)
        if self.state in PING_PONG:
            self.frame += self.dir
            if self.frame >= n - 1:
                self.frame = n - 1
                self.dir = -1
            elif self.frame <= 0:
                self.frame = 0
                self.dir = 1
        elif self.state == "jump":
            if self.frame < n - 1:
                self.frame += 1
        else:
            self.frame = (self.frame + 1) % n

    def set_state(self, state, reset=True):
        if state not in self.frames:
            return
        self.state = state
        if reset:
            self.frame = 0
            self.dir = 1
            self._acc = 0

    def pixmap(self):
        seq = self.frames.get(self.state)
        if not seq:
            return None
        return seq[min(self.frame, len(seq) - 1)]

    def n_frames(self):
        return len(self.frames.get(self.state, []))
