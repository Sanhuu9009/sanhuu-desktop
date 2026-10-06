# -*- coding: utf-8 -*-
"""三虎桌宠 v3 · 原生 PyQt6 桌宠本体

无边框透明置顶窗口，QPainter 逐帧绘制；支持点击/双击/拖拽/鼠标跟随/打盹/雨警。
"""
import math
import random

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPixmap
from PyQt6.QtWidgets import QWidget

from animator import Animator, load_frames, SPRITE_W, SPRITE_H

DEFAULT_SIZE = 220          # 显示高度 px
GROUND_MARGIN = 8           # 底部留白
IDLE_DOZE_SEC = 75          # 无操作多久进入打盹
JUMP_SEC = 0.9
RAIN_SEC = 10.0
WALK_SPEED = 140            # px/s


class PetWindow(QWidget):
    def __init__(self, app_ctx):
        super().__init__(None)
        self.app = app_ctx              # 共享上下文（面板/设置/托盘）
        self.frames = load_frames()
        self.anim = Animator(self.frames)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.scale = DEFAULT_SIZE / SPRITE_H
        w = int(SPRITE_W * self.scale)
        h = int(SPRITE_H * self.scale)
        self.setFixedSize(w, h)
        self._apply_mask()

        # 运动状态
        self.t = 0.0
        self.bob = 0.0
        self.lean = 0.0
        self.look = 0.0
        self.doze = 0.0
        self.sleep_t = 0.0
        self.hop = 0.0
        self.jump_t = 0.0
        self.rain_t = 0.0
        self.walk_tgt_x = 0
        self.facing = 1
        self.dragging = False
        self.drag_start = None
        self.drag_moved = False
        self.last_tap = 0
        self.bubble_text = ""
        self.bubble_t = 0.0

        # 定时器
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self._tick)
        self.frame_timer.start(16)

        # 全局鼠标跟踪
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self._track_mouse)
        self.mouse_timer.start(50)

        self._place_default()
        self.show()

    # ---------- 窗口基础 ----------
    def _apply_mask(self):
        """用全部帧 alpha 合并生成窗口 mask：透明区域鼠标穿透到桌面"""
        from PyQt6.QtGui import QBitmap, QImage
        import sys
        if sys.platform != "linux":
            return  # macOS/Windows 由透明背景处理
        w, h = self.width(), self.height()
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        for st, seq in self.frames.items():
            for pm in seq:
                p.setOpacity(1.0)
                p.drawPixmap(0, 0, w, h, pm)
        p.end()
        self.setMask(QBitmap.fromImage(img))

    def _place_default(self):
        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 60
        y = screen.height() - self.height() - 10
        self.move(x, y)
        self.walk_tgt_x = self.x() + self.width() / 2

    def center_x(self):
        return self.x() + self.width() / 2

    def ground_y(self):
        return self.height() - GROUND_MARGIN

    # ---------- 动画状态 ----------
    def set_state(self, st, reset=True):
        self.anim.set_state(st, reset)
        if st == "idle":
            self.sleep_t = 0.0

    def trigger_rain_alert(self, text="要下雨啦，记得带伞哦~"):
        if self.anim.state == "rain":
            return
        self.set_state("rain")
        self.rain_t = RAIN_SEC
        self.say(text, 4.2)

    def say(self, text, sec=2.5):
        self.bubble_text = text
        self.bubble_t = sec

    # ---------- 交互 ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start = e.globalPosition().toPoint()
            self.drag_moved = False
            self.sleep_t = 0
            self.doze = 0

    def mouseMoveEvent(self, e):
        self.sleep_t = 0
        self.doze = 0
        if self.dragging and self.drag_start:
            delta = e.globalPosition().toPoint() - self.drag_start
            if delta.manhattanLength() > 6:
                self.drag_moved = True
                self.move(self.pos() + delta)
                self.drag_start = e.globalPosition().toPoint()
                if self.anim.state in ("idle", "walk"):
                    self.set_state("idle")

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton or not self.dragging:
            return
        self.dragging = False
        if self.drag_moved:
            self.set_state("jump")
            self.jump_t = JUMP_SEC
            self.drag_moved = False
            return
        now = self.app.now_ms()
        if now - self.last_tap < 320:
            self.last_tap = 0
            self._start_walk()
            return
        self.last_tap = now
        self.set_state("happy")
        self.hop = 1.0
        self.sleep_t = 0
        self.say(random.choice(["喵~", "你好呀", "是三虎！", "摸摸我"]), 2.0)
        self.app.open_panel("tools")

    def mouseDoubleClickEvent(self, e):
        self._start_walk()

    def contextMenuEvent(self, e):
        self.app.open_panel("tools")

    def _start_walk(self):
        self.set_state("walk")
        screen = self.screen().availableGeometry()
        cur = self.center_x()
        # 向鼠标所在侧走一段
        mouse_x = self.app.mouse_x()
        margin = 80
        if mouse_x > cur:
            target = cur + random.randint(60, 200)
        else:
            target = cur - random.randint(60, 200)
        self.walk_tgt_x = max(screen.x() + margin, min(screen.x() + screen.width() - margin, target))
        self.facing = 1 if self.walk_tgt_x > cur else -1
        self.say("溜达一下~", 1.5)

    # ---------- 运动学 tick ----------
    def _tick(self):
        dt = 0.016
        self.t += dt * self.anim.speed
        st = self.anim.state
        if st == "idle":
            self.bob = math.sin(self.t * 2.2) * 2.5 * (1 - self.doze * 0.6)
            self.sleep_t += dt
            if self.sleep_t > IDLE_DOZE_SEC:
                self.doze = min(1.0, (self.sleep_t - IDLE_DOZE_SEC) / 12)
                if random.random() < 0.006:
                    self.say("zZ…", 1.5)
            else:
                self.doze = max(0.0, self.doze - dt * 0.4)
        elif st == "happy":
            self.hop = max(0.0, self.hop - dt * 2.4)
            self.bob = math.sin(self.t * 6) * 1.5
        elif st == "walk":
            self._walk_step(dt)
        elif st == "jump":
            self.jump_t -= dt
            self.bob = math.sin(self.t * 7) * 1.5
            if self.jump_t <= 0:
                self.set_state("idle")
        elif st == "rain":
            self.rain_t -= dt
            self.bob = math.sin(self.t * 9) * 1.2
            if self.rain_t <= 0:
                self.set_state("idle")
        # 视线平滑
        mx = self.app.mouse_x()
        my = self.app.mouse_y()
        win_geo = self.frameGeometry()
        cx = win_geo.x() + self.width() / 2
        cy = win_geo.y() + self.ground_y()
        lean_t = max(-0.14, min(0.14, (mx - cx) / max(self.screen().geometry().width(), 1) * 0.5))
        self.lean += (lean_t - self.lean) * min(1.0, dt * 5)
        look_t = max(-0.05, min(0.08, (cy - my) / max(self.screen().geometry().height(), 1) * 0.6))
        self.look += (look_t - self.look) * min(1.0, dt * 5)
        if self.bubble_t > 0:
            self.bubble_t -= dt
            if self.bubble_t <= 0:
                self.bubble_text = ""
        self.update()

    def _walk_step(self, dt):
        spd = WALK_SPEED * self.anim.speed * dt
        dx = self.walk_tgt_x - self.center_x()
        if abs(dx) < 4:
            self.facing = 1 if self.walk_tgt_x > self.x() else -1
            self.set_state("idle")
            return
        self.facing = 1 if dx > 0 else -1
        self.move(self.x() + int(math.copysign(min(spd, abs(dx)), dx)), self.y())
        self.bob = abs(math.sin(self.t * 10)) * 3

    def _track_mouse(self):
        from PyQt6.QtGui import QCursor
        self.app.mouse_pos = QCursor.pos()

    # ---------- 绘制 ----------
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        st = self.anim.state
        img = self.anim.pixmap()
        if img is None:
            return
        scale = self.scale
        g = self.ground_y()
        jump_y = 0
        sx, sy = 1.0, 1.0
        if st == "jump":
            prog = max(0.0, 1 - self.jump_t / JUMP_SEC)
            jump_y = -math.sin(math.pi * min(1.0, prog)) * 44
            if prog > 0.88:
                s = math.sin(math.pi * (prog - 0.88) / 0.12) * 0.10
                sx, sy = 1 + s, 1 - s
        by = g + self.bob * scale * 0.5 + jump_y * scale + (self.hop * 18 if st == "happy" else 0) + self.look * scale * 7
        rot = math.sin(self.t * 6) * 0.02 if st == "happy" else 0
        p.setOpacity(1 - self.doze * 0.15)
        p.translate(self.width() / 2, by)
        p.scale(self.facing * scale * sx, scale * sy)
        p.rotate(math.degrees(rot + self.lean * 0.7))
        p.drawPixmap(int(-SPRITE_W / 2), int(-SPRITE_H * 0.9), SPRITE_W, SPRITE_H, img)
        p.resetTransform()
        p.setOpacity(1.0)
        if st == "rain":
            self._draw_rain(p)
        if self.bubble_text:
            self._draw_bubble(p)

    def _draw_rain(self, p):
        import random
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(24):
            x = random.uniform(0, w)
            y = random.uniform(0, h)
            p.fillRect(int(x), int(y), 1, 6, QColor(140, 180, 230, 160))
        p.fillRect(0, 0, w, h, QColor(10, 14, 26, 40))

    def _draw_bubble(self, p):
        from PyQt6.QtCore import QRect
        txt = self.bubble_text
        font = QFont("PingFang SC, Microsoft YaHei, sans-serif")
        font.setPixelSize(13)
        p.setFont(font)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(txt)
        bw = tw + 24
        bh = fm.height() + 14
        bx = self.width() / 2 - bw / 2
        by = 6
        p.setPen(QPen(QColor(26, 29, 38), 2))
        p.setBrush(QColor(245, 242, 236, 235))
        p.drawRoundedRect(QRect(int(bx), int(by), int(bw), int(bh)), 8, 8)
        p.setPen(QColor(26, 29, 38))
        p.drawText(QRect(int(bx), int(by), int(bw), int(bh)), Qt.AlignmentFlag.AlignCenter, txt)
