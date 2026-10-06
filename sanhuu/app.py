# -*- coding: utf-8 -*-
"""应用装配:把桌宠、菜单、托盘、各功能服务连起来。"""
import os, sys, time, random
from PySide6.QtCore import Qt, QTimer, QObject, QLockFile, QPoint
from PySide6.QtGui import QIcon, QAction, QGuiApplication, QCursor
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QInputDialog, QLineEdit, QMessageBox
from . import APP_NAME, theme
from .store import Store
from .sprites import Sprites
from .pet import Pet
from .weather import WeatherService, describe
from .scheduler import Scheduler, power, KIND_CN
from .capture import Picker, Recorder, grab, crop, current_screen, native_fps, stamp_name
from .dialogs import DropDialog, FormatDialog, CountdownDialog, Onboarding
from .jobs import run_async
from .paths import resource, reveal, data_dir
from . import convert, archive


class App(QObject):
    def __init__(self, qapp):
        super().__init__()
        self.qapp = qapp
        self.store = Store()
        self.sprites = Sprites()
        self.pet = Pet(self.sprites, self.store)
        self.weather = WeatherService(self.store)
        self.sched = Scheduler(self.store)
        self.rec = Recorder(self)
        self.panel = None
        self._picker = None
        self._last_wx_show = 0

        self.pet.clicked.connect(self.on_click)
        self.pet.filesDropped.connect(self.handle_files)
        self.weather.changed.connect(lambda k, t: self.show_weather(k, t))
        self.weather.alert.connect(self.weather_alert)
        self.sched.fire.connect(self.on_task)
        self.rec.finished.connect(self.rec_done)
        self.rec.failed.connect(self.rec_failed)

        self.tray = QSystemTrayIcon(QIcon(resource('assets', 'icon.png')), self)
        self.tray.setToolTip(APP_NAME)
        self.tray_menu = self.build_menu()
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(lambda r: self.pet.raise_() if r == QSystemTrayIcon.Trigger else None)
        self.tray.show()

        self.wx_timer = QTimer(self, interval=60 * 1000, timeout=self.wx_tick)
        self.wx_timer.start()

    # ---------- 启动 ----------
    def start(self):
        self.pet.place_default()
        self.pet.show()
        if not self.store.get('onboarded'):
            Onboarding(self.sprites, self.store).exec()
            self.pet.act('happy')
            self.pet.say("以后请多关照!点我一下看看菜单~", 6000)
        else:
            self.pet.act('wave')
            QTimer.singleShot(1500, self.greet)
        QTimer.singleShot(2500, self.weather.refresh)

    def greet(self):
        h = time.localtime().tm_hour
        hi = '早上好' if 5 <= h < 11 else '中午好' if h < 14 else '下午好' if h < 18 else '晚上好'
        due = [t for t in self.store.todos if not t['done'] and t.get('due') and t['due'] <= time.strftime('%Y-%m-%d')]
        if due:
            self.pet.say(f"{hi}!今天有 {len(due)} 件待办到期,点我看看", 7000, lambda: self.open_panel('todo'))
        else:
            self.pet.say(f"{hi}!三虎上班啦~", 3500)

    # ---------- 菜单 ----------
    def build_menu(self):
        m = QMenu()
        m.setWindowFlag(Qt.FramelessWindowHint, True)
        m.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        m.setAttribute(Qt.WA_TranslucentBackground)
        if self.rec.active:
            m.addAction('⏹  结束录制', self.stop_record)
            m.addSeparator()
        s = m.addMenu('📸  截图')
        s.addAction('全屏', lambda: self.screenshot('full'))
        s.addAction('选择窗口', lambda: self.screenshot('window'))
        s.addAction('框选区域', lambda: self.screenshot('region'))
        r = m.addMenu('🎬  录屏')
        r.addAction('全屏录制', lambda: self.record('full'))
        r.addAction('窗口录制', lambda: self.record('window'))
        r.addAction('框选区域录制', lambda: self.record('region'))
        for sub in (s, r):
            sub.setWindowFlag(Qt.FramelessWindowHint, True)
            sub.setWindowFlag(Qt.NoDropShadowWindowHint, True)
            sub.setAttribute(Qt.WA_TranslucentBackground)
        m.addSeparator()
        m.addAction('✅  待办清单', lambda: self.open_panel('todo'))
        m.addAction('⏰  定时任务', lambda: self.open_panel('timer'))
        m.addAction('⛅  今日天气', self.tell_weather)
        m.addAction('🧰  转换 / 压缩 / 解压', lambda: self.open_panel('tools'))
        m.addSeparator()
        m.addAction('🐾  去溜达', self.pet.start_walk)
        m.addAction('⚙  设置', lambda: self.open_panel('settings'))
        m.addAction('关于三虎', lambda: self.open_panel('about'))
        m.addSeparator()
        m.addAction('再见(退出)', self.quit)
        return m

    def on_click(self, pos):
        if self.rec.active:
            return self.stop_record()
        self.pet.act('wave')
        self._menu = self.build_menu()
        self._menu.popup(pos + QPoint(8, 8))

    def open_panel(self, name):
        if self.panel is None:
            from .panel import MainPanel
            self.panel = MainPanel(self)
            self.panel.wx.perform.connect(lambda k: self.show_weather(k, None))
            self.panel.tools.files.connect(self.handle_files)
            self.panel.tools.shot.connect(lambda m: (self.panel.hide(), QTimer.singleShot(250, lambda: self.screenshot(m))))
            self.panel.tools.rec.connect(lambda m: (self.panel.hide(), QTimer.singleShot(250, lambda: self.record(m))))
            self.panel.settings.scale_changed.connect(self.pet.set_scale)
            self.panel.settings.demo.connect(self.demo)
        self.panel.open(name)

    def demo(self, name):
        if name == 'walk':
            self.pet.start_walk()
        elif name == 'idle':
            self.pet._rest()
        elif name == 'sleep':
            self.pet.state = 'sleep'
            self.pet._set_anim('sleep')
        else:
            self.pet.act(name)

    def quit(self):
        if self.rec.active:
            self.rec.stop()
        self.pet.bubble.hide()
        self.tray.hide()
        self.qapp.quit()

    # ---------- 天气 ----------
    def show_weather(self, kind, text):
        self._last_wx_show = time.time()
        self.pet.act(kind)
        if text:
            self.pet.say(text, 10000)

    def weather_alert(self, kind, text):
        self.show_weather(kind, text)
        self.tray.showMessage('三虎的天气提醒', text, QSystemTrayIcon.Information, 8000)

    def tell_weather(self):
        city, w = self.store.get('city'), self.weather.data
        if not city:
            self.pet.say("还不知道你在哪座城市呢,点我去设置", 6000, lambda: self.open_panel('weather'))
        elif not w:
            self.pet.say("三虎正在看天……稍等一下下", 3000)
            self.weather.refresh()
        else:
            self.show_weather(w['kind'], describe(w, city))
            self.pet.bubble._cb = lambda: self.open_panel('weather')

    def wx_tick(self):
        every = self.store.get('weather_remind_min') or 0
        w, city = self.weather.data, self.store.get('city')
        if every and w and city and time.time() - self._last_wx_show > every * 60 and self.pet.state == 'idle':
            self.show_weather(w['kind'], describe(w, city))

    # ---------- 定时 ----------
    def on_task(self, t):
        if t['kind'] == 'remind':
            text = t.get('text') or '时间到啦!'
            self.pet.act('jump', lambda: self.pet.act('happy'))
            self.pet.say('⏰ ' + text, 20000)
            self.tray.showMessage('三虎提醒你', text, QSystemTrayIcon.Information, 15000)
            QApplication.beep()
        else:
            self.pet.act('jump')
            d = CountdownDialog(t['kind'])
            if d.exec():
                power(t['kind'])
            else:
                self.pet.say(f"好,这次不{KIND_CN[t['kind']]}了", 3000)

    # ---------- 截图 ----------
    def _hide_pet(self, then):
        self.pet.bubble.hide()
        self.pet.hide()
        QTimer.singleShot(260, then)

    def screenshot(self, mode):
        scr = current_screen()

        def go():
            pix = grab(scr)
            self.pet.show()
            if pix.isNull():
                return self.pet.say("没截到画面……macOS 需要在 系统设置 → 隐私与安全性 → 屏幕录制 里允许三虎", 9000)
            if mode == 'full':
                return self._save_shot(pix)
            self._picker = Picker(scr, mode, frozen=pix)
            self._picker.picked.connect(lambda rect, _t: self._save_shot(crop(pix, scr, rect)))
            self._picker.start()
        self._hide_pet(go)

    def _save_shot(self, pix):
        path = os.path.join(self.store.output_dir(), stamp_name('三虎截图', 'png'))
        pix.save(path, 'PNG')
        QGuiApplication.clipboard().setPixmap(pix)
        self.pet.act('happy')
        self.pet.say("咔嚓!截好啦,已复制到剪贴板。点我打开位置", 6000, lambda: reveal(path))

    # ---------- 录屏 ----------
    def record(self, mode):
        if self.rec.active:
            return self.pet.say("正在录着呢,点我一下结束", 3000)
        scr = current_screen()
        fps = native_fps(scr, self.store.get('record_fps'))
        r = scr.devicePixelRatio()
        d = FormatDialog(fps, (int(scr.geometry().width() * r), int(scr.geometry().height() * r)))
        if not d.exec() or not d.fmt:
            return
        fmt = d.fmt
        if mode == 'full':
            return self._start_record(scr, None, fmt, fps)
        self._picker = Picker(scr, mode, frozen=None)
        self._picker.picked.connect(lambda rect, _t: self._start_record(scr, rect, fmt, fps))
        QTimer.singleShot(200, self._picker.start)

    def _exclude_from_capture(self, on):
        """Windows:让三虎自己不出现在录像里(系统不支持时忽略)。"""
        if sys.platform != 'win32':
            return
        try:
            import ctypes
            for w in (self.pet, self.pet.bubble):
                ctypes.windll.user32.SetWindowDisplayAffinity(int(w.winId()), 0x11 if on else 0)
        except Exception:
            pass

    def _start_record(self, scr, rect, fmt, fps):
        self.pet.say("3、2、1,开拍!录完点我一下就结束", 2200)

        def go():
            self.pet.bubble.hide()
            self._exclude_from_capture(True)
            self.pet.recording = True
            self.rec.start(scr, rect, fmt, fps, self.store.output_dir())
        QTimer.singleShot(2400, go)

    def stop_record(self):
        self.pet.recording = False
        self.pet.update()
        self.pet.set_busy(True)
        self._rec_busy = True
        self.pet.say("收工!三虎正在整理录像……", 60000)
        self.rec.stop()

    def _rec_cleanup(self):
        self.pet.recording = False
        self._exclude_from_capture(False)
        if getattr(self, '_rec_busy', False):
            self._rec_busy = False
            self.pet.set_busy(False)

    def rec_done(self, path):
        self._rec_cleanup()
        self.pet.act('happy')
        self.pet.say("录好啦!点我打开位置", 8000, lambda: reveal(path))

    def rec_failed(self, msg):
        self._rec_cleanup()
        self.pet.say("录屏没成功:" + msg, 12000)

    # ---------- 文件:转换 / 压缩 / 解压 ----------
    def handle_files(self, paths):
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            return
        d = DropDialog(paths, self.sprites)
        scr = current_screen().availableGeometry()
        d.adjustSize()
        d.move(scr.center() - d.rect().center())
        if not d.exec() or not d.action:
            return
        act = d.action
        if act[0] == 'convert':
            self._convert(paths, act[1])
        elif act[0] == 'compress':
            self._job(lambda: archive.compress(paths, act[1], act[2]), "压好啦!点我打开位置", "正在打包,嘿咻嘿咻……")
        else:
            self._extract(paths, act[1])

    def _job(self, fn, ok_text, busy_text, on_fail=None):
        self.pet.set_busy(True)
        self.pet.say(busy_text, 600000)

        def ok(out):
            self.pet.set_busy(False)
            self.pet.act('happy')
            last = out[-1] if isinstance(out, list) else out
            self.pet.say(ok_text, 8000, lambda: reveal(last))

        def fail(e):
            self.pet.set_busy(False)
            self.pet.bubble.hide()
            if on_fail and on_fail(e):
                return
            self.pet.say(("三虎搞不定:" if not isinstance(e, archive.ToolMissing) else '') + str(e), 14000)
        run_async(fn, ok, fail)

    def _convert(self, paths, fmt):
        gui = [p for p in paths if convert.needs_gui_thread(p, fmt)]
        rest = [p for p in paths if p not in gui]
        outs = []
        try:
            for p in gui:       # 文字 → PDF 使用 Qt 排版,需在界面线程
                outs.append(convert.convert(p, fmt))
        except Exception as e:
            return self.pet.say("三虎搞不定:" + str(e), 10000)
        if not rest:
            self.pet.act('happy')
            return self.pet.say(f"转成 {fmt.upper()} 啦!点我打开位置", 8000, lambda: reveal(outs[-1]))
        self._job(lambda: outs + [convert.convert(p, fmt) for p in rest],
                  f"转成 {fmt.upper()} 啦!点我打开位置", f"正在转成 {fmt.upper()},嚼嚼嚼……")

    def _extract(self, paths, pw):
        def on_fail(e):
            if isinstance(e, archive.NeedPassword):
                text, ok = QInputDialog.getText(None, '需要密码', '这个压缩包有密码(或密码不对),请输入:', QLineEdit.Password)
                if ok and text:
                    self._extract(paths, text)
                return True
            return False
        self._job(lambda: [archive.extract(p, pw or None) for p in paths], "解压好啦!点我打开位置", "正在拆包裹……", on_fail)


def main():
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    qapp = QApplication(sys.argv)
    qapp.setApplicationName('Sanhuu')
    qapp.setApplicationDisplayName(APP_NAME)
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setWindowIcon(QIcon(resource('assets', 'icon.png')))
    qapp.setStyle('Fusion')
    qapp.setStyleSheet(theme.QSS)
    lock = QLockFile(os.path.join(data_dir(), 'sanhuu.lock'))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, APP_NAME, '三虎已经在桌面上啦(看看屏幕右下角,或系统托盘)。')
        return 0
    app = App(qapp)
    app.start()
    code = qapp.exec()
    lock.unlock()
    return code
