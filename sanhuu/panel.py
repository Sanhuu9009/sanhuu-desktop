# -*- coding: utf-8 -*-
"""主面板(Qt Widgets 原生界面):待办 / 定时 / 天气 / 工具箱 / 设置 / 关于。"""
import os, time
from datetime import datetime, date, timedelta
from PySide6.QtCore import Qt, QDate, QTime, QTimer, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QComboBox, QDateEdit,
                               QTimeEdit, QSpinBox, QCheckBox, QScrollArea, QStackedWidget, QButtonGroup, QFrame,
                               QListWidget, QListWidgetItem, QFileDialog, QSizePolicy)
from . import theme, VERSION, COPYRIGHT, APP_NAME, autostart
from .widgets import card, label, button, pill, CheckDot, AnimLabel, DropZone
from .scheduler import KIND_CN, next_fire
from .weather import search_city, KIND_CN as WX_CN, describe
from .jobs import run_async
from .paths import data_dir, resource

PRIO = [('高', theme.ACCENT), ('中', theme.GOLD), ('低', theme.GREEN)]


def scroll_wrap(inner):
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(inner)
    return sa


class Page(QWidget):
    def __init__(self, title, sub=''):
        super().__init__()
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(28, 24, 28, 20)
        self.root.setSpacing(14)
        self.title = label(title, 'h1')
        self.sub = label(sub, 'sub')
        self.root.addWidget(self.title)
        self.root.addWidget(self.sub)


