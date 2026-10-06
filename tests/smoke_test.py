# -*- coding: utf-8 -*-
"""无头冒烟测试:QT_QPA_PLATFORM=offscreen python tests/smoke_test.py
覆盖:精灵加载、状态机(拖拽/双击走路/落地)、天气解析与变天判断、定时任务、压缩解压(含密码)、图片转换。"""
import os, sys, tempfile
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['HOME'] = tempfile.mkdtemp()
os.environ['APPDATA'] = os.environ['HOME']
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from datetime import datetime, timedelta
from PySide6.QtCore import Qt, QTimer, QPoint, QPointF, QEvent, QEventLoop
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication
from sanhuu import theme, weather, archive, convert
from sanhuu.app import App


def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


qapp = QApplication(sys.argv)
qapp.setStyleSheet(theme.QSS)
qapp.setQuitOnLastWindowClosed(False)
app = App(qapp)
app.store.set('onboarded', True)
pet = app.pet
pet.place_default()
pet.show()

# 1. 必备动画齐全
need = ['idle_11', 'walk_l', 'walk_r', 'happy', 'rain', 'jump', 'drag', 'land', 'sunny', 'cloudy', 'snow', 'thunder', 'wind']
assert all(app.sprites.has(n) for n in need)
assert abs(app.sprites.info('rain')['frames'] / app.sprites.info('rain')['fps'] - 10) < 0.01   # 10 秒

# 2. 鼠标交互状态机
def ev(t, pos, btns=Qt.LeftButton):
    return QMouseEvent(t, QPointF(pos), QPointF(pet.mapToGlobal(pos)), Qt.LeftButton, btns, Qt.NoModifier)
c = QPoint(pet.width() // 2, pet.height() // 2)
pet._rest()
pet.mousePressEvent(ev(QEvent.MouseButtonPress, c))
pet.mouseMoveEvent(ev(QEvent.MouseMove, c + QPoint(30, 10)))
assert pet.state == 'drag'
pet.mouseReleaseEvent(ev(QEvent.MouseButtonRelease, c + QPoint(30, 10), Qt.NoButton))
assert pet.anim == 'land'
wait(700)
assert pet.state == 'idle'
pet.mouseDoubleClickEvent(ev(QEvent.MouseButtonDblClick, c))
assert pet.state == 'walk'
pet._rest()

# 3. 天气:当前多云、2 小时后下雨 → 触发变天提醒
hrs = [f"2026-10-06T{h:02d}:00" for h in range(24)]
raw = dict(current=dict(time='2026-10-06T14:15', temperature_2m=30, apparent_temperature=34, relative_humidity_2m=70,
                        weather_code=2, wind_speed_10m=10),
           hourly=dict(time=hrs, temperature_2m=[28] * 24, weather_code=[2] * 16 + [80] * 8,
                       precipitation_probability=[10] * 16 + [90] * 8, wind_speed_10m=[8] * 24),
           daily=dict(time=['2026-10-06'], weather_code=[80], temperature_2m_max=[32], temperature_2m_min=[26],
                      precipitation_probability_max=[90]))
w = weather.parse(raw)
assert w['kind'] == 'cloudy' and weather.upcoming_change(w)[0] == 'rain'
app.store.set('city', dict(name='测试城', lat=0, lon=0))
app.weather._ok(w)
app.weather._ok(w)
assert pet.anim == 'rain', pet.anim

# 4. 定时提醒
pet._rest()
app.sched.add('remind', '喝水', at=datetime.now() - timedelta(seconds=3))
app.sched.check()
assert pet.anim == 'jump' and '喝水' in pet.bubble._text

# 5. 压缩 / 解压(含密码)与图片转换
d = tempfile.mkdtemp()
open(os.path.join(d, '文件.txt'), 'w', encoding='utf-8').write('三虎')
for fmt in ('zip', '7z'):
    out = archive.compress([os.path.join(d, '文件.txt')], fmt, '密码123')
    try:
        archive.extract(out)
        raise SystemExit('应当要求密码')
    except archive.NeedPassword:
        pass
    assert open(os.path.join(archive.extract(out, '密码123'), '文件.txt'), encoding='utf-8').read() == '三虎'
from PIL import Image
Image.new('RGBA', (32, 32), (255, 0, 0, 255)).save(os.path.join(d, 'a.png'))
for f in ('jpg', 'webp', 'ico'):
    assert os.path.getsize(convert.convert(os.path.join(d, 'a.png'), f)) > 0
assert os.path.getsize(convert.convert(os.path.join(d, '文件.txt'), 'pdf')) > 0
print('ALL OK')
