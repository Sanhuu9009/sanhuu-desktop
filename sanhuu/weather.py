# -*- coding: utf-8 -*-
"""天气服务:使用 Open-Meteo 开放接口(免费、无需密钥)。"""
import json, time, urllib.parse, urllib.request
from datetime import datetime
from PySide6.QtCore import QObject, QTimer, Signal
from .jobs import run_async

UA = {'User-Agent': 'SanhuuPet/1.0'}
WET = ('rain', 'snow', 'thunder')
KIND_CN = {'sunny': '晴', 'cloudy': '多云', 'rain': '雨', 'snow': '雪', 'thunder': '雷雨', 'wind': '大风'}
CODE_CN = {0: '晴朗', 1: '大致晴朗', 2: '局部多云', 3: '阴天', 45: '有雾', 48: '雾凇', 51: '小毛毛雨', 53: '毛毛雨',
           55: '浓毛毛雨', 56: '冻毛毛雨', 57: '冻毛毛雨', 61: '小雨', 63: '中雨', 65: '大雨', 66: '冻雨', 67: '冻雨',
           71: '小雪', 73: '中雪', 75: '大雪', 77: '米雪', 80: '阵雨', 81: '较强阵雨', 82: '强阵雨', 85: '阵雪',
           86: '强阵雪', 95: '雷雨', 96: '雷雨伴冰雹', 99: '强雷雨伴冰雹'}


def kind_of(code, wind=0.0):
    if code in (95, 96, 99):
        return 'thunder'
    if code in (71, 73, 75, 77, 85, 86):
        return 'snow'
    if 51 <= code <= 67 or code in (80, 81, 82):
        return 'rain'
    if wind >= 39:
        return 'wind'
    if code in (0, 1):
        return 'sunny'
    return 'cloudy'


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=12) as r:
        return json.loads(r.read().decode('utf-8'))


def search_city(name):
    q = urllib.parse.urlencode({'name': name, 'count': 8, 'language': 'zh', 'format': 'json'})
    res = _get('https://geocoding-api.open-meteo.com/v1/search?' + q).get('results') or []
    return [dict(name=r.get('name', ''), admin=r.get('admin1', '') or '', country=r.get('country', '') or '',
                 lat=r['latitude'], lon=r['longitude']) for r in res]


def fetch(city):
    q = urllib.parse.urlencode({
        'latitude': city['lat'], 'longitude': city['lon'], 'timezone': 'auto', 'forecast_days': 2,
        'current': 'temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m',
        'hourly': 'temperature_2m,weather_code,precipitation_probability,wind_speed_10m',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max'})
    return parse(_get('https://api.open-meteo.com/v1/forecast?' + q))


def parse(raw):
    cur = raw['current']
    code = int(cur['weather_code'])
    wind = float(cur.get('wind_speed_10m') or 0)
    out = dict(temp=cur['temperature_2m'], feels=cur.get('apparent_temperature'), hum=cur.get('relative_humidity_2m'),
               wind=wind, code=code, desc=CODE_CN.get(code, '未知'), kind=kind_of(code, wind), hours=[], days=[],
               fetched=time.time())
    h = raw.get('hourly', {})
    now = cur.get('time', '')[:13]
    times = h.get('time', [])
    start = next((i for i, t in enumerate(times) if t[:13] >= now), 0)
    for i in range(start, min(start + 12, len(times))):
        c = int(h['weather_code'][i])
        out['hours'].append(dict(time=times[i][11:16], temp=h['temperature_2m'][i], code=c,
                                 kind=kind_of(c, float((h.get('wind_speed_10m') or [0] * len(times))[i] or 0)),
                                 pop=(h.get('precipitation_probability') or [None] * len(times))[i]))
    d = raw.get('daily', {})
    for i, t in enumerate(d.get('time', [])):
        c = int(d['weather_code'][i])
        out['days'].append(dict(date=t, code=c, desc=CODE_CN.get(c, ''), tmax=d['temperature_2m_max'][i],
                                tmin=d['temperature_2m_min'][i], pop=(d.get('precipitation_probability_max') or [None] * 9)[i]))
    return out


def upcoming_change(w, hours=3):
    """未来几小时是否要变天:返回 (kind, 几小时后, 文案) 或 None。"""
    cur = w['kind']
    for i, h in enumerate(w['hours'][1:hours + 1], start=1):
        k = h['kind']
        wet_soon = k in WET or (h.get('pop') or 0) >= 70
        if wet_soon and cur not in WET:
            k = k if k in WET else 'rain'
            what = {'rain': '下雨', 'snow': '下雪', 'thunder': '打雷下雨'}[k]
            tip = '出门记得带伞!' if k != 'snow' else '多穿一点哦!'
            return k, i, f"大约 {i} 小时后要{what}啦({h['time']} 前后),{tip}"
        if k == 'wind' and cur != 'wind':
            return 'wind', i, f"大约 {i} 小时后会起大风({h['time']} 前后),东西收好~"
    return None


def describe(w, city):
    feels = f",体感 {round(w['feels'])}°" if w.get('feels') is not None else ''
    s = f"{city['name']}现在{w['desc']},{round(w['temp'])}°C{feels}"
    if w['days']:
        d = w['days'][0]
        s += f"。今天 {round(d['tmin'])}° ~ {round(d['tmax'])}°"
        if d.get('pop') is not None:
            s += f",降水概率 {d['pop']}%"
    return s


class WeatherService(QObject):
    updated = Signal(dict)          # 新数据
    changed = Signal(str, str)      # 天气类型变了 (kind, 文案)
    alert = Signal(str, str)        # 即将变天 (kind, 文案)
    failed = Signal(str)

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.data = None
        self._last_kind = None
        self._alerted = {}
        self.timer = QTimer(self, interval=20 * 60 * 1000, timeout=self.refresh)
        self.timer.start()

    def refresh(self):
        city = self.store.get('city')
        if not city:
            return
        run_async(fetch, self._ok, lambda e: self.failed.emit(str(e)), city)

    def _ok(self, w):
        city = self.store.get('city')
        self.data = w
        self.updated.emit(w)
        if w['kind'] != self._last_kind:
            first = self._last_kind is None
            self._last_kind = w['kind']
            self.changed.emit(w['kind'], describe(w, city) if first else f"变天啦:现在是{w['desc']},{round(w['temp'])}°C")
            return
        up = upcoming_change(w)
        if up:
            kind, _, text = up
            if time.time() - self._alerted.get(kind, 0) > 2 * 3600:
                self._alerted[kind] = time.time()
                self.alert.emit(kind, text)