# ---------------- 待办 ----------------
class TodoPage(Page):
    def __init__(self, store):
        super().__init__('待办清单')
        self.store = store
        self.filter = 0
        c, lay = card(QHBoxLayout, (14, 12, 14, 12))
        self.edit = QLineEdit()
        self.edit.setPlaceholderText('要做什么?写下来,回车添加')
        self.edit.returnPressed.connect(self.add)
        self.prio = QComboBox()
        self.prio.addItems(['优先级 高', '优先级 中', '优先级 低'])
        self.prio.setCurrentIndex(1)
        self.has_due = QCheckBox('截止')
        self.due = QDateEdit(QDate.currentDate())
        self.due.setCalendarPopup(True)
        self.due.setDisplayFormat('M月d日')
        self.due.setEnabled(False)
        self.has_due.toggled.connect(self.due.setEnabled)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.prio)
        lay.addWidget(self.has_due)
        lay.addWidget(self.due)
        lay.addWidget(button('添加', 'primary', self.add))
        self.root.addWidget(c)
        row = QHBoxLayout()
        self.grp = QButtonGroup(self)
        for i, t in enumerate(('全部', '进行中', '已完成')):
            b = button(t, 'chip', checkable=True)
            b.setChecked(i == 0)
            self.grp.addButton(b, i)
            row.addWidget(b)
        self.grp.idClicked.connect(self._set_filter)
        row.addStretch(1)
        row.addWidget(button('清除已完成', 'ghost', self.clear_done))
        self.root.addLayout(row)
        self.list_w = QWidget()
        self.list_l = QVBoxLayout(self.list_w)
        self.list_l.setContentsMargins(0, 0, 6, 0)
        self.list_l.setSpacing(8)
        self.root.addWidget(scroll_wrap(self.list_w), 1)
        self.refresh()

    def _set_filter(self, i):
        self.filter = i
        self.refresh()

    def add(self):
        t = self.edit.text().strip()
        if not t:
            return
        self.store.todos.append(dict(id=self.store.new_id(), title=t, done=False, prio=self.prio.currentIndex(),
                                     due=self.due.date().toString('yyyy-MM-dd') if self.has_due.isChecked() else None,
                                     created=time.time()))
        self.store.save()
        self.edit.clear()
        self.refresh()

    def clear_done(self):
        self.store.data['todos'] = [t for t in self.store.todos if not t['done']]
        self.store.save()
        self.refresh()

    def _toggle(self, tid, on):
        for t in self.store.todos:
            if t['id'] == tid:
                t['done'] = on
        self.store.save()
        QTimer.singleShot(120, self.refresh)

    def _delete(self, tid):
        self.store.data['todos'] = [t for t in self.store.todos if t['id'] != tid]
        self.store.save()
        self.refresh()

    def refresh(self):
        while self.list_l.count():
            it = self.list_l.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        todos = sorted(self.store.todos, key=lambda t: (t['done'], t['prio'], t['due'] or '9999', t['created']))
        left = sum(1 for t in todos if not t['done'])
        self.sub.setText(f"还有 {left} 件事等着你,三虎陪你一件件划掉" if left else "全部搞定!三虎给你鼓掌 (ง •̀_•́)ง")
        shown = [t for t in todos if self.filter == 0 or (self.filter == 1) != t['done']]
        today = date.today().isoformat()
        for t in shown:
            f = QFrame()
            f.setObjectName('row')
            h = QHBoxLayout(f)
            h.setContentsMargins(14, 10, 10, 10)
            h.setSpacing(12)
            dot = CheckDot(t['done'])
            dot.toggled.connect(lambda on, tid=t['id']: self._toggle(tid, on))
            h.addWidget(dot)
            v = QVBoxLayout()
            v.setSpacing(2)
            ttl = label(t['title'])
            fnt = ttl.font()
            fnt.setPointSize(11)
            fnt.setStrikeOut(t['done'])
            ttl.setFont(fnt)
            if t['done']:
                ttl.setStyleSheet(f"color:{theme.SUB};")
            v.addWidget(ttl)
            if t['due']:
                d = datetime.strptime(t['due'], '%Y-%m-%d')
                txt = f"{d.month}月{d.day}日截止"
                col = theme.SUB
                if not t['done']:
                    if t['due'] < today:
                        txt, col = f"已逾期 · {d.month}月{d.day}日", '#D64545'
                    elif t['due'] == today:
                        txt, col = '今天截止', theme.ACCENT
                dl = label(txt)
                dl.setStyleSheet(f"color:{col}; font-size:11px;")
                v.addWidget(dl)
            h.addLayout(v, 1)
            name, col = PRIO[t['prio']]
            h.addWidget(pill(name, col if not t['done'] else '#C9C5BD'))
            h.addWidget(button('✕', 'ghost', lambda _=False, tid=t['id']: self._delete(tid)))
            self.list_l.addWidget(f)
        if not shown:
            e = label('这里空空的。' if self.filter else '还没有待办,在上面写一条吧。', 'sub')
            e.setAlignment(Qt.AlignCenter)
            e.setMinimumHeight(120)
            self.list_l.addWidget(e)
        self.list_l.addStretch(1)

    def due_today(self):
        today = date.today().isoformat()
        return [t for t in self.store.todos if not t['done'] and t['due'] and t['due'] <= today]


