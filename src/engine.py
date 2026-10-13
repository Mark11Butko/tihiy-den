"""Движок виджета «Тихий день» v3: данные -> форматирование -> файлы для Rainmeter, обработка кликов.

  engine.py refresh [--force]   получить устаревшие данные и перерисовать (планировщик, раз в минуту)
  engine.py render              перерисовать из кэша
  engine.py act <действие> [аргумент]
"""
import calendar as pycal
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import google as gcal
import markets
from i18n import LANG, tr
from td_common import CFG, COLORS, DATA, RAINMETER, NC, NE, NF, NT, chunks, geo_keys, hex_rgba, load_config, save_config, text_keys
from td_layout import CW, RH, S, SPARK_H, SPARK_W, TILE_SPARK_H, TILE_SPARK_W

CACHE = os.path.join(DATA, "cache.json")
STATE = os.path.join(DATA, "state.json")
DEMO = os.environ.get("TD_DEMO") == "1" or bool(CFG.get("demo"))

DEFAULT_STATE = {"mode": "expanded", "chartOpen": False, "chart": "1:0", "period": "7d", "month": None, "year": None, "selected": None}
CBR_CODES = markets.CBR_CODES
WEEKDAYS, WD_SHORT, MONTHS, MONTHS_GEN, COMPASS = tr("weekdays"), tr("wd_short"), tr("months"), tr("months_gen"), tr("compass")
CONFIG = os.path.join(DATA, "config.json")
NBSP = " "
MINUS = "−"
EN = "–"


# ---------------------------------------------------------------- файлы
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return json.loads(json.dumps(default))


LOCK = os.path.join(DATA, "state.lock")


class state_lock:
    """Простой файловый замок: клики запускают отдельные процессы engine.py, они не должны затирать state.json друг у друга."""

    def __enter__(self):
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.time() - t0 > 5:  # замок завис (процесс убит) — снимаем
                    try:
                        os.remove(LOCK)
                    except OSError:
                        pass
                time.sleep(0.03)
            except OSError:
                time.sleep(0.03)

    def __exit__(self, *a):
        try:
            os.close(self.fd)
            os.remove(LOCK)
        except OSError:
            pass


def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "TihiyDen/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------- данные
def weather_icon(code):
    c = int(code)
    if c == 0:
        return "clear"
    if c in (1, 2):
        return "partly"
    if c == 3:
        return "cloud"
    if c in (45, 48):
        return "fog"
    if 51 <= c <= 67 or 80 <= c <= 82:
        return "rain"
    if 71 <= c <= 77 or c in (85, 86):
        return "snow"
    if c >= 95:
        return "storm"
    return "cloud"


