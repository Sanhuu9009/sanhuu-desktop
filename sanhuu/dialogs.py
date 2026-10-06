# -*- coding: utf-8 -*-
"""对话框:拖入文件后的操作面板、录屏格式选择、电源倒计时、首次启动引导。"""
import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QButtonGroup,
                               QStackedWidget, QCheckBox, QWidget)
from . import theme, COPYRIGHT, APP_NAME, autostart
from .widgets import card, label, button, AnimLabel
from .convert import targets_for, category
from .scheduler import KIND_CN
from .paths import resource


class Base(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(resource('assets', 'icon.png')))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(22, 20, 22, 20)
        self.root.setSpacing(12)


class DropDialog(Base):
    """三虎接住文件后:转换 / 压缩 / 解压。结果在 self.action。"""

    def __init__(self, paths, sprites):
        super().__init__('三虎接住啦')
        self.action = None
        self.setMinimumWidth(500)
        top = QHBoxLayout()
        top.setSpacing(14)
        pic = label()
        pic.setPixmap(sprites.portrait(88, 'work', 1))
        top.addWidget(pic)
        v = QVBoxLayout()
        names = [os.path.basename(p.rstrip('/\\')) for p in paths]
        v.addWidget(label(f"三虎接住了 {len(paths)} 个文件" if len(paths) > 1 else names[0], 'h2', True))
        more = '、'.join(names[:3]) + (f" 等 {len(names)} 项" if len(names) > 3 else '')
        v.addWidget(label(more if len(paths) > 1 else '想让三虎怎么处理它?', 'sub', True))
        top.addLayout(v, 1)
        self.root.addLayout(top)

        cats = {category(p) for p in paths}
        if cats == {'archive'}:
            c, l = card()
            l.addWidget(label('解压', 'h2'))
            h = QHBoxLayout()
            self.xpw = QLineEdit()
            self.xpw.setEchoMode(QLineEdit.Password)
            self.xpw.setPlaceholderText('解压密码(没有就留空)')
            h.addWidget(self.xpw, 1)
            h.addWidget(button('解压到同名文件夹', 'primary', lambda: self._done(('extract', self.xpw.text()))))
            l.addLayout(h)
            self.root.addWidget(c)
        tg = targets_for(paths)
        if tg:
            c, l = card()
            l.addWidget(label('转换为', 'h2'))
            g = QGridLayout()
            g.setSpacing(8)
            for i, f in enumerate(tg):
                g.addWidget(button(f.upper(), 'fmt', lambda _=False, f=f: self._done(('convert', f))), i // 5, i % 5)
            l.addLayout(g)
            self.root.addWidget(c)
        c, l = card()
        l.addWidget(label('压缩为', 'h2'))
        h = QHBoxLayout()
        self.grp = QButtonGroup(self)
        for i, f in enumerate(('zip', '7z', 'rar')):
            b = button(f, 'chip', checkable=True)
            b.setChecked(i == 0)
            self.grp.addButton(b, i)
            h.addWidget(b)
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw.setPlaceholderText('设置密码(可选)')
        h.addWidget(self.pw, 1)
        h.addWidget(button('开始压缩', 'primary',
                           lambda: self._done(('compress', ('zip', '7z', 'rar')[self.grp.checkedId()], self.pw.text()))))
        l.addLayout(h)
        l.addWidget(label('zip 与 7z 使用 AES-256 加密;rar 需要电脑上已安装 WinRAR。', 'sub', True))
        self.root.addWidget(c)

    def _done(self, action):
        self.action = action
        self.accept()


class FormatDialog(Base):
    def __init__(self, fps, size):
        super().__init__('录屏')
        self.fmt = None
        self.root.addWidget(label('录成什么格式?', 'h2'))
        self.root.addWidget(label(f"分辨率 {size[0]} × {size[1]}(屏幕原生像素) · 帧率 {fps} fps", 'sub'))
        h = QHBoxLayout()
        for f, tip in (('mp4', 'MP4\nH.264 高画质'), ('gif', 'GIF\n原分辨率动图')):
            b = button(tip, 'fmt', lambda _=False, f=f: self._pick(f))
            b.setMinimumSize(150, 70)
            h.addWidget(b)
        self.root.addLayout(h)
        self.root.addWidget(label('开始后,点一下三虎(或托盘菜单)就能结束录制。\nGIF 受格式限制,帧率最高 50 fps。', 'sub', True))

    def _pick(self, f):
        self.fmt = f
        self.accept()


class CountdownDialog(Base):
    def __init__(self, kind, seconds=30):
        super().__init__('定时' + KIND_CN[kind])
        self.kind, self.left = kind, seconds
        self.msg = label('', 'h2')
        self.root.addWidget(self.msg)
        self.root.addWidget(label('还没保存的东西记得先保存哦。', 'sub'))
        h = QHBoxLayout()
        h.addWidget(button('取消', None, self.reject))
        h.addWidget(button('立即' + KIND_CN[kind], 'primary', self.accept))
        self.root.addLayout(h)
        self.t = QTimer(self, interval=1000, timeout=self._tick)
        self.t.start()
        self._show()

    def _show(self):
        self.msg.setText(f"三虎将在 {self.left} 秒后帮你{KIND_CN[self.kind]}")

    def _tick(self):
        self.left -= 1
        if self.left <= 0:
            self.accept()
        else:
            self._show()


class Onboarding(Base):
    """首次启动的介绍页。"""

    def __init__(self, sprites, store):
        super().__init__('认识一下三虎 Sanhuu')
        from .panel import CityPicker
        self.store = store
        self.setFixedSize(560, 520)
        self.stack = QStackedWidget()
        self.root.addWidget(self.stack, 1)
        # 第 1 页:欢迎
        p1 = QWidget()
        v = QVBoxLayout(p1)
        a = AnimLabel(sprites, 'wave', 3)
        v.addWidget(a, 0, Qt.AlignHCenter)
        t = label('嗷呜!我是三虎 Sanhuu', 'h1')
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)
        d = label('从今天起住在你的桌面上。我会看天气、截图录屏、转格式、压缩解压,\n还能帮你记待办、定闹钟。', 'sub', True)
        d.setAlignment(Qt.AlignCenter)
        v.addWidget(d)
        v.addStretch(1)
        cp = label(COPYRIGHT, 'sub', True)
        cp.setAlignment(Qt.AlignCenter)
        v.addWidget(cp)
        # 第 2 页:城市
        p2 = QWidget()
        v = QVBoxLayout(p2)
        hh = QHBoxLayout()
        hh.addWidget(AnimLabel(sprites, 'rain', 2))
        vv = QVBoxLayout()
        vv.addStretch(1)
        vv.addWidget(label('你在哪座城市?', 'h1'))
        vv.addWidget(label('告诉我之后,快下雨时我会提前撑伞提醒你。', 'sub', True))
        vv.addStretch(1)
        hh.addLayout(vv, 1)
        v.addLayout(hh)
        self.picker = CityPicker(store.city_hint or '')
        self.picker.chosen.connect(self._city)
        v.addWidget(self.picker)
        self.city_ok = label('', 'h2')
        v.addWidget(self.city_ok)
        v.addStretch(1)
        # 第 3 页:玩法
        p3 = QWidget()
        v = QVBoxLayout(p3)
        hh = QHBoxLayout()
        hh.addWidget(AnimLabel(sprites, 'happy', 2))
        g = QVBoxLayout()
        g.addWidget(label('怎么和我玩', 'h1'))
        for k, d in (('单击', '卖个萌,弹出菜单'), ('双击', '我去溜达一圈'), ('拖拽', '把我拎起来,松手我会跳下来'),
                     ('摸头', '鼠标在我身上来回蹭'), ('滚轮', '调整我的大小'), ('拖文件给我', '转格式 / 压缩 / 解压')):
            r = QHBoxLayout()
            kk = label(k, 'h2')
            kk.setFixedWidth(96)
            r.addWidget(kk)
            r.addWidget(label(d, 'sub'), 1)
            g.addLayout(r)
        hh.addLayout(g, 1)
        v.addLayout(hh)
        self.auto = QCheckBox('开机自动启动三虎')
        self.auto.setChecked(True)
        v.addWidget(self.auto)
        v.addStretch(1)
        for p in (p1, p2, p3):
            self.stack.addWidget(p)
        nav = QHBoxLayout()
        self.back = button('上一步', None, lambda: self._go(-1))
        self.next = button('下一步', 'primary', lambda: self._go(1))
        nav.addWidget(self.back)
        nav.addStretch(1)
        nav.addWidget(self.next)
        self.root.addLayout(nav)
        self._go(0)
        if store.city_hint:
            QTimer.singleShot(300, self.picker.search)

    def _city(self, c):
        self.store.set('city', c)
        self.picker.list.hide()
        self.picker.msg.hide()
        self.city_ok.setText(f"记住啦:{c['name']} ✓")

    def _go(self, d):
        i = self.stack.currentIndex() + d
        if i > 2:
            autostart.set_enabled(self.auto.isChecked())
            self.store.set('onboarded', True)
            return self.accept()
        self.stack.setCurrentIndex(i)
        self.back.setVisible(i > 0)
        self.next.setText('开始吧!' if i == 2 else ('下一步' if i == 0 or self.store.get('city') else '先跳过'))
        if i == 1:
            self.picker.chosen.connect(lambda _c: self.next.setText('下一步'))