# ---------------- 定时 ----------------
class TimerPage(Page):
    def __init__(self, store, sched):
        super().__init__('定时任务', '到点提醒你,或者帮你关机、睡眠、重启(执行前会有 30 秒倒计时,可以反悔)')
        self.store, self.sched = store, sched
        c, g = card(QGridLayout)
        g.setHorizontalSpacing(10)
        self.kind = QComboBox()
        self.kind.addItems(['提醒我', '关机', '睡眠', '重启'])
        self.mode = QComboBox()
        self.mode.addItems(['在指定时间', '倒计时'])
        self.time = QTimeEdit(QTime.currentTime().addSecs(600))
        self.time.setDisplayFormat('HH:mm')
        self.mins = QSpinBox()
        self.mins.setRange(1, 1440)
        self.mins.setValue(25)
        self.mins.setSuffix(' 分钟后')
        self.mins.hide()
        self.daily = QCheckBox('每天重复')
        self.text = QLineEdit()
        self.text.setPlaceholderText('提醒内容,例如:起来喝水、活动一下')
        self.mode.currentIndexChanged.connect(self._mode)
        self.kind.currentIndexChanged.connect(lambda i: self.text.setEnabled(i == 0))
        g.addWidget(self.kind, 0, 0)
        g.addWidget(self.mode, 0, 1)
        g.addWidget(self.time, 0, 2)
        g.addWidget(self.mins, 0, 2)
        g.addWidget(self.daily, 0, 3)
        g.addWidget(self.text, 1, 0, 1, 3)
        g.addWidget(button('添加任务', 'primary', self.add), 1, 3)
        g.setColumnStretch(2, 1)
        self.root.addWidget(c)
        self.list_w = QWidget()
        self.list_l = QVBoxLayout(self.list_w)
        self.list_l.setContentsMargins(0, 0, 6, 0)
        self.list_l.setSpacing(8)
        self.root.addWidget(scroll_wrap(self.list_w), 1)
        sched.changed.connect(self.refresh)
        self.refresh()

    def _mode(self, i):
        self.time.setVisible(i == 0)
        self.mins.setVisible(i == 1)
        self.daily.setEnabled(i == 0)
        if i == 1:
            self.daily.setChecked(False)

    def add(self):
        kind = ['remind', 'shutdown', 'sleep', 'restart'][self.kind.currentIndex()]
        text = self.text.text().strip() if kind == 'remind' else ''
        now = datetime.now()
        if self.mode.currentIndex() == 1:
            self.sched.add(kind, text, at=now + timedelta(minutes=self.mins.value()))
        else:
            t = self.time.time()
            if self.daily.isChecked():
                self.sched.add(kind, text, daily=True, time_hm=f"{t.hour():02d}:{t.minute():02d}")
            else:
                at = now.replace(hour=t.hour(), minute=t.minute(), second=0, microsecond=0)
                if at <= now:
                    at += timedelta(days=1)
                self.sched.add(kind, text, at=at)
        self.text.clear()

    def refresh(self):
        while self.list_l.count():
            it = self.list_l.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        tasks = [(next_fire(t), t) for t in self.store.tasks]
        tasks.sort(key=lambda x: (x[0] is None, x[0] or datetime.max))
        cols = {'remind': theme.BLUE, 'shutdown': '#D64545', 'sleep': '#7A6FD6', 'restart': theme.ACCENT2}
        for nf, t in tasks:
            f = QFrame()
            f.setObjectName('row')
            h = QHBoxLayout(f)
            h.setContentsMargins(14, 10, 10, 10)
            h.setSpacing(12)
            h.addWidget(pill(KIND_CN[t['kind']], cols[t['kind']] if nf else '#C9C5BD'))
            v = QVBoxLayout()
            v.setSpacing(2)
            v.addWidget(label(t['text'] or ('到点' + KIND_CN[t['kind']])))
            if nf is None:
                when = '已完成'
            else:
                day = '今天' if nf.date() == date.today() else ('明天' if nf.date() == date.today() + timedelta(days=1) else f"{nf.month}月{nf.day}日")
                when = ('每天 ' + t['time'] + ' · 下次' + day) if t.get('daily') else f"{day} {nf.strftime('%H:%M')}"
            v.addWidget(label(when, 'sub'))
            h.addLayout(v, 1)
            h.addWidget(button('✕', 'ghost', lambda _=False, tid=t['id']: self.sched.remove(tid)))
            self.list_l.addWidget(f)
        if not tasks:
            e = label('还没有定时任务。', 'sub')
            e.setAlignment(Qt.AlignCenter)
            e.setMinimumHeight(120)
            self.list_l.addWidget(e)
        self.list_l.addStretch(1)


