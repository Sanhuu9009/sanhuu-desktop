# -*- coding: utf-8 -*-
"""冒烟测试：创建 App → 逐面板打开渲染 → 动画状态切换渲染 → 存 PNG 供人工检查"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from app import App

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke_out")
os.makedirs(OUT, exist_ok=True)

app = QApplication(sys.argv)
ctx = App(app)

# 逐面板打开并渲染
for name in ["tools", "capture", "convert", "zip", "timer", "todo", "weather", "settings", "about"]:
    ctx.open_panel(name)
    p = ctx.panels.get(name)
    if not p:
        print("FAIL 面板未创建:", name)
        continue
    p.show()
    app.processEvents()
    p.grab().save(os.path.join(OUT, f"panel_{name}.png"))
    print("panel", name, "OK")

# 动画状态渲染
pet = ctx.pet
for st in ["idle", "walk", "happy", "rain", "jump"]:
    pet.set_state(st)
    if st == "rain":
        pet.rain_t = 10
    if st == "jump":
        pet.jump_t = 0.9
    for _ in range(8):
        app.processEvents()
    pet.grab().save(os.path.join(OUT, f"pet_{st}.png"))
    print("pet", st, "OK")

# 气泡
pet.set_state("idle")
pet.say("测试气泡喵~")
app.processEvents()
pet.grab().save(os.path.join(OUT, "pet_bubble.png"))

print("SMOKE DONE", OUT)
