# -*- coding: utf-8 -*-
"""桌宠本体:透明置顶窗口 + 逐帧动画状态机 + 鼠标交互。"""
import random, time
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QCursor, QColor, QGuiApplication
from PySide6.QtWidgets import QWidget, QApplication
from .bubble import Bubble

LOOP_STATES = ('idle', 'sleep', 'walk', 'drag', 'work')
PURR = ["呼噜呼噜~", "再摸摸头!", "嘿嘿,好舒服", "尾巴不许碰哦", "喵…不对,嗷呜~"]


class Pet(QWidget):
    clicked = Signal(QPoint)
    filesDropped = Signal(list)

    def __init__(self, sprites, store):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setWindowTitle('三虎 Sanhuu')
        self.sp, self.store = sprites, store
        self.scale = int(store.get('scale') or 3)
        self.state, self.anim, self.fi = 'idle', 'idle_11', 0
        self.frames = []
        self.busy = 0
        self.recording = False
        self._on_done = None
        self._press = None
        self._dragging = False
        self._swallow = False
        self._grab = QPoint()
        self._speed = 0.0
        self._last_mv = (time.time(), QPoint())
        self._fast_until = 0
        self._pet_acc = 0.0
        self._pet_cool = 0
        self._last_cursor = QCursor.pos()
        self._last_touch = time.time()
        self._next_auto = time.time() + random.uniform(25, 60)
        self._walk_dir, self._walk_target = 1, 0
        self.bubble = Bubble()
        self.timer = QTimer(self, timeout=self._tick)
        self.poll = QTimer(self, interval=40, timeout=self._poll)
        self.walk_timer = QTimer(self, interval=40, timeout=self._walk_step)
        self.click_timer = QTimer(self, singleShot=True, timeout=self._single_click)
        self._apply_scale()
        self._set_anim('idle_11')
        self.poll.start()

    # ---------- 动画 ----------
    def _apply_scale(self):
        self.resize(self.sp.size * self.scale, self.sp.size * self.scale)

    def _set_anim(self, name):
        self.anim = name
        self.frames = self.sp.frames(name, self.scale)
        self.fi = 0
        self.timer.start(int(1000 / self.sp.info(name)['fps']))
        self.update()

    def _tick(self):
        self.fi += 1
        if self.fi >= len(self.frames):
            if self.state in LOOP_STATES:
                self.fi = 0
            else:
                cb, self._on_done = self._on_done, None
                self._rest()
                if cb:
                    cb()
        self.update()

    def _rest(self):
        if self.busy > 0:
            self.state = 'work'
            self._set_anim('work')
        else:
            self.state = 'idle'
            self._set_anim('idle_11')

    def act(self, name, on_done=None):
        """播放一次性动画(开心、跳跃、各类天气……)。拖拽中不打断。"""
        if self.state == 'drag' or not self.sp.has(name):
            return False
        self.walk_timer.stop()
        self.state = 'act'
        self._on_done = on_done
        self._set_anim(name)
        self._last_touch = time.time()
        return True

    def set_busy(self, on):
        self.busy = max(0, self.busy + (1 if on else -1))
        if self.state in ('idle', 'sleep', 'work', 'walk'):
            self.walk_timer.stop()
            self._rest()

    def paintEvent(self, _):
        p = QPainter(self)
        if self.frames:
            p.drawPixmap(0, 0, self.frames[min(self.fi, len(self.frames) - 1)])
        if self.recording and int(time.time() * 2) % 2 == 0:
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(230, 40, 40))
            r = 4 * self.scale
            p.drawEllipse(self.width() - r * 4, r * 5, r * 2, r * 2)

    # ---------- 位置 ----------
    def head_point(self):
        return self.pos() + QPoint(self.sp.meta['cx'] * self.scale, (self.sp.ground - 32) * self.scale)

    def bubble_anchor(self):
        return self.pos() + QPoint(self.sp.meta['cx'] * self.scale, (self.sp.ground - 58) * self.scale)

    def say(self, text, ms=4500, on_click=None):
        self.bubble.popup(text, self.bubble_anchor(), ms, on_click)

    def moveEvent(self, e):
        if self.bubble.isVisible():
            self.bubble.place(self.bubble_anchor())

    def place_default(self):
        pos = self.store.get('pos')
        scr = QGuiApplication.primaryScreen().availableGeometry()
        if pos and QGuiApplication.screenAt(QPoint(pos[0] + 40, pos[1] + 40)):
            self.move(pos[0], pos[1])
        else:
            self.move(scr.right() - self.width() - 60, scr.bottom() - self.height() + (self.sp.size - self.sp.ground - 2) * self.scale)

    def _clamp(self):
        scr = (QGuiApplication.screenAt(self.head_point()) or QGuiApplication.primaryScreen()).availableGeometry()
        pad = 30 * self.scale
        x = max(scr.left() - pad, min(self.x(), scr.right() - self.width() + pad))
        y = max(scr.top() - 20 * self.scale, min(self.y(), scr.bottom() - self.sp.ground * self.scale))
        self.move(x, y)
        self.store.set('pos', [x, y])

    def set_scale(self, sc):
        sc = max(2, min(5, int(sc)))
        if sc == self.scale:
            return
        foot = self.pos() + QPoint(self.width() // 2, self.sp.ground * self.scale)
        self.scale = sc
        self.store.set('scale', sc)
        self._apply_scale()
        self.frames = self.sp.frames(self.anim, sc)
        self.move(foot.x() - self.width() // 2, foot.y() - self.sp.ground * sc)
        self.update()

    # ---------- 鼠标 ----------
    def _touch(self):
        self._last_touch = time.time()
        if self.state == 'sleep':
            self._rest()

    def mousePressEvent(self, e):
        self._touch()
        if e.button() == Qt.LeftButton:
            self._press = e.globalPosition().toPoint()
            self._dragging = False
        elif e.button() == Qt.RightButton:
            self.clicked.emit(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        if self._press is None or not (e.buttons() & Qt.LeftButton):
            return
        gp = e.globalPosition().toPoint()
        if not self._dragging and (gp - self._press).manhattanLength() > 6:
            self._dragging = True
            self.click_timer.stop()
            self.walk_timer.stop()
            self._on_done = None
            self.state = 'drag'
            self._set_anim('drag')
            self._grab = QPoint(self.sp.grab[0] * self.scale, self.sp.grab[1] * self.scale)
            self._last_mv = (time.time(), gp)
            self.bubble.hide()
        if self._dragging:
            self.move(gp - self._grab)
            now = time.time()
            t0, p0 = self._last_mv
            if now - t0 > 0.03:
                v = (gp - p0).manhattanLength() / (now - t0)
                self._speed = self._speed * 0.6 + v * 0.4
                self._last_mv = (now, gp)
                if self._speed > 1100 and self.anim != 'drag_fast':
                    self._set_anim('drag_fast')
                    self._fast_until = now + 0.7
                elif self.anim == 'drag_fast' and now > self._fast_until and self._speed < 450:
                    self._set_anim('drag')

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self._swallow:
            self._swallow = False
            self._press = None
            return
        if self._dragging:
            self._dragging = False
            self.state = 'act'
            self._set_anim('land')
            self._clamp()
        elif self._press is not None:
            self.click_timer.start(QApplication.doubleClickInterval())
        self._press = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.click_timer.stop()
            self._swallow = True
            self.start_walk()

    def _single_click(self):
        self.clicked.emit(QCursor.pos())

    def wheelEvent(self, e):
        self.set_scale(self.scale + (1 if e.angleDelta().y() > 0 else -1))

    # ---------- 拖放文件 ----------
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._touch()
            self.say("啊——放下来,交给三虎!", 3000)

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        e.acceptProposedAction()
        if paths:
            QTimer.singleShot(0, lambda: self.filesDropped.emit(paths))

    # ---------- 走路 ----------
    def start_walk(self):
        if self.state == 'drag' or self.busy:
            return
        scr = (QGuiApplication.screenAt(self.head_point()) or QGuiApplication.primaryScreen()).availableGeometry()
        lo, hi = scr.left(), scr.right() - self.width()
        for _ in range(8):
            tx = random.randint(lo, max(lo + 1, hi))
            if abs(tx - self.x()) > 140:
                break
        self._walk_target = tx
        self._walk_dir = 1 if tx > self.x() else -1
        self.state = 'walk'
        self._on_done = None
        self._set_anim('walk_r' if self._walk_dir > 0 else 'walk_l')
        self.walk_timer.start()
        self._last_touch = time.time()

    def _walk_step(self):
        if self.state != 'walk':
            self.walk_timer.stop()
            return
        x = self.x() + self._walk_dir * self.scale
        self.move(x, self.y())
        if (x - self._walk_target) * self._walk_dir >= 0:
            self.walk_timer.stop()
            self._rest()
            self.store.set('pos', [self.x(), self.y()])

    # ---------- 视线跟随 / 摸头 / 自主行为 ----------
    def _poll(self):
        pos = QCursor.pos()
        hc = self.head_point()
        dx, dy = pos.x() - hc.x(), pos.y() - hc.y()
        sc = self.scale
        if self.state == 'idle':
            gx = (dx > 14 * sc) - (dx < -14 * sc)
            gy = (dy > 12 * sc) - (dy < -12 * sc)
            name = f'idle_{gx + 1}{gy + 1}'
            if name != self.anim:
                self.anim = name
                self.frames = self.sp.frames(name, sc)
                self.update()
        inside = abs(dx) < 20 * sc and -22 * sc < dy < 34 * sc
        if inside and QApplication.mouseButtons() == Qt.NoButton:
            self._pet_acc += (pos - self._last_cursor).manhattanLength()
        self._pet_acc *= 0.95
        now = time.time()
        if self._pet_acc > 700 and now > self._pet_cool and self.state in ('idle', 'sleep'):
            self._pet_acc, self._pet_cool = 0, now + 6
            self.act('happy')
            self.say(random.choice(PURR), 2500)
        self._last_cursor = pos
        if self.recording:
            self.update()
        if self.state == 'idle' and not self.busy and not self.recording:
            hour = time.localtime().tm_hour
            if self.store.get('night_sleep') and (hour >= 23 or hour < 6) and now - self._last_touch > 120:
                self.state = 'sleep'
                self._set_anim('sleep')
            elif now > self._next_auto:
                self._next_auto = now + random.uniform(30, 80)
                if self.store.get('auto_wander') and random.random() < 0.6:
                    self.start_walk()
                elif not inside:
                    self.act(random.choice(['wave', 'jump']))