# ---------------- 城市搜索(天气页与引导页共用) ----------------
class CityPicker(QWidget):
    chosen = Signal(dict)

    def __init__(self, hint=''):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        h = QHBoxLayout()
        self.edit = QLineEdit(hint)
        self.edit.setPlaceholderText('输入城市名,例如:上海 / Singapore / 東京')
        self.edit.returnPressed.connect(self.search)
        self.btn = button('搜索', 'primary', self.search)
        h.addWidget(self.edit, 1)
        h.addWidget(self.btn)
        v.addLayout(h)
        self.msg = label('', 'sub')
        self.msg.hide()
        v.addWidget(self.msg)
        self.list = QListWidget()
        self.list.setMaximumHeight(170)
        self.list.hide()
        self.list.itemClicked.connect(lambda it: self.chosen.emit(it.data(Qt.UserRole)))
        v.addWidget(self.list)

    def search(self):
        q = self.edit.text().strip()
        if not q:
            return
        self.btn.setEnabled(False)
        self.msg.setText('三虎正在翻地图……')
        self.msg.show()
        run_async(search_city, self._ok, self._fail, q)

    def _ok(self, res):
        self.btn.setEnabled(True)
        self.list.clear()
        if not res:
            self.msg.setText('没找到这个城市,换个写法试试(中文、英文、拼音都可以)')
            self.list.hide()
            return
        self.msg.setText('点一下选择你所在的城市:')
        for c in res:
            it = QListWidgetItem(' · '.join(x for x in (c['name'], c['admin'], c['country']) if x))
            it.setData(Qt.UserRole, c)
            self.list.addItem(it)
        self.list.show()

    def _fail(self, e):
        self.btn.setEnabled(True)
        self.msg.setText('联网失败了,检查一下网络再试试')
        self.msg.show()


# ---------------- 天气 ----------------
class WeatherPage(Page):
    perform = Signal(str)

    def __init__(self, store, weather, sprites):
        super().__init__('天气', '变天之前,三虎会先跑出来提醒你')
        self.store, self.weather = store, weather
        c, h = card(QHBoxLayout, (10, 10, 22, 10), 18)
        self.anim = AnimLabel(sprites, 'cloudy', 2)
        h.addWidget(self.anim)
        v = QVBoxLayout()
        v.setSpacing(4)
        self.city_l = label('还没有设置城市', 'h2')
        self.temp = label('--°', 'big')
        self.desc = label('', 'h2')
        self.detail = label('', 'sub', wrap=True)
        v.addStretch(1)
        for w in (self.city_l, self.temp, self.desc, self.detail):
            v.addWidget(w)
        v.addStretch(1)
        h.addLayout(v, 1)
        bv = QVBoxLayout()
        bv.addStretch(1)
        bv.addWidget(button('让三虎表演', 'primary', lambda: self.perform.emit(self.weather.data['kind'] if self.weather.data else 'cloudy')))
        bv.addWidget(button('刷新', None, self.weather.refresh))
        bv.addStretch(1)
        h.addLayout(bv)
        self.root.addWidget(c)
        self.hours = QHBoxLayout()
        self.hours.setSpacing(8)
        self.root.addLayout(self.hours)
        self.tomorrow = label('', 'sub', wrap=True)
        self.root.addWidget(self.tomorrow)
        c2, l2 = card()
        l2.addWidget(label('所在城市', 'h2'))
        self.picker = CityPicker()
        self.picker.chosen.connect(self._choose)
        l2.addWidget(self.picker)
        self.root.addWidget(c2)
        self.root.addStretch(1)
        weather.updated.connect(self.show_data)
        weather.failed.connect(lambda m: self.detail.setText('天气没取到,稍后三虎会再试一次'))
        if weather.data:
            self.show_data(weather.data)
        elif store.get('city'):
            self.city_l.setText(store.get('city')['name'])

    def _choose(self, c):
        self.store.set('city', c)
        self.picker.list.hide()
        self.picker.msg.setText(f"好的,以后就看{c['name']}的天气啦")
        self.city_l.setText(c['name'])
        self.weather._last_kind = None
        self.weather.refresh()

    def show_data(self, w):
        city = self.store.get('city') or {'name': ''}
        self.city_l.setText(city['name'])
        self.temp.setText(f"{round(w['temp'])}°C")
        self.desc.setText(w['desc'])
        bits = []
        if w.get('feels') is not None:
            bits.append(f"体感 {round(w['feels'])}°")
        if w.get('hum') is not None:
            bits.append(f"湿度 {round(w['hum'])}%")
        bits.append(f"风速 {round(w['wind'])} km/h")
        self.detail.setText('   '.join(bits))
        self.anim.play(w['kind'])
        while self.hours.count():
            it = self.hours.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for hr in w['hours'][:8]:
            f, l = card(QVBoxLayout, (6, 10, 6, 10), 3)
            for txt, nm in ((hr['time'], 'sub'), (WX_CN.get(hr['kind'], ''), 'h2'), (f"{round(hr['temp'])}°", None),
                            (f"降水 {hr['pop']}%" if hr.get('pop') is not None else ' ', 'sub')):
                x = label(txt, nm)
                x.setAlignment(Qt.AlignCenter)
                l.addWidget(x)
            self.hours.addWidget(f)
        if len(w['days']) > 1:
            d = w['days'][1]
            pop = f",降水概率 {d['pop']}%" if d.get('pop') is not None else ''
            self.tomorrow.setText(f"明天:{d['desc']},{round(d['tmin'])}° ~ {round(d['tmax'])}°{pop}")


