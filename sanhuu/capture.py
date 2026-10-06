# -*- coding: utf-8 -*-
"""截图与录屏。
截图:Qt 原生抓屏(物理像素,不缩放)。
录屏:FFmpeg 直接抓取桌面,分辨率 = 屏幕物理像素,帧率 = 显示器刷新率(可在设置里改)。"""
import os, sys, time, subprocess, tempfile
from datetime import datetime
from PySide6.QtCore import Qt, QRect, QPoint, QTimer, Signal, QObject, QProcess
from PySide6.QtGui import QPainter, QColor, QPen, QGuiApplication, QCursor, QFont
from PySide6.QtWidgets import QWidget
from . import theme
from .winlist import list_windows, window_at, logical_to_phys
from .convert import ffmpeg_exe
from .paths import no_window_kwargs


def stamp_name(prefix, ext):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"


def current_screen():
    return QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()


def grab(screen):
    return screen.grabWindow(0)


def crop(pix, screen, rect):
    """从整屏截图里裁出逻辑矩形 rect(全局坐标)。"""
    x, y, w, h = logical_to_phys(screen, rect)
    return pix.copy(QRect(x, y, w, h))


class Picker(QWidget):
    """全屏选择层。mode='window':鼠标移到窗口上出现高亮待选框,点击确认;
    mode='region':拖出一个矩形。frozen 为整屏截图时显示冻结画面(截图用),否则为半透明实时层(录屏用)。"""
    picked = Signal(QRect, str)
    cancelled = Signal()

    def __init__(self, screen, mode='window', frozen=None):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.screen_, self.mode, self.frozen = screen, mode, frozen
        if frozen is None:
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(screen.geometry())
        self.windows = list_windows() if mode == 'window' else []
        if mode == 'window' and not self.windows:
            self.mode = 'region'      # 拿不到窗口列表(例如权限未开)时退回框选
        self.hot = None
        self.origin = None
        self.sel = QRect()

    def start(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self._hover(QCursor.pos())

    def _hover(self, gp):
        if self.mode == 'window':
            hit = window_at(self.windows, gp)
            self.hot = (hit[0], hit[1].intersected(self.screen_.geometry())) if hit else None
            self.update()

    def mouseMoveEvent(self, e):
        gp = e.globalPosition().toPoint()
        if self.mode == 'window':
            self._hover(gp)
        elif self.origin is not None:
            self.sel = QRect(self.origin, gp).normalized()
            self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            return self._cancel()
        if self.mode == 'region':
            self.origin = e.globalPosition().toPoint()
            self.sel = QRect(self.origin, self.origin)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.mode == 'window':
            if self.hot:
                title, rect = self.hot
                self.close()
                self.picked.emit(rect, title)
        elif self.origin is not None:
            rect = self.sel.intersected(self.screen_.geometry())
            self.origin = None
            if rect.width() > 8 and rect.height() > 8:
                self.close()
                self.picked.emit(rect, '区域')

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._cancel()

    def _cancel(self):
        self.close()
        self.cancelled.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        if self.frozen is not None:
            p.drawPixmap(self.rect(), self.frozen)
        p.fillRect(self.rect(), QColor(20, 22, 30, 110))
        off = self.screen_.geometry().topLeft()
        hi = None
        label = ''
        if self.mode == 'window' and self.hot:
            hi, label = self.hot[1].translated(-off), self.hot[0]
        elif self.mode == 'region' and not self.sel.isNull():
            hi = self.sel.translated(-off)
            r = self.screen_.devicePixelRatio()
            label = f"{int(self.sel.width() * r)} × {int(self.sel.height() * r)}"
        if hi is not None:
            if self.frozen is not None:
                r = self.screen_.devicePixelRatio()
                p.drawPixmap(hi, self.frozen, QRect(int(hi.x() * r), int(hi.y() * r), int(hi.width() * r), int(hi.height() * r)))
            else:
                p.setCompositionMode(QPainter.CompositionMode_Source)
                p.fillRect(hi, QColor(0, 0, 0, 1))
                p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(QColor(theme.ACCENT), 3))
            p.setBrush(Qt.NoBrush)
            p.drawRect(hi.adjusted(1, 1, -2, -2))
            f = QFont()
            f.setPointSize(11)
            f.setBold(True)
            p.setFont(f)
            text = label if len(label) < 40 else label[:38] + '…'
            tw = p.fontMetrics().horizontalAdvance(text) + 20
            ty = hi.y() - 30 if hi.y() > 34 else hi.y() + 6
            tag = QRect(hi.x() + 4, ty, tw, 24)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.ACCENT))
            p.drawRoundedRect(tag, 8, 8)
            p.setPen(QColor('#FFFFFF'))
            p.drawText(tag, Qt.AlignCenter, text)
        hint = "移动鼠标选择窗口,单击确认 · Esc 取消" if self.mode == 'window' else "按住拖出一个区域 · Esc 取消"
        f = QFont()
        f.setPointSize(12)
        p.setFont(f)
        tw = p.fontMetrics().horizontalAdvance(hint) + 36
        box = QRect((self.width() - tw) // 2, 28, tw, 36)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(43, 45, 54, 230))
        p.drawRoundedRect(box, 18, 18)
        p.setPen(QColor('#FFFFFF'))
        p.drawText(box, Qt.AlignCenter, hint)


def native_fps(screen, setting='native'):
    if setting in ('30', '60', 30, 60):
        return int(setting)
    r = int(round(screen.refreshRate() or 60))
    return max(24, min(r, 240))


def _mac_screen_device(index):
    """解析 FFmpeg avfoundation 设备列表,找到第 index 块屏幕对应的设备号。"""
    p = subprocess.run([ffmpeg_exe(), '-hide_banner', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                       capture_output=True)
    ids = []
    for line in p.stderr.decode('utf-8', 'ignore').splitlines():
        if 'Capture screen' in line and '[' in line:
            try:
                ids.append(int(line.split('] [')[1].split(']')[0]))
            except Exception:
                pass
    if not ids:
        raise RuntimeError('没有找到可录制的屏幕。请在"系统设置 → 隐私与安全性 → 屏幕录制"里允许三虎。')
    return ids[min(index, len(ids) - 1)]


class Recorder(QObject):
    """FFmpeg 录屏。start() 开始,stop() 结束;finished(path) / failed(msg)。"""
    finished = Signal(str)
    failed = Signal(str)
    started = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proc = None
        self.active = False
        self._stopping = False
        self._attempt = 0
        self._t0 = 0

    def start(self, screen, rect, fmt, fps, out_dir):
        """rect: 逻辑坐标 QRect(全局)或 None(整屏)。fmt: 'mp4' / 'gif'。"""
        self.screen, self.rect, self.fmt, self.fps, self.out_dir = screen, rect, fmt, fps, out_dir
        self._attempt = 0
        self._launch()

    def _input_args(self):
        scr, fps = self.screen, self.fps
        g, r = scr.geometry(), scr.devicePixelRatio()
        full = (0, 0, int(round(g.width() * r)), int(round(g.height() * r)))
        x, y, w, h = logical_to_phys(scr, self.rect) if self.rect else full
        w -= w % 2
        h -= h % 2
        vf = []
        if sys.platform == 'win32':
            primary = scr == QGuiApplication.primaryScreen()
            if self._attempt == 0 and primary:
                # 桌面复制 API(DXGI),高分屏高刷新率下也能跟上原生帧率
                src = f"ddagrab=output_idx=0:framerate={fps}:draw_mouse=1"
                if self.rect:
                    src += f":offset_x={x}:offset_y={y}:video_size={w}x{h}"
                args = ['-f', 'lavfi', '-i', src]
                vf = ['hwdownload', 'format=bgra']
            else:
                args = ['-f', 'gdigrab', '-framerate', str(fps), '-draw_mouse', '1',
                        '-offset_x', str(g.x() + x), '-offset_y', str(g.y() + y), '-video_size', f'{w}x{h}', '-i', 'desktop']
        elif sys.platform == 'darwin':
            fps = min(fps, 60)       # macOS 的屏幕采集接口上限为 60 帧
            self.fps = fps
            idx = QGuiApplication.screens().index(scr)
            dev = _mac_screen_device(idx)
            args = ['-f', 'avfoundation', '-framerate', str(fps), '-capture_cursor', '1', '-pixel_format', 'nv12',
                    '-i', f'{dev}:none']
            if self.rect:
                vf = [f'crop={w}:{h}:{x}:{y}']
        else:
            disp = os.environ.get('DISPLAY', ':0')
            args = ['-f', 'x11grab', '-framerate', str(fps), '-video_size', f'{w}x{h}', '-i', f'{disp}+{g.x() + x},{g.y() + y}']
        if w % 2 or h % 2 or not self.rect:
            vf.append('crop=trunc(iw/2)*2:trunc(ih/2)*2')
        return args, vf

    def _launch(self):
        try:
            args, vf = self._input_args()
        except Exception as e:
            self.failed.emit(str(e))
            return
        os.makedirs(self.out_dir, exist_ok=True)
        if self.fmt == 'gif':
            self.tmp = os.path.join(tempfile.gettempdir(), stamp_name('sanhuu_rec', 'mkv'))
            enc = ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '8', '-pix_fmt', 'yuv444p']
            target = self.tmp
        else:
            self.tmp = None
            enc = ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
            target = os.path.join(self.out_dir, stamp_name('三虎录屏', 'mp4'))
        self.out = target if self.fmt != 'gif' else os.path.join(self.out_dir, stamp_name('三虎录屏', 'gif'))
        cmd = ['-y', '-hide_banner', '-loglevel', 'error'] + args + (['-vf', ','.join(vf)] if vf else []) + enc + [target]
        self.proc = QProcess(self)
        self.proc.finished.connect(self._done)
        self.proc.errorOccurred.connect(lambda _e: None)
        self._stopping = False
        self._t0 = time.time()
        self.proc.start(ffmpeg_exe(), cmd)
        self.active = True
        self.started.emit()

    def stop(self):
        if not self.proc or self._stopping:
            return
        self._stopping = True
        self.proc.write(b'q\n')
        self.proc.closeWriteChannel()
        QTimer.singleShot(8000, lambda p=self.proc: p.kill() if p.state() != QProcess.NotRunning else None)

    def _done(self, code, _status):
        err = bytes(self.proc.readAllStandardError()).decode('utf-8', 'ignore')
        if not self._stopping:
            # 进程自己退出了:Windows 上先从 ddagrab 回退到 gdigrab 再试一次
            if sys.platform == 'win32' and self._attempt == 0 and time.time() - self._t0 < 4:
                self._attempt = 1
                return self._launch()
            self.active = False
            msg = err.strip()[-240:] or '录屏进程意外退出'
            if sys.platform == 'darwin':
                msg += '\n请确认已在"系统设置 → 隐私与安全性 → 屏幕录制"中允许三虎。'
            return self.failed.emit(msg)
        self.active = False
        src = self.tmp or self.out
        if not os.path.exists(src) or os.path.getsize(src) < 1024:
            return self.failed.emit('没有录到画面。' + err.strip()[-200:])
        if self.fmt != 'gif':
            return self.finished.emit(self.out)
        # GIF:原分辨率 + 全局调色板。GIF 的帧间隔以 1/100 秒为单位,故帧率最高 50。
        gfps = min(self.fps, 50)
        vf = (f"fps={gfps},split[a][b];[a]palettegen=stats_mode=diff[p];"
              f"[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle")
        from .jobs import run_async

        def work():
            p = subprocess.run([ffmpeg_exe(), '-y', '-hide_banner', '-loglevel', 'error', '-i', self.tmp, '-vf', vf,
                                '-loop', '0', self.out], capture_output=True, **no_window_kwargs())
            try:
                os.remove(self.tmp)
            except OSError:
                pass
            if p.returncode != 0:
                raise RuntimeError(p.stderr.decode('utf-8', 'ignore')[-200:])
            return self.out
        run_async(work, self.finished.emit, self.failed.emit)
