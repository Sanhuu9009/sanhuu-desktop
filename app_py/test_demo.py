# -*- coding: utf-8 -*-
"""生成 PyQt6 原生版运行效果预览 GIF（offscreen 渲染）"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage
from pet import PetWindow

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke_out", "pet_preview.gif")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

app = QApplication(sys.argv)


class Dummy:
    mouse_pos = None
    settings = {"size": 220, "speed": 1.0}
    def now_ms(self): return 0
    def mouse_x(self): return 0
    def mouse_y(self): return 0
    def open_panel(self, n): pass


ctx = Dummy()
pet = PetWindow(ctx)
pet.move(0, 0)

frames = []
seq = [("idle", 30), ("happy", 22), ("idle", 12), ("walk", 26), ("rain", 24), ("jump", 16), ("idle", 18)]

for st, n in seq:
    pet.set_state(st)
    if st == "rain":
        pet.rain_t = 10
        pet.say("要下雨啦，记得带伞~", 10)
    if st == "jump":
        pet.jump_t = 0.9
    for i in range(n):
        app.processEvents()
        img = pet.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
        ptr = img.bits()
        ptr.setsize(img.sizeInBytes())
        import numpy as np
        frames.append(np.frombuffer(bytes(ptr), dtype=np.uint8).reshape(img.height(), img.width(), 3))

import imageio
imageio.mimsave(OUT, frames, fps=14)
print("DONE", OUT, len(frames), "frames")