# ---------------- 工具箱 ----------------
class ToolsPage(Page):
    files = Signal(list)
    shot = Signal(str)
    rec = Signal(str)

    def __init__(self, store):
        super().__init__('工具箱', '把文件直接拖到三虎身上也可以——它会问你想转换、压缩还是解压')
        self.store = store
        dz = DropZone('把文件或文件夹拖到这里\n图片 / 文档 / 视频 / 音频 转格式 · 压缩成 zip / 7z / rar · 解压 zip / 7z / rar')
        dz.dropped.connect(self.files.emit)
        self.root.addWidget(dz)
        self.root.addWidget(button('或者,点这里选择文件…', None, self._choose))
        g = QGridLayout()
        g.setSpacing(10)
        c1, l1 = card()
        l1.addWidget(label('截图', 'h2'))
        l1.addWidget(label('保存为 PNG 并复制到剪贴板', 'sub'))
        h = QHBoxLayout()
        for t, m in (('全屏', 'full'), ('窗口', 'window'), ('框选', 'region')):
            h.addWidget(button(t, None, lambda _=False, m=m: self.shot.emit(m)))
        l1.addLayout(h)
        c2, l2 = card()
        l2.addWidget(label('录屏', 'h2'))
        l2.addWidget(label('原生分辨率与刷新率,输出 MP4 或 GIF', 'sub'))
        h = QHBoxLayout()
        for t, m in (('全屏', 'full'), ('窗口', 'window'), ('框选', 'region')):
            h.addWidget(button(t, None, lambda _=False, m=m: self.rec.emit(m)))
        l2.addLayout(h)
        g.addWidget(c1, 0, 0)
        g.addWidget(c2, 0, 1)
        self.root.addLayout(g)
        c3, l3 = card(QHBoxLayout)
        self.out = label('', 'sub')
        l3.addWidget(label('截图 / 录屏保存到'))
        l3.addWidget(self.out, 1)
        l3.addWidget(button('更改', None, self._change))
        self.root.addWidget(c3)
        self.root.addStretch(1)
        self._show_out()

    def _show_out(self):
        self.out.setText(self.store.output_dir())

    def _choose(self):
        fs, _ = QFileDialog.getOpenFileNames(self, '选择要交给三虎的文件')
        if fs:
            self.files.emit(fs)

    def _change(self):
        d = QFileDialog.getExistingDirectory(self, '选择保存位置', self.store.output_dir())
        if d:
            self.store.set('output_dir', d)
            self._show_out()


