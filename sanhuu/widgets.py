# -*- coding: utf-8 -*-
"""通用小部件(全部为 Qt 原生控件或自绘)。"""
from PySide6.QtCore import Qt, QTimer, QSize, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtWidgets import (QFrame, QLabel, QAbstractButton, QPushButton, QVBoxLayout, QHBoxLayout, QWidget)
from . import theme


def card(layout_cls=QVBoxLayout, margins=(18, 16, 18, 16), spacing=10):
    f = QFrame()
    f.setObjectName('card')
    lay = layout_cls(f)
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return f, lay


def label(text='', name=None, wrap=False):
    l = QLabel(text)
    l.setTextFormat(Qt.PlainText)
    if name:
        l.setObjectName(name)
    l.setWordWrap(wrap)
    return l


def button(text, name=None, on=None, checkable=False):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    if on:
        b.clicked.connect(on)
    return b


def pill(text, color):
    l = QLabel(text)
    l.setTextFormat(Qt.PlainText)
    l.setAlignment(Qt.AlignCenter)
    l.setStyleSheet(f"background:{color}; color:#FFFFFF; border-radius:10px; padding:0 10px; font-size:11px; font-weight:600;")
    l.setFixedHeight(20)
    return l


class CheckDot(QAbstractButton):
    """圆形勾选框(自绘)。"""

    def __init__(self, checked=False):
        super().__init__()
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        return QSize(24, 24)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(2, 2, 20, 20)
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.ACCENT))
            p.drawEllipse(r)
            p.setPen(QPen(QColor('#FFFFFF'), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            path = QPainterPath(QPointF(7.5, 12.5))
            path.lineTo(10.8, 15.5)
            path.lineTo(16.5, 9)
            p.drawPath(path)
        else:
            p.setPen(QPen(QColor(theme.ACCENT2 if self.underMouse() else '#C9C5BD'), 2))
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(r)


class AnimLabel(QLabel):
    """循环播放一段三虎精灵动画。"""

    def __init__(self, sprites, anim='idle_11', scale=2):
        super().__init__()
        self.sp, self.scale = sprites, scale
        self.setFixedSize(sprites.size * scale, sprites.size * scale)
        self._i = 0
        self._timer = QTimer(self, timeout=self._tick)
        self.play(anim)

    def play(self, anim):
        if not self.sp.has(anim):
            anim = 'idle_11'
        self._frames = self.sp.frames(anim, self.scale)
        self._i = 0
        self.setPixmap(self._frames[0])
        self._timer.start(int(1000 / self.sp.info(anim)['fps']))

    def _tick(self):
        if not self.isVisible():
            return
        self._i = (self._i + 1) % len(self._frames)
        self.setPixmap(self._frames[self._i])


class DropZone(QFrame):
    dropped = Signal(list)

    def __init__(self, text):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self._text = text
        self._hot = False

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._hot = True
            self.update()

    def dragLeaveEvent(self, e):
        self._hot = False
        self.update()

    def dropEvent(self, e):
        self._hot = False
        self.update()
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if paths:
            QTimer.singleShot(0, lambda: self.dropped.emit(paths))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(theme.ACCENT if self._hot else '#CFCAC1'), 2, Qt.DashLine)
        p.setPen(pen)
        p.setBrush(QColor('#FBEDE4' if self._hot else '#FFFFFF'))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 14, 14)
        p.setPen(QColor(theme.ACCENT if self._hot else theme.SUB))
        p.drawText(self.rect(), Qt.AlignCenter, self._text)