def fetch_weather_openmeteo(cfg):
    q = {
        "latitude": cfg["lat"], "longitude": cfg["lon"], "timezone": "auto", "forecast_days": 6, "wind_speed_unit": "ms",
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
        "hourly": "temperature_2m,weather_code,precipitation_probability",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
    }
    j = json.loads(get("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(q)))
    cur = j["current"]
    now_h = cur["time"][:13]
    times = j["hourly"]["time"]
    idx = next((i for i, t in enumerate(times) if t[:13] >= now_h), 0)
    hourly = [{"time": times[i], "temp": j["hourly"]["temperature_2m"][i], "icon": weather_icon(j["hourly"]["weather_code"][i])}
              for i in range(idx + 1, idx + 7)]
    daily = [{"date": j["daily"]["time"][i], "min": j["daily"]["temperature_2m_min"][i], "max": j["daily"]["temperature_2m_max"][i],
              "icon": weather_icon(j["daily"]["weather_code"][i])} for i in range(5)]
    return {"t": time.time(), "temp": cur["temperature_2m"], "feels": cur["apparent_temperature"], "icon": weather_icon(cur["weather_code"]),
            "wind": cur["wind_speed_10m"], "dir": cur.get("wind_direction_10m"), "hum": cur.get("relative_humidity_2m"),
            "hourly": hourly, "daily": daily}


def metno_icon(code):
    c = code.split("_")[0]
    for key, icon in (("thunder", "storm"), ("snow", "snow"), ("sleet", "snow"), ("rain", "rain"), ("shower", "rain"), ("fog", "fog"),
                      ("partlycloudy", "partly"), ("fair", "partly"), ("cloudy", "cloud"), ("clearsky", "clear")):
        if key in c:
            return icon
    return "cloud"


def fetch_weather_metno(cfg):
    """Запасной источник: Норвежский метеоинститут (api.met.no), тоже без ключа."""
    from zoneinfo import ZoneInfo
    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=%.4f&lon=%.4f" % (cfg["lat"], cfg["lon"])
    req = urllib.request.Request(url, headers={"User-Agent": "TihiyDen/1.1 github.com/Mark11Butko/tihiy-den"})
    with urllib.request.urlopen(req, timeout=15) as r:
        ts = json.loads(r.read())["properties"]["timeseries"]
    try:
        tz = ZoneInfo(cfg["tz"]) if cfg.get("tz") else None
    except Exception:
        tz = None
    rows = []
    for e in ts:
        t = dt.datetime.fromisoformat(e["time"].replace("Z", "+00:00")).astimezone(tz)
        d = e["data"]
        sym = ((d.get("next_1_hours") or d.get("next_6_hours") or d.get("next_12_hours") or {}).get("summary") or {}).get("symbol_code", "cloudy")
        rows.append((t, d["instant"]["details"], metno_icon(sym)))
    now = rows[0]
    cur = now[1]
    hourly = [{"time": r[0].strftime("%Y-%m-%dT%H:%M"), "temp": r[1]["air_temperature"], "icon": r[2]} for r in rows[1:7]]
    days = {}
    for t, det, icon in rows:
        days.setdefault(t.date(), []).append((t, det["air_temperature"], icon))
    daily = []
    for day in sorted(days)[:5]:
        vals = days[day]
        mid = min(vals, key=lambda v: abs(v[0].hour - 13))
        daily.append({"date": day.isoformat(), "min": min(v[1] for v in vals), "max": max(v[1] for v in vals), "icon": mid[2]})
    wind = cur.get("wind_speed", 0)
    return {"t": time.time(), "temp": cur["air_temperature"], "feels": cur["air_temperature"], "icon": now[2], "wind": wind,
            "dir": cur.get("wind_from_direction"), "hum": cur.get("relative_humidity"), "hourly": hourly, "daily": daily, "src": "met.no"}


def fetch_weather(cfg):
    """Open-Meteo, а если он не отвечает — met.no: виджет не остаётся без погоды."""
    try:
        w = fetch_weather_openmeteo(cfg)
        w["src"] = "open-meteo"
        return w
    except Exception as first:
        try:
            return fetch_weather_metno(cfg)
        except Exception:
            raise first


def geocode(query, lang):
    """Город по названию (Open-Meteo Geocoding): 'Вена', 'Paris, US'. Возвращает dict или None."""
    name, _, country = query.partition(",")
    j = json.loads(get("https://geocoding-api.open-meteo.com/v1/search?count=10&language=%s&name=%s" % (lang, urllib.parse.quote(name.strip()))))
    res = j.get("results") or []
    c = country.strip().lower()
    if c:
        res = [r for r in res if c in (r.get("country_code", "").lower(), r.get("country", "").lower(), (r.get("admin1") or "").lower())] or res
    if not res:
        return None
    r = res[0]
    return {"label": r["name"], "lat": r["latitude"], "lon": r["longitude"], "tz": r.get("timezone"), "country": r.get("country", "")}


def refresh_data(force=False):
    cfg = load_config()
    cache = load_json(CACHE, {})
    now = time.time()
    online = True

    def due(key, every):
        return force or key not in cache or now - cache[key].get("t", 0) >= every

    try:
        if due("weather", cfg["weather_every"]):
            cache["weather"] = fetch_weather(cfg)
    except Exception as e:
        online = False
        cache["err_weather"] = str(e)[:100]
    try:
        items = cache.setdefault("items", {})
        errs = markets.refresh(cfg, items, force=force, now=now)
        cache["err_items"] = errs
        if errs and all(k.startswith(("coin", "coins")) for k in errs):
            online = False
    except Exception as e:
        cache["err_items"] = {"all": str(e)[:100]}
    try:
        gcal.sync(force=force)
    except Exception as e:
        cache["err_google"] = str(e)[:100]
    cache["online"] = online
    cache["checked"] = now
    save_json(CACHE, cache)
    return cache


# ---------------------------------------------------------------- форматирование
def fmt_temp(v):
    if v is None:
        return "—"
    n = int(round(v))
    if n > 0:
        return "+%d°" % n
    if n < 0:
        return "%s%d°" % (MINUS, abs(n))
    return "0°"


def dec(text):
    """Десятичный разделитель по языку: запятая для ru, точка для en."""
    return text.replace(".", ",") if LANG == "ru" else text


def usd(text):
    """Подпись доллара: «1 234 $» (ru) / «$1,234» (en)."""
    return text + " $" if LANG == "ru" else "$" + text


def fmt_rate(v):
    if v is None:
        return "—"
    return dec("%.2f" % v) if v >= 1 else dec("%.4g" % v)


def fmt_price(p):
    if p is None:
        return "—"
    if p >= 1000:
        n = f"{int(round(p)):,}"
        return n.replace(",", NBSP) if LANG == "ru" else n
    if p >= 1:
        return dec("%.2f" % p)
    return dec("%.6g" % p)


def fmt_change(pct):
    if pct is None:
        return "—"
    if round(pct, 2) > 0:
        return dec("▲ +%.2f%%" % pct)
    if round(pct, 2) < 0:
        return dec("▼ %s%.2f%%" % (MINUS, abs(pct)))
    return dec("→ 0.00%")


def trend_hex(pct):
    if pct is None or round(pct, 2) == 0:
        return COLORS["textDim"]
    return COLORS["up"] if pct > 0 else COLORS["down"]


def rgba(name, mul=1.0):
    return hex_rgba(COLORS[name], mul)


def spark_paths(series, w, h, inset=2):
    """(линия, область) — пути Rainmeter для блока w×h дизайн-пикселей (масштабируются на SCALE)."""
    if not series:
        z = "%s,%s | LineTo %s,%s" % (S(0), S(0), S(0), S(0))
        return z, z + " | ClosePath 1"
    x0, x1, y0, y1 = inset, w - inset, inset, h - inset
    mn, mx = min(series), max(series)
    n = len(series)
    pts = []
    for i, v in enumerate(series):
        x = (x0 + x1) / 2 if n == 1 else x0 + (x1 - x0) * i / (n - 1)
        y = (y0 + y1) / 2 if mx == mn else y1 - (y1 - y0) * (v - mn) / (mx - mn)
        pts.append((S(x), S(y)))
    if n == 1:
        pts.append((pts[0][0] + 0.1, pts[0][1]))
    line = " | LineTo ".join("%s,%s" % p for p in pts)
    area = line + " | LineTo %s,%s | LineTo %s,%s | ClosePath 1" % (pts[-1][0], S(y1), pts[0][0], S(y1))
    return line, area


def hour_label(hhmm, cfg):
    if cfg.get("clock24", True):
        return hhmm
    h, m = int(hhmm[:2]), hhmm[3:]
    return "%d%s %s" % (h % 12 or 12, "" if m == "00" else ":" + m, "AM" if h < 12 else "PM")


def flag_name(sym):
    if sym.lower() in ("usd", "eur", "pln", "czk", "uah", "gbp"):
        return "f_" + sym.lower()
    try:
        from build_icons import ensure_badge
        return ensure_badge("f", sym)
    except Exception:
        return "f_other"


def coin_name(sym):
    if sym.lower() in ("btc", "eth", "ton"):
        return "c_" + sym.lower()
    try:
        from build_icons import ensure_badge
        return ensure_badge("c", sym)
    except Exception:
        return "c_other"


def item_icon(it):
    if it["k"] == "fx":
        return flag_name(it["s"])
    if it["k"] == "coin":
        return coin_name(it["s"])
    try:
        from build_icons import ensure_badge
        return ensure_badge("y", it["s"])
    except Exception:
        return "c_other"


def money(price, cur):
    """Цена с валютой: «83 094 $» (ru) / «$83,094» (en); для евро, фунтов и прочего — свой знак."""
    if price is None:
        return "—"
    t = fmt_price(price)
    if cur == "USD":
        return usd(t)
    sym = markets.CUR_SYMBOL.get(cur)
    if sym in ("€", "£", "¥") and LANG == "en":
        return sym + t
    return "%s %s" % (t, sym or cur)


def item_label(it, base):
    return "%s/%s" % (it["s"], base) if it["k"] == "fx" else it["s"]


def item_text(it, d, base):
    """(метка, цена, изменение) строки списка; пустая цена — «—», если данных пока нет."""
    label = item_label(it, base)
    if not d:
        return label, "—", ""
    price = fmt_rate(d["price"]) if it["k"] == "fx" else money(d["price"], d.get("cur", "USD"))
    return label, price, fmt_change(d["chg"])


def item_series(d, period=None):
    """Ряд для графика: запрошенный период, а если его нет у этого актива — лучший из имеющихся."""
    if not d:
        return None
    order = {"24h": ("s24", "s7", "s30"), "7d": ("s7", "s30", "s24"), "30d": ("s30", "s7", "s24")}.get(period or "7d", ("s7", "s30", "s24"))
    for k in order:
        if d.get(k):
            return d[k]
    return None


def titles(cfg):
    t = cfg.get("titles") or [None, None]
    return (t[0] or tr("ui_markets1"), (t[1] or tr("ui_markets2")) if len(t) > 1 else tr("ui_markets2"))


def countdown(start_iso, end_iso, now):
    try:
        st = dt.datetime.fromisoformat(start_iso)
    except Exception:
        return ""
    if st > now:
        m = int((st - now).total_seconds() // 60)
        h, mm = divmod(m, 60)
        if h:
            return tr("in_h") % (h, mm)
        return tr("in_m") % max(mm, 1)
    return tr("ongoing")


# ---------------------------------------------------------------- демо-данные (TD_DEMO=1) для скриншотов и проверки
def demo_cache(cfg):
    import random
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    icons = ["partly", "partly", "cloud", "cloud", "rain", "rain"]
    hourly = [{"time": (now + dt.timedelta(hours=i + 1)).strftime("%Y-%m-%dT%H:%M"), "temp": 13 + (i % 3) + (1 if i > 2 else 0), "icon": icons[i]} for i in range(6)]
    dicons = ["partly", "rain", "cloud", "partly", "clear"]
    daily = [{"date": (dt.date.today() + dt.timedelta(days=i)).isoformat(), "min": 8 - i % 3, "max": 14 + (i % 3) - 1, "icon": dicons[i]} for i in range(5)]
    weather = {"t": time.time(), "temp": 12, "feels": 10, "icon": "partly", "wind": 3.6, "dir": 315, "hum": 55, "hourly": hourly, "daily": daily}

    def series(base, n, amp, drift, phase):
        rnd = random.Random(int(phase * 10) + n)   # фиксированное зерно: скриншоты воспроизводимы
        v, out = 0.0, []
        for i in range(n):
            v += rnd.uniform(-1, 1) * amp
            out.append(base * (1 + drift * (i - n + 1) / (n - 1) + v - 0))
        shift = base / out[-1]
        return [x * shift for x in out]
    base = cfg.get("fx_base", "RUB")
    demo_fx = ({"USD": (92.45, 0.62), "EUR": (99.18, -0.31), "PLN": (23.41, 0.48), "CZK": (4.02, 0.12), "CHF": (100.8, 0.2), "GBP": (116.4, 0.3)}
               if base == "RUB" else
               {"USD": (1.0912, 0.22), "PLN": (0.2331, -0.04), "CZK": (0.0398, 0.1), "CHF": (1.04, 0.2), "GBP": (1.1836, 0.33)})
    demo_other = {"BTC": (83220, -0.07), "ETH": (2497, -1.81), "TON": (1.37, -2.86), "SOL": (105.8, -4.49), "GOLD": (4208.6, 0.43),
                  "BRENT": (104.7, -0.9), "AAPL": (231.4, 0.8), "SILVER": (52.4, 1.1), "WTI": (99.8, -0.7), "S&P 500": (6890, 0.3)}
    items = {}
    for lst in cfg["lists"]:
        for k, it in enumerate(lst):
            key = markets.item_key(it)
            if it["k"] == "fx":
                p, c = demo_fx.get(it["s"], (50.0 + 10 * k, 0.1))
                cur = base
            else:
                p, c = demo_other.get(it["s"], (100.0 + 7 * k, 0.5))
                cur = "USD"
            items[key] = {"price": p, "chg": c, "cur": cur, "s24": series(p, 24, 0.004, c / 100, k) if it["k"] != "fx" else None,
                          "s7": series(p, 56 if it["k"] != "fx" else 7, 0.012 if it["k"] != "fx" else 0.004, c / 100 * 2, k),
                          "s30": series(p, 60, 0.03, c / 100 * 4, k), "t": time.time()}
    return {"weather": weather, "items": items, "online": True}


def demo_google(y, m, sel):
    en = LANG == "en"
    titles = ["Team standup", "Design review", "Client meeting"] if en else ["Планёрка команды", "Дизайн-ревью", "Встреча с клиентом"]
    colors = ["#2F7BFFFF", "#A78BFAFF", "#4ADE80FF"]
    d = pycal.monthrange(y, m)[1]
    days = {}
    for k, day in enumerate((2, 3, 5, 9, 10, 12, 15, 16, 18, 19, 22, 25, 27)):
        if day <= d:
            days[day] = colors[: 1 + (k * 7) % 3]
    base = dt.datetime.combine(dt.date.today(), dt.time.min)
    events = []
    for k, (h1, h2) in enumerate(((10, 11), (13, 14), (16, 17))):
        st, en_ = base + dt.timedelta(hours=h1), base + dt.timedelta(hours=h2)
        events.append({"sort": "%02d:00" % h1, "time": "%02d:00 – %02d:00" % (h1, h2), "title": titles[k], "color": colors[k],
                       "start": st.isoformat(), "end": en_.isoformat()})
    tasks_ = ["Prepare the presentation", "Reply to emails", "Buy a gift"] if en else ["Подготовить презентацию", "Ответить на письма", "Купить подарок"]
    return {"connected": True, "synced": dt.datetime.now().strftime("%H:%M"), "events": events if sel == dt.date.today() else [], "days": days,
            "tasks": [{"title": tasks_[0], "done": False}, {"title": tasks_[1], "done": True}, {"title": tasks_[2], "done": False}], "err": None}


# ---------------------------------------------------------------- отрисовка в файлы
def render():
    cfg = load_config()
    state = load_json(STATE, DEFAULT_STATE)
    cache = demo_cache(cfg) if DEMO else load_json(CACHE, {})
    now = dt.datetime.now()
    today = now.date()
    T = {k: "" for k in text_keys()}
    G = {k: "" for k in geo_keys()}
    NONE_SHAPE = "Ellipse -50,-50,0.1 | Fill Color 0,0,0,0 | StrokeWidth 0"

    # --- шапка
    T["date1"] = WEEKDAYS[today.weekday()]
    T["date2"] = tr("date_full").format(d=today.day, m=MONTHS_GEN[today.month - 1], y=today.year)

    # --- погода
    w = cache.get("weather")
    T["w.loc"] = cfg.get("label", "")
    for k in ["ic.cur"] + [f"ic.h{i}" for i in range(6)] + [f"ic.d{i}" for i in range(5)]:
        G[k] = "w_none"
    if w:
        T["w.temp"] = fmt_temp(w["temp"])
        T["w.feels"] = tr("feels") % fmt_temp(w["feels"])
        d0 = w["daily"][0]
        T["w.hi"], T["w.lo"] = fmt_temp(d0["max"]), fmt_temp(d0["min"])
        compass = COMPASS[int(round((w.get("dir") or 0) / 45.0)) % 8] if w.get("dir") is not None else ""
        T["w.wind"] = ("%d %s %s" % (round(w["wind"]), tr("ms"), compass)).rstrip()
        T["w.hum"] = "%d%%" % w["hum"] if w.get("hum") is not None else "—"
        G["ic.cur"] = "w_" + w["icon"]
        for i, h in enumerate(w["hourly"][:6]):
            T[f"h{i}.l"] = hour_label(h["time"][11:16], cfg)
            T[f"h{i}.t"] = fmt_temp(h["temp"])
            G[f"ic.h{i}"] = "w_" + h["icon"]
        for i, d in enumerate(w["daily"][:5]):
            day = dt.date.fromisoformat(d["date"])
            T[f"d{i}.n"] = WD_SHORT[day.weekday()]
            T[f"d{i}.d"] = day.strftime("%d.%m")
            T[f"d{i}.h"] = fmt_temp(d["max"])
            T[f"d{i}.l"] = fmt_temp(d["min"])
            G[f"ic.d{i}"] = "w_" + d["icon"]
    else:
        T["w.temp"], T["w.wind"], T["w.feels"] = "—", "—", tr("no_weather")

    # --- календарь
    m = state.get("month") or today.month
    y = state.get("year") or today.year
    sel = dt.date.fromisoformat(state["selected"]) if state.get("selected") else today
    T["cal.title"] = tr("month_title").format(m=MONTHS[m - 1], y=y)
    first_wd, ndays = pycal.monthrange(y, m)
    prev_last = (dt.date(y, m, 1) - dt.timedelta(days=1)).day
    G["sel"] = G["today"] = NONE_SHAPE
    for i in range(42):
        day = i - first_wd + 1
        r, c = divmod(i, 7)
        if 1 <= day <= ndays:
            T[f"c{i}"] = str(day)
            G[f"cc{i}"] = rgba("text")
            d = dt.date(y, m, day)
            cx, cy = S(CW * c + CW / 2), S(RH * r + RH / 2 - 1)
            if d == today:
                G["today"] = "Ellipse %s,%s,%s | Fill Color 0,0,0,0 | StrokeWidth 1 | Stroke Color %s" % (cx, cy, S(13), rgba("accent"))
            if d == sel:
                G["sel"] = "Ellipse %s,%s,%s | Fill Color %s | StrokeWidth 0" % (cx, cy, S(13), rgba("blue"))
                G[f"cc{i}"] = rgba("text")
        else:
            T[f"c{i}"] = str(prev_last + day) if day < 1 else str(day - ndays)
            G[f"cc{i}"] = rgba("textFaint")
    try:
        google = demo_google(y, m, sel) if DEMO else gcal.view(y, m, sel)
    except Exception:
        google = {"connected": False, "events": [], "days": {}, "tasks": []}
    connected = bool(google.get("connected"))
    dots = google["days"]
    inp = state.get("input")  # task | event | fx | coin — открыто окно ввода
    toast = state.get("toast") or {}
    if toast.get("until", 0) < time.time():
        toast = {}
    if toast.get("sec") == "city":
        T["w.loc"] = toast["msg"]
    n = 0
    for day, colors in dots.items():
        i = day + first_wd - 1
        r, c = divmod(i, 7)
        cx, cy = CW * c + CW / 2, RH * r + RH - 4
        cs = colors[:3]
        for j, colr in enumerate(cs):
            if n < 60:
                dx = (j - (len(cs) - 1) / 2) * 6
                G[f"dot{n}"] = "Ellipse %s,%s,%s | Fill Color %s | StrokeWidth 0" % (S(cx + dx), S(cy), S(1.8), hex_rgba(colr))
                n += 1
    for j in range(n, 60):
        G[f"dot{j}"] = NONE_SHAPE
    online = cache.get("online", True)
    if not online:
        T["cal.sync"] = tr("offline")
    elif connected and google.get("synced"):
        T["cal.sync"] = tr("synced") % google["synced"]
    elif not connected:
        T["cal.sync"] = tr("connect_google")
    G["stale"] = rgba("warning") if not online else rgba("accent")

    # --- повестка
    events = google.get("events", [])
    tasks = google.get("tasks", [])
    typing = inp in ("task", "event")
    if typing:
        T["ag.title"] = tr("in_" + inp)
    else:
        T["ag.title"] = (tr("today_fmt") if sel == today else tr("day_fmt")).format(d=sel.day, m=MONTHS_GEN[sel.month - 1])
    if typing:
        T["ag.empty"] = tr("hint_" + inp)
    else:
        T["ag.empty"] = tr("no_events") if not events else ""
    T["in.hint"] = tr("hint_keys")
    T["fx.title"] = toast["msg"] if toast.get("sec") == "fx" else (tr("in_fx") if inp == "fx" else tr("ui_currencies"))
    T["cr.title"] = toast["msg"] if toast.get("sec") == "coin" else (tr("in_coin") if inp == "coin" else tr("ui_crypto"))
    evmap = []
    for i in range(NE):
        if i < len(events) and not typing:
            e = events[i]
            if i == NE - 1 and len(events) > NE:
                T[f"ev{i}.t"], T[f"ev{i}.n"] = "", tr("more_events") % (len(events) - NE + 1)
                G[f"col.ev{i}"] = "0,0,0,0"
                evmap.append(-1)
                continue
            T[f"ev{i}.t"] = e["time"].replace(" – ", " %s " % EN) if " – " in e["time"] else e["time"]
            T[f"ev{i}.n"] = e["title"]
            G[f"col.ev{i}"] = hex_rgba(e.get("color", COLORS["accent"]))
            evmap.append(e.get("lid", -1) if e.get("lid") is not None else -1)
        else:
            G[f"col.ev{i}"] = "0,0,0,0"
            evmap.append(-1)
    state["evmap"] = evmap
    for i in range(NT):
        has = i < len(tasks)
        done = has and tasks[i].get("done")
        T[f"tk{i}"] = tasks[i]["title"] if has else ""
        G[f"tkcol{i}"] = rgba("textFaint") if done else rgba("text")
        sz = S(16)
        if has:
            G[f"chk{i}a"] = ("Rectangle 0.5,0.5,%s,%s,%s | Fill Color %s | StrokeWidth 0" % (sz - 1, sz - 1, S(4), rgba("blue"))) if done else \
                ("Rectangle 0.5,0.5,%s,%s,%s | Fill Color 0,0,0,0 | StrokeWidth 1 | Stroke Color %s" % (sz - 1, sz - 1, S(4), rgba("textDim", 0.8)))
            G[f"chk{i}b"] = ("Path P | Fill Color 0,0,0,0 | StrokeWidth 1.6 | Stroke Color 255,255,255,255") if done else NONE_SHAPE
        else:
            G[f"chk{i}a"] = G[f"chk{i}b"] = NONE_SHAPE
    T["status"] = ""
    T["tk.empty"] = tr("no_tasks") if not tasks else ""

    # --- списки котировок (две карточки по 3 строки): валюты / золото / нефть / крипта / акции — что выбрал пользователь
    store = cache.get("items") or {}
    base = cfg.get("fx_base", "RUB")
    lists = cfg.get("lists") or [[], []]
    while len(lists) < 2:
        lists.append([])
    T["fx.title"], T["cr.title"] = titles(cfg)
    for L, (pf, kk) in enumerate((("fx", "fx"), ("cr", "c"))):
        for i in range(3):
            it = lists[L][i] if i < len(lists[L]) else None
            d = store.get(markets.item_key(it)) if it else None
            G[("fl.fx%d" if L == 0 else "lg.c%d") % i] = item_icon(it) if it else ("f_none" if L == 0 else "c_none")
            lab, pr, chg = item_text(it, d, base) if it else ("", "", "")
            if L == 0:
                T[f"fx{i}.p"], T[f"fx{i}.r"], T[f"fx{i}.c"] = lab, pr, chg
            else:
                T[f"cr{i}.s"], T[f"cr{i}.p"], T[f"cr{i}.c"] = lab, pr, chg
            ch = trend_hex(d["chg"]) if d else COLORS["textDim"]
            line, area = spark_paths(item_series(d, "7d") if d else [], SPARK_W, SPARK_H)
            G[f"sp.{kk}{i}.l" if L else f"sp.fx{i}.l"], G[f"sp.{kk}{i}.a" if L else f"sp.fx{i}.a"] = line, area
            G[f"col.{kk}{i}" if L else f"col.fx{i}"], G[f"cola.{kk}{i}" if L else f"cola.fx{i}"] = hex_rgba(ch), hex_rgba(ch, 0.14)
    # подписи окон ввода/ошибок поверх заголовков карточек
    if toast.get("sec") == "add0":
        T["fx.title"] = toast["msg"]
    elif inp == "add0":
        T["fx.title"] = tr("in_add")
    if toast.get("sec") == "add1":
        T["cr.title"] = toast["msg"]
    elif inp == "add1":
        T["cr.title"] = tr("in_add")

    # --- график (раскрытая строка списка)
    cl, cr_i = 1, 0
    try:
        cl, cr_i = (int(x) for x in str(state.get("chart", "1:0")).split(":"))
    except ValueError:
        pass
    cit = lists[cl][cr_i] if cl < len(lists) and cr_i < len(lists[cl]) else None
    d = store.get(markets.item_key(cit)) if cit else None
    per = state.get("period", "7d")
    for i, p in enumerate(("24h", "7d", "30d")):
        G[f"pc{i}"] = rgba("text") if p == per else rgba("textDim")
    G["ch.l"] = "0,0 | LineTo 0,0"
    G["ch.a"] = "0,0 | LineTo 0,0 | ClosePath 1"
    G["ch.dot"], G["ch.cury"] = NONE_SHAPE, "0"
    G["ch.col"], G["ch.cola"] = rgba("accent"), rgba("accent", 0.12)
    cprice = (lambda v: fmt_rate(v) if cit["k"] == "fx" else money(v, d.get("cur", "USD"))) if (cit and d) else None
    T["ch.title"] = "%s · %s" % (item_label(cit, base), cprice(d["price"])) if cprice else (item_label(cit, base) if cit else "")
    series = item_series(d, per)
    if d and series:
        CW_, CH_ = 344, 240
        lo, hi = min(min(series), d["price"]), max(max(series), d["price"])
        pad = (hi - lo) * 0.08 or hi * 0.01
        lo2, hi2 = lo - pad, hi + pad
        pts = []
        n_ = len(series)
        for i, v in enumerate(series):
            x = (CW_ / 2) if n_ == 1 else CW_ * i / (n_ - 1)
            yy = CH_ - (v - lo2) / (hi2 - lo2) * CH_
            pts.append((S(x), S(yy)))
        if n_ == 1:
            pts.append((pts[0][0] + 0.1, pts[0][1]))
        line = " | LineTo ".join("%s,%s" % p for p in pts)
        G["ch.l"] = line
        G["ch.a"] = line + " | LineTo %s,%s | LineTo %s,%s | ClosePath 1" % (pts[-1][0], S(CH_), pts[0][0], S(CH_))
        py = CH_ - (d["price"] - lo2) / (hi2 - lo2) * CH_
        G["ch.dot"] = "Ellipse %s,%s,%s | Fill Color %s | StrokeWidth 0" % (S(CW_ - 1), S(py), S(3.5), rgba("accent"))
        G["ch.cury"] = str(S(min(max(py - 26, 0), CH_ - 22)))
        T["ch.current"] = cprice(d["price"])
        T["ch.minmax"] = tr("minmax") % (cprice(min(series)), cprice(max(series)))
    else:
        T["ch.minmax"], T["ch.current"] = tr("no_data"), ""

    # --- компактный режим
    upcoming = []
    try:
        today_ev = events if sel == today else (demo_google if DEMO else (lambda y, m, d: gcal.view(y, m, d)))(today.year, today.month, today)["events"]
        for e in today_ev:
            if e.get("start"):
                st = dt.datetime.fromisoformat(e["start"])
                en = dt.datetime.fromisoformat(e["end"]) if e.get("end") else st
                if en >= now or st >= now:
                    upcoming.append((e["time"].replace(" – ", " %s " % EN), e["title"], countdown(e["start"], e.get("end"), now), e["color"]))
            else:
                upcoming.append((e["time"], e["title"], "", e["color"]))
        if len(upcoming) < 2:
            tm = today + dt.timedelta(days=1)
            tev = gcal.month_events(tm.year, tm.month).get(tm.day, [])
            for e in tev[:2 - len(upcoming)]:
                upcoming.append((tr("tomorrow") + " " + e["time"].split(" ")[0], e["title"], "", e["color"]))
    except Exception:
        upcoming = []
    for i in range(2):
        if i < len(upcoming):
            T[f"cp.ev{i}.t"], T[f"cp.ev{i}.n"], T[f"cp.ev{i}.in"] = upcoming[i][:3]
            G[f"cpcol.ev{i}"] = hex_rgba(upcoming[i][3])
        else:
            G[f"cpcol.ev{i}"] = "0,0,0,0"
    T["cp.empty"] = tr("no_events")
    tiles = [lists[0][0] if lists[0] else None, lists[0][1] if len(lists[0]) > 1 else None, lists[1][0] if lists[1] else None]
    for i, it in enumerate(tiles):
        d = store.get(markets.item_key(it)) if it else None
        if it and d:
            lab, pr, chg = item_text(it, d, base)
            T[f"cp.f{i}.p"], T[f"cp.f{i}.r"], T[f"cp.f{i}.c"] = lab, pr, chg
            line, area = spark_paths(item_series(d, "7d"), TILE_SPARK_W, TILE_SPARK_H)
            ch = trend_hex(d["chg"])
        else:
            line, area = spark_paths([], TILE_SPARK_W, TILE_SPARK_H)
            ch = COLORS["textDim"]
        G[f"sp.t{i}.l"], G[f"sp.t{i}.a"] = line, area
        G[f"col.t{i}"], G[f"cola.t{i}"] = hex_rgba(ch), hex_rgba(ch, 0.14)
    for i in range(3):
        G[f"fl.t{i}"] = "f_none"

    # --- видимость (1 = скрыто)
    compact = state.get("mode") == "compact"
    chart = bool(state.get("chartOpen")) and not compact
    H1 = lambda cond: "1" if cond else "0"  # noqa: E731
    G["hid.ex"] = H1(compact)
    G["hid.cal"] = H1(compact)
    G["hid.sync"] = H1(compact)
    G["hid.ag"] = H1(compact or chart)
    G["hid.go"] = "1"
    G["hid.lists"] = H1(compact or chart)
    G["hid.ch"] = H1(not chart)
    G["hid.k"] = H1(not compact)
    G["hid.kev"] = H1(not (compact and upcoming))
    G["hid.kempty"] = H1(not (compact and not upcoming))
    G["hid.kgo"] = "1"
    ag_off = compact or chart
    G["hid.btn"] = H1(ag_off or typing)
    G["hid.inag"] = H1(ag_off or not typing)
    G["hid.fxadd"] = H1(compact or chart or inp in ("add0", "add1"))
    G["hid.infx"] = H1(compact or chart or inp != "add0")
    G["hid.incr"] = H1(compact or chart or inp != "add1")
    G["hid.inwx"] = H1(compact or inp != "city")
    G["hid.tkempty"] = H1(ag_off or bool(tasks))
    for i in range(NE):
        G[f"hid.evx{i}"] = H1(ag_off or typing or i >= len(evmap) or evmap[i] < 0)
    for i in range(NT):
        G[f"hid.tkx{i}"] = H1(ag_off or i >= len(tasks))

    write_chunks("text", text_keys(), T)
    write_chunks("geo", geo_keys(), G)
    with state_lock():
        st = load_json(STATE, DEFAULT_STATE)
        st["evmap"] = evmap
        save_json(STATE, st)


def write_chunks(prefix, keys, values):
    for n, ks in enumerate(chunks(keys)):
        lines = [str(values.get(k, "")).replace("\r", "").replace("\n", " ") for k in ks]
        path = os.path.join(DATA, "%s%d.txt" % (prefix, n))
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, path)


# ---------------------------------------------------------------- действия
def poke():
    """Просит Rainmeter сразу перечитать файлы данных (иначе виджет обновится только на следующем тике)."""
    try:
        subprocess.Popen([RAINMETER, "!Update", load_config().get("skin_name", "TihiyDen")], creationflags=0x08000000)
    except Exception:
        pass


def act(name, arg=None):
    if name == "inputoff":
        # окно ввода закрылось (Esc / потеря фокуса, а при Enter — ещё и вслед за командой «in»):
        # ждём, чтобы не затереть результат «in» (например, сообщение об ошибке)
        time.sleep(1.5)
        if not load_json(STATE, DEFAULT_STATE).get("input"):
            return
    lock = state_lock()
    lock.__enter__()
    state = load_json(STATE, DEFAULT_STATE)
    today = dt.date.today()
    if name == "mode":
        state["mode"] = "compact" if state["mode"] == "expanded" else "expanded"
        state["chartOpen"] = False
    elif name == "month":
        m = (state.get("month") or today.month) + int(arg)
        y = state.get("year") or today.year
        if m < 1:
            m, y = 12, y - 1
        if m > 12:
            m, y = 1, y + 1
        state["month"], state["year"] = m, y
    elif name == "date":
        m = state.get("month") or today.month
        y = state.get("year") or today.year
        first_wd, ndays = pycal.monthrange(y, m)
        day = int(arg) - first_wd + 1
        if 1 <= day <= ndays:
            state["selected"] = dt.date(y, m, day).isoformat()
    elif name == "today":
        state["month"] = state["year"] = state["selected"] = None
    elif name == "chart":
        state["chartOpen"] = True
        state["chart"] = arg
        state["period"] = "7d"
    elif name == "rm":
        cfg_ = load_config()
        li, ri = (int(x) for x in arg.split(":"))
        if li < len(cfg_["lists"]) and ri < len(cfg_["lists"][li]):
            del cfg_["lists"][li][ri]
            save_config(cfg_)
            refresh_data()
    elif name == "chartclose":
        state["chartOpen"] = False
    elif name == "period":
        state["period"] = arg
    elif name == "retry":
        refresh_data(force=True)
    elif name == "connect":
        gcal.calendars()
        subprocess.Popen(["notepad.exe", gcal.CAL_FILE])
    elif name == "task":
        gcal.toggle_task(int(arg))
    elif name == "taskadd":
        if not os.path.exists(gcal.TASK_FILE):
            with open(gcal.TASK_FILE, "w", encoding="utf-8") as f:
                f.write(tr("task_example"))
        subprocess.Popen(["notepad.exe", gcal.TASK_FILE])
    elif name == "cfg":
        subprocess.Popen(["notepad.exe", CONFIG])
    elif name == "inputon":
        if time.time() - state.get("input_done", 0) > 2.0:  # запоздавший inputon после быстрого Enter не должен открывать режим заново
            state["input"] = arg
            state.pop("toast", None)
    elif name == "inputoff":
        state["input"] = None
    elif name == "tkdel":
        gcal.delete_task(int(arg))
    elif name == "evdel":
        evmap = state.get("evmap") or []
        i = int(arg)
        if i < len(evmap) and evmap[i] >= 0:
            gcal.delete_local_event(evmap[i])
    elif name == "gclick":
        meta = load_json(gcal.META, {})
        if meta.get("ok"):
            gcal.sync(force=True)
        else:
            gcal.calendars()
            subprocess.Popen(["notepad.exe", gcal.CAL_FILE])
    save_json(STATE, state)
    lock.__exit__()
    render()
    poke()


TIME_RE = r"(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?"


def _parse_clock(txt):
    """'18:30' | '6:30pm' | '6pm' -> 'HH:MM' или None (голое число без минут и am/pm временем не считаем)."""
    m = re.fullmatch(TIME_RE, txt.strip().lower())
    if not m or (m.group(2) is None and m.group(3) is None):
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    return "%02d:%02d" % (h, mi) if h < 24 and mi < 60 else None


def parse_event(text):
    """'18:30-19:45 Встреча' -> ('18:30', '19:45', 'Встреча'); без времени -> ('', '', 'Встреча')."""
    text = text.strip()
    m = re.match(r"^(\S+?)\s*[-–]\s*(\S+)\s+(.+)$", text)
    if m:
        a, b = _parse_clock(m.group(1)), _parse_clock(m.group(2))
        if a and b:
            return a, b, m.group(3).strip()
    m = re.match(r"^(\S+(?:\s*[ap]m)?)\s+(.+)$", text, re.I)
    if m:
        a = _parse_clock(m.group(1))
        if a:
            return a, "", m.group(2).strip()
    return "", "", text


def toast_msg(state, sec, msg):
    state["toast"] = {"sec": sec, "msg": msg, "until": time.time() + 6}


def finish_input(state, kind, orig):
    """Закрывает режим ввода и переносит результат (сообщение об ошибке, выбранную монету) в свежий state.json."""
    with state_lock():
        st = load_json(STATE, DEFAULT_STATE)
        st["input"] = None
        st["input_done"] = time.time()
        if state.get("toast") != orig["toast"]:
            st["toast"] = state.get("toast")
        if state.get("chart") != orig["chart"]:
            st["chart"] = state.get("chart")
        save_json(STATE, st)


def add_input(kind, text):
    """Результат окна ввода (Enter): добавляет задачу / событие / валюту / монету."""
    text = (text or "").strip()
    state = load_json(STATE, DEFAULT_STATE)
    orig = {"toast": state.get("toast"), "chart": state.get("chart")}
    if not text:
        finish_input(state, kind, orig)
        render()
        poke()
        return
    cfg = load_config()
    if kind == "task":
        gcal.add_task(text)
    elif kind == "event":
        sel = dt.date.fromisoformat(state["selected"]) if state.get("selected") else dt.date.today()
        st, en, title = parse_event(text)
        gcal.add_local_event(sel, st, en, title)
    elif kind in ("add0", "add1"):
        li = int(kind[-1])
        base = cfg.get("fx_base", "RUB")
        item, err = markets.resolve(text, base)
        if not item:
            toast_msg(state, kind, tr("err_nofx") % text[:12] if err == "nofx" else tr("err_notfound") % text[:14])
        else:
            lists = cfg["lists"]
            while len(lists) < 2:
                lists.append([])
            old = json.loads(json.dumps(lists))
            key = markets.item_key(item)
            lists[li] = ([item] + [it for it in lists[li] if markets.item_key(it) != key])[:3]
            save_config(cfg)
            cache = refresh_data(force=item["k"] == "coin")
            if key not in (cache.get("items") or {}):
                cfg["lists"] = old
                save_config(cfg)
                refresh_data()
                toast_msg(state, kind, tr("err_notfound") % text[:14])
            else:
                state["chart"] = "%d:0" % li
                toast_msg(state, kind, tr("added") % item_label(item, base))
    elif kind == "city":
        try:
            g = geocode(text, cfg.get("lang", "ru"))
        except Exception:
            g = None
            toast_msg(state, "city", tr("err_net"))
        if g is None and not (state.get("toast") or {}).get("sec") == "city":
            toast_msg(state, "city", tr("err_city") % text[:14])
        elif g:
            cfg.update({"lat": g["lat"], "lon": g["lon"], "label": g["label"], "tz": g["tz"]})
            save_config(cfg)
            refresh_data(force=True)
    finish_input(state, kind, orig)
    render()
    poke()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "refresh"
    os.makedirs(DATA, exist_ok=True)
    if not os.path.exists(CONFIG):
        save_config(load_config())
    if cmd == "refresh":
        refresh_data(force="--force" in sys.argv)
        render()
    elif cmd == "render":
        render()
    elif cmd == "act":
        act(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "in":
        add_input(sys.argv[2], " ".join(sys.argv[3:]))


if __name__ == "__main__":
    main()