# ---------------- 设置 ----------------
class SettingsPage(Page):
    scale_changed = Signal(int)
    demo = Signal(str)

    def __init__(self, store, sprites):
        super().__init__('设置')
        self.sub.hide()
        self.store = store
        c, g = card(QGridLayout)
        g.setVerticalSpacing(14)
        g.setColumnStretch(1, 1)
        r = 0

        def row(name, w, tip=''):
            nonlocal r
            g.addWidget(label(name), r, 0)
            g.addWidget(w, r, 2)
            if tip:
                g.addWidget(label(tip, 'sub'), r, 1)
            r += 1
        self.size = QComboBox()
        self.size.addItems(['小 (2×)', '中 (3×)', '大 (4×)', '特大 (5×)'])
        self.size.setCurrentIndex(int(store.get('scale')) - 2)
        self.size.currentIndexChanged.connect(lambda i: self.scale_changed.emit(i + 2))
        row('三虎的大小', self.size, '在三虎身上滚动鼠标滚轮也能调')
        self.wander = QCheckBox('开启')
        self.wander.setChecked(bool(store.get('auto_wander')))
        self.wander.toggled.connect(lambda v: store.set('auto_wander', v))
        row('自己溜达', self.wander, '没事的时候在屏幕上走一走')
        self.night = QCheckBox('开启')
        self.night.setChecked(bool(store.get('night_sleep')))
        self.night.toggled.connect(lambda v: store.set('night_sleep', v))
        row('深夜打瞌睡', self.night, '23 点到 6 点,没人理就睡觉')
        self.auto = QCheckBox('开启')
        self.auto.setChecked(autostart.is_enabled())
        self.auto.toggled.connect(autostart.set_enabled)
        row('开机自动启动', self.auto)
        self.remind = QComboBox()
        self._rv = [0, 30, 60, 120, 180]
        self.remind.addItems(['只在变天时', '每 30 分钟', '每 1 小时', '每 2 小时', '每 3 小时'])
        self.remind.setCurrentIndex(self._rv.index(store.get('weather_remind_min')) if store.get('weather_remind_min') in self._rv else 2)
        self.remind.currentIndexChanged.connect(lambda i: store.set('weather_remind_min', self._rv[i]))
        row('天气播报', self.remind, '用大约 10 秒的天气动画提醒你')
        self.fps = QComboBox()
        self._fv = ['native', '60', '30']
        self.fps.addItems(['跟随显示器刷新率(原生)', '60 帧', '30 帧'])
        self.fps.setCurrentIndex(self._fv.index(str(store.get('record_fps'))) if str(store.get('record_fps')) in self._fv else 0)
        self.fps.currentIndexChanged.connect(lambda i: store.set('record_fps', self._fv[i]))
        row('录屏帧率', self.fps, '分辨率始终为屏幕物理像素')
        self.demo_c = QComboBox()
        self._dv = [('待机', 'idle'), ('走路', 'walk'), ('开心', 'happy'), ('跳跃', 'jump'), ('卖萌', 'wave'),
                    ('下雨', 'rain'), ('晴天', 'sunny'), ('多云', 'cloudy'), ('下雪', 'snow'), ('打雷', 'thunder'),
                    ('大风', 'wind'), ('睡觉', 'sleep')]
        self.demo_c.addItems([n for n, _ in self._dv])
        self.demo_c.setCurrentIndex(5)
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.demo_c)
        h.addWidget(button('播放', None, lambda: self.demo.emit(self._dv[self.demo_c.currentIndex()][1])))
        row('动画预览', w, '让三虎现在表演一段')
        self.root.addWidget(c)
        self.root.addStretch(1)


