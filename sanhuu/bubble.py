# -*- coding: utf-8 -*-
"""三虎的对话气泡(自绘)。"""
from PySide6.QtCore import Qt, QTimer, QRect, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPainterPath, QGuiApplication, QPolygonF
from PySide6.QtWidgets import QWidget
from . import theme


class Bubble(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                         | Qt.NoDropShadowWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_MacAlwaysShowToolWindow, True)
        self._text = ''
        self._cb = None
        self._font = QFont()
        self._font.setPointSize(11)
        self._timer = QTimer(self, singleShot=True, timeout=self.hide)
        self._tail_x = 0

    def popup(self, text, anchor, ms=4500, on_click=None):
        self._text, self._cb = text, on_click
        fm = QFontMetrics(self._font)
        r = fm.boundingRect(QRect(0, 0, 250, 2000), Qt.TextWordWrap, text)
        w, h = max(70, r.width() + 30), r.height() + 22 + 12
        self.resize(w, h)
        self.place(anchor)
        self.setCursor(Qt.PointingHandCursor if on_click else Qt.ArrowCursor)
        self.show()
        self.raise_()
        self.update()
        self._timer.start(ms)

    def place(self, anchor):
        x, y = anchor.x() - self.width() // 2, anchor.y() - self.height()
        scr = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
        g = scr.availableGeometry()
        x = max(g.left() + 4, min(x, g.right() - self.width() - 4))
        y = max(g.top() + 4, y)
        self._tail_x = max(18, min(self.width() - 18, anchor.x() - x))
        self.move(x, y)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        body = QRectF(1.5, 1.5, w - 3, h - 13)
        path = QPainterPath()
        path.addRoundedRect(body, 12, 12)
        tail = QPainterPath()
        tx = self._tail_x
        tail.addPolygon(QPolygonF([QPointF(tx - 7, h - 12.5), QPointF(tx + 7, h - 12.5), QPointF(tx, h - 2)]))
        path = path.united(tail)
        p.setPen(QPen(QColor(theme.INK), 2))
        p.setBrush(QColor('#FFFFFF'))
        p.drawPath(path)
        p.setFont(self._font)
        p.setPen(QColor(theme.INK))
        p.drawText(body.adjusted(13, 9, -13, -9).toRect(), Qt.TextWordWrap | Qt.AlignCenter, self._text)

    def mousePressEvent(self, e):
        cb, self._cb = self._cb, None
        self.hide()
        if cb:
            cb()
