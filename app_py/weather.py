# -*- coding: utf-8 -*-
"""天气（Open-Meteo）+ 下雨预警"""
import json
import threading
import time
import urllib.request


def get_weather(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&current=temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m"
           f"&hourly=precipitation_probability&forecast_hours=8&timezone=auto")
    with urllib.request.urlopen(url, timeout=8) as r:
        d = json.load(r)
    cur = d.get("current", {})
    codes = {0: "晴", 1: "大致晴朗", 2: "多云", 3: "阴", 45: "雾", 48: "雾凇", 51: "毛毛雨",
             53: "毛毛雨", 55: "毛毛雨", 61: "小雨", 63: "中雨", 65: "大雨", 66: "冻雨",
             67: "冻雨", 71: "小雪", 73: "中雪", 75: "大雪", 80: "阵雨", 81: "阵雨",
             82: "强阵雨", 85: "阵雪", 86: "阵雪", 95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "雷暴"}
    code = cur.get("weather_code", 0)
    precip = d.get("hourly", {}).get("precipitation_probability", [])
    rain_soon = any(p >= 40 for p in precip[:3])
    return {
        "temp": cur.get("temperature_2m"),
        "code": code,
        "desc": codes.get(code, "未知"),
        "humidity": cur.get("relative_humidity_2m"),
        "wind": cur.get("wind_speed_10m"),
        "rain_soon": rain_soon,
    }


def locate_ip():
    try:
        with urllib.request.urlopen("https://ipapi.co/json/", timeout=6) as r:
            d = json.load(r)
            return d.get("latitude"), d.get("longitude"), d.get("city", "")
    except Exception:
        return None, None, None


class RainWatcher:
    """每 30 分钟查一次天气；未来 3 小时有雨 → 桌宠播放下雨动画提醒"""

    def __init__(self, app):
        self.app = app
        self.cooldown = 0

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            try:
                self.check()
            except Exception as e:
                print("weather check fail", e)
            time.sleep(1800)

    def check(self):
        lat, lon, city = locate_ip()
        if lat is None:
            return
        w = get_weather(lat, lon)
        if w["rain_soon"] and time.time() > self.cooldown:
            self.cooldown = time.time() + 4 * 3600
            self.app.pet.trigger_rain_alert(f"{city or '本地'} 3 小时内要下雨，记得带伞~")
