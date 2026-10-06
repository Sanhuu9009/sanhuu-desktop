# -*- coding: utf-8 -*-
"""后台任务:在线程池里跑耗时函数,结果通过信号回到界面线程。"""
import traceback
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class _Sig(QObject):
    done = Signal(object)
    fail = Signal(object)


class _Run(QRunnable):
    def __init__(self, fn, args, kw):
        super().__init__()
        self.fn, self.args, self.kw, self.sig = fn, args, kw, _Sig()

    def run(self):
        try:
            self.sig.done.emit(self.fn(*self.args, **self.kw))
        except Exception as e:  # noqa
            traceback.print_exc()
            self.sig.fail.emit(e)


_keep = set()


def run_async(fn, on_done=None, on_fail=None, *args, **kw):
    r = _Run(fn, args, kw)
    _keep.add(r.sig)

    def fin(*_):
        _keep.discard(r.sig)
    if on_done:
        r.sig.done.connect(on_done)
    if on_fail:
        r.sig.fail.connect(on_fail)
    r.sig.done.connect(fin)
    r.sig.fail.connect(fin)
    QThreadPool.globalInstance().start(r)
    return r