# ---------------- 关于 ----------------
class AboutPage(Page):
    def __init__(self, sprites):
        super().__init__('关于')
        self.sub.hide()
        c, h = card(QHBoxLayout, (10, 10, 24, 10), 16)
        h.addWidget(AnimLabel(sprites, 'wave', 2))
        v = QVBoxLayout()
        v.addStretch(1)
        v.addWidget(label(APP_NAME, 'h1'))
        v.addWidget(label(f'桌面宠物 · 版本 {VERSION}', 'sub'))
        v.addWidget(label('一只住在你桌面上的像素小老虎。会看天气、截图录屏、转格式、压缩解压、记待办、定闹钟。', None, True))
        v.addStretch(1)
        h.addLayout(v, 1)
        self.root.addWidget(c)
        c2, l2 = card()
        l2.addWidget(label('版权声明', 'h2'))
        l2.addWidget(label(COPYRIGHT, None, True))
        self.root.addWidget(c2)
        c3, l3 = card()
        l3.addWidget(label('使用的开源项目', 'h2'))
        l3.addWidget(label('Qt for Python (PySide6, LGPL) · FFmpeg · Pillow · pyzipper · py7zr · 7-Zip · pypdf · '
                           'pypdfium2 · python-docx · Open-Meteo 天气数据 (CC BY 4.0)。'
                           '界面为 Qt Widgets 原生控件,不含任何网页或 WebView 组件。', 'sub', True))
        self.root.addWidget(c3)
        self.root.addWidget(label('数据保存在:' + data_dir(), 'sub', True))
        self.root.addStretch(1)


class MainPanel(QWidget):
    def __init__(self, app):
        super().__init__()
        self.setObjectName('root')
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(resource('assets', 'icon.png')))
        self.resize(900, 640)
        self.setMinimumSize(820, 560)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        side = QWidget()
        side.setObjectName('sidebar')
        side.setFixedWidth(196)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(14, 22, 14, 16)
        sv.setSpacing(6)
        av = label(name='avatar')
        av.setPixmap(app.sprites.portrait(88))
        av.setAlignment(Qt.AlignCenter)
        av.setFixedSize(108, 100)
        sv.addWidget(av, 0, Qt.AlignHCenter)
        sv.addSpacing(6)
        b = label('三虎 Sanhuu', 'brand')
        b.setAlignment(Qt.AlignCenter)
        sv.addWidget(b)
        s = label('你的桌面小老虎', 'brandSub')
        s.setAlignment(Qt.AlignCenter)
        sv.addWidget(s)
        sv.addSpacing(14)
        self.stack = QStackedWidget()
        self.todo = TodoPage(app.store)
        self.timer = TimerPage(app.store, app.sched)
        self.wx = WeatherPage(app.store, app.weather, app.sprites)
        self.tools = ToolsPage(app.store)
        self.settings = SettingsPage(app.store, app.sprites)
        self.about = AboutPage(app.sprites)
        self.grp = QButtonGroup(self)
        self.names = ['todo', 'timer', 'weather', 'tools', 'settings', 'about']
        for i, (t, pg) in enumerate((('待办清单', self.todo), ('定时任务', self.timer), ('天气', self.wx),
                                     ('工具箱', self.tools), ('设置', self.settings), ('关于', self.about))):
            nb = button(t, 'nav', checkable=True)
            self.grp.addButton(nb, i)
            sv.addWidget(nb)
            self.stack.addWidget(pg)
        self.grp.idClicked.connect(self.stack.setCurrentIndex)
        sv.addStretch(1)
        cp = label('美术素材 © 三虎 Sanhuu\n保留所有权利', 'brandSub')
        cp.setAlignment(Qt.AlignCenter)
        sv.addWidget(cp)
        root.addWidget(side)
        root.addWidget(self.stack, 1)
        self.open('todo')

    def open(self, name):
        i = self.names.index(name)
        self.grp.button(i).setChecked(True)
        self.stack.setCurrentIndex(i)
        if name == 'todo':
            self.todo.refresh()
        self.show()
        self.raise_()
        self.activateWindow()
