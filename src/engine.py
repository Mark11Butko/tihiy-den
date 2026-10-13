"""Движок виджета «Тихий день» v3: данные -> форматирование -> файлы для Rainmeter, обработка кликов.

  engine.py refresh [--force]   получить устаревшие данные и перерисовать (планировщик, раз в минуту)
  engine.py render              перерисовать из кэша
  engine.py act <действие> [аргумент]
"""
import calendar as pycal
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import google as gcal
from i18n import LANG, tr
from td_common import CFG, COLORS, DATA, NC, NE, NF, NT, chunks, geo_keys, hex_rgba, load_config, save_config, text_keys
from td_layout import CW, RH, S, SPARK_H, SPARK_W, TILE_SPARK_H, TILE_SPARK_W

CACHE = os.path.join(DATA, "cache.json")
STATE = os.path.join(DATA, "state.json")
DEMO = os.environ.get("TD_DEMO") == "1" or bool(CFG.get("demo"))

DEFAULT_STATE = {"mode": "expanded", "chartOpen": False, "coin": 0, "period": "7d", "month": None, "year": None, "selected": None}
CBR_CODES = {"USD": "R01235", "EUR": "R01239", "PLN": "R01565", "CZK": "R01760", "UAH": "R01720", "GBP": "R01035",
             "CHF": "R01775", "JPY": "R01820", "CNY": "R01375", "TRY": "R01700J", "KZT": "R01335", "BYN": "R01090B"}
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


def fetch_weather(cfg):
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


def fetch_fx(cfg):
    if cfg.get("fx_base", "RUB") != "RUB":
        return fetch_fx_ecb(cfg)
    return fetch_fx_cbr(cfg)


def fetch_fx_ecb(cfg):
    """Курсы ЕЦБ через Frankfurter (без ключа): сколько базовой валюты стоит 1 единица котируемой."""
    base = cfg["fx_base"]
    end = dt.date.today()
    start = end - dt.timedelta(days=25)
    out = {}
    for sym in cfg["fx"]:
        if sym == base:
            continue
        j = json.loads(get("https://api.frankfurter.dev/v1/%s..%s?base=%s&symbols=%s" % (start, end, sym, base)))
        rates = j["rates"]
        vals = [rates[d][base] for d in sorted(rates)]
        if len(vals) < 2:
            raise ValueError("not enough ECB data for " + sym)
        out[sym] = {"rate": vals[-1], "chg": (vals[-1] / vals[-2] - 1) * 100, "s7": vals[-7:]}
    out["t"] = time.time()
    return out


def fetch_fx_cbr(cfg):
    end = dt.date.today() + dt.timedelta(days=1)
    start = end - dt.timedelta(days=24)
    out = {}
    for sym in cfg["fx"]:
        url = ("https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=%s&date_req2=%s&VAL_NM_RQ=%s"
               % (start.strftime("%d/%m/%Y"), end.strftime("%d/%m/%Y"), CBR_CODES[sym]))
        root = ET.fromstring(get(url))
        vals = []
        for rec in root.findall("Record"):
            nominal = float(rec.find("Nominal").text.replace(",", "."))
            vals.append(float(rec.find("Value").text.replace(",", ".")) / nominal)
        if len(vals) < 2:
            raise ValueError("not enough CBR data for " + sym)
        out[sym] = {"rate": vals[-1], "chg": (vals[-1] / vals[-2] - 1) * 100, "s7": vals[-7:]}
    out["t"] = time.time()
    return out


def resample(vals, n):
    if len(vals) <= n:
        return list(vals)
    step = (len(vals) - 1) / (n - 1)
    return [vals[int(round(i * step))] for i in range(n)]


def fetch_crypto(cfg, old):
    ids = ",".join(c[0] for c in cfg["coins"])
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=%s&sparkline=true&price_change_percentage=24h" % ids
    data = {d["id"]: d for d in json.loads(get(url))}
    out = {"t": time.time(), "coins": {}, "t30": (old or {}).get("t30", 0)}
    for cid, sym in cfg["coins"]:
        d = data[cid]
        sp = d["sparkline_in_7d"]["price"]
        prev = (old or {}).get("coins", {}).get(cid, {})
        out["coins"][cid] = {"sym": sym, "price": d["current_price"], "chg": d.get("price_change_percentage_24h") or 0.0,
                             "s24": sp[-24:], "s7": resample(sp, 56), "s30": prev.get("s30")}
    return out


def fetch_series30(cfg, crypto):
    for cid, _ in cfg["coins"]:
        try:
            j = json.loads(get("https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=30" % cid))
            crypto["coins"][cid]["s30"] = resample([p[1] for p in j["prices"]], 60)
        except Exception:
            pass
        time.sleep(1.5)
    crypto["t30"] = time.time()


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
        if due("fx", cfg["fx_every"]) or any(s not in cache.get("fx", {}) for s in cfg["fx"] if s != cfg.get("fx_base")):
            cache["fx"] = fetch_fx(cfg)
    except Exception as e:
        cache["err_fx"] = str(e)[:100]
    try:
        if due("crypto", cfg["crypto_every"]):
            cache["crypto"] = fetch_crypto(cfg, cache.get("crypto"))
        if "crypto" in cache and (force or now - cache["crypto"].get("t30", 0) >= cfg["series_every"]
                                  or any(c.get("s30") is None for c in cache["crypto"]["coins"].values())):
            fetch_series30(cfg, cache["crypto"])
    except Exception as e:
        online = False
        cache["err_crypto"] = str(e)[:100]
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
    return "—" if v is None else dec("%.2f" % v)


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
    return "f_" + (sym.lower() if sym.lower() in ("usd", "eur", "pln", "czk", "uah", "gbp") else "other")


def coin_name(sym):
    return "c_" + (sym.lower() if sym.lower() in ("btc", "eth", "ton") else "other")


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
    if cfg.get("fx_base") == "RUB":
        demo_fx = {"USD": (92.45, 0.62), "EUR": (99.18, -0.31), "PLN": (23.41, 0.48), "CZK": (4.02, 0.12), "UAH": (2.23, -0.2), "GBP": (116.4, 0.3)}
    else:
        demo_fx = {"USD": (1.0912, 0.22), "EUR": (1.0, 0.0), "PLN": (0.2331, -0.04), "CZK": (0.0398, 0.1), "GBP": (1.1836, 0.33), "UAH": (0.0242, -0.2)}
    fx = {"t": time.time()}
    for k, sym in enumerate(cfg["fx"]):
        r, c = demo_fx.get(sym, (50.0 + 10 * k, 0.1))
        fx[sym] = {"rate": r, "chg": c, "s7": series(r, 7, 0.004, c / 100 * 3, k)}
    demo_c = {"BTC": (63482, 2.18), "ETH": (3072, -1.24), "TON": (7.41, 0.96)}
    coins = {}
    for k, (cid, sym) in enumerate(cfg["coins"]):
        pr, ch = demo_c.get(sym, (10.0, 0.5))
        coins[cid] = {"sym": sym, "price": pr, "chg": ch, "s24": series(pr, 24, 0.004, ch / 100, k), "s7": series(pr, 56, 0.012, ch / 100 * 2, k),
                      "s30": series(pr, 60, 0.03, ch / 100 * 4, k)}
    return {"weather": weather, "fx": fx, "crypto": {"t": time.time(), "coins": coins, "t30": time.time()}, "online": True}


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
    dots = google["days"] if connected else {}
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
    T["cal.sync"] = tr("offline") if not online else (tr("synced") % google["synced"] if google.get("synced") else "")
    G["stale"] = rgba("warning") if not online else rgba("accent")

    # --- повестка
    events = google.get("events", []) if connected else []
    tasks = google.get("tasks", [])
    T["ag.title"] = (tr("today_fmt") if sel == today else tr("day_fmt")).format(d=sel.day, m=MONTHS_GEN[sel.month - 1])
    T["ag.empty"] = tr("no_events") if (connected and not events) else ""
    for i in range(NE):
        if i < len(events):
            e = events[i]
            T[f"ev{i}.t"] = e["time"].replace(" – ", " %s " % EN) if " – " in e["time"] else e["time"]
            T[f"ev{i}.n"] = e["title"]
            G[f"col.ev{i}"] = hex_rgba(e.get("color", COLORS["accent"]))
        else:
            G[f"col.ev{i}"] = "0,0,0,0"
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

    # --- валюты
    fx = cache.get("fx") or {}
    base = cfg.get("fx_base", "RUB")
    comp = []
    for i in range(NF):
        sym = cfg["fx"][i] if i < len(cfg["fx"]) else None
        d = fx.get(sym) if sym else None
        G[f"fl.fx{i}"] = flag_name(sym) if sym else "f_none"
        if d:
            T[f"fx{i}.p"] = "%s/%s" % (sym, base)
            T[f"fx{i}.r"] = fmt_rate(d["rate"])
            T[f"fx{i}.c"] = fmt_change(d["chg"])
            ch = trend_hex(d["chg"])
            line, area = spark_paths(d["s7"], SPARK_W, SPARK_H)
        else:
            T[f"fx{i}.p"], T[f"fx{i}.r"], T[f"fx{i}.c"] = (("%s/%s" % (sym, base)) if sym else ""), "—", ""
            ch = COLORS["textDim"]
            line, area = spark_paths([], SPARK_W, SPARK_H)
        G[f"sp.fx{i}.l"], G[f"sp.fx{i}.a"] = line, area
        G[f"col.fx{i}"], G[f"cola.fx{i}"] = hex_rgba(ch), hex_rgba(ch, 0.14)

    # --- крипта
    cr = (cache.get("crypto") or {}).get("coins", {})
    coins = cfg["coins"]
    for i in range(NC):
        cid, sym = coins[i] if i < len(coins) else (None, "")
        d = cr.get(cid) if cid else None
        G[f"lg.c{i}"] = coin_name(sym) if sym else "c_none"
        if d:
            T[f"cr{i}.s"], T[f"cr{i}.p"], T[f"cr{i}.c"] = sym, usd(fmt_price(d["price"])), fmt_change(d["chg"])
            ch = trend_hex(d["chg"])
            line, area = spark_paths(d["s7"], SPARK_W, SPARK_H)
        else:
            T[f"cr{i}.s"], T[f"cr{i}.p"], T[f"cr{i}.c"] = sym, "—", ""
            ch = COLORS["textDim"]
            line, area = spark_paths([], SPARK_W, SPARK_H)
        G[f"sp.c{i}.l"], G[f"sp.c{i}.a"] = line, area
        G[f"col.c{i}"], G[f"cola.c{i}"] = hex_rgba(ch), hex_rgba(ch, 0.14)

    # --- график (раскрытая монета)
    ci = min(state.get("coin", 0), max(0, len(coins) - 1))
    cid, sym = coins[ci]
    d = cr.get(cid)
    per = state.get("period", "7d")
    for i, p in enumerate(("24h", "7d", "30d")):
        G[f"pc{i}"] = rgba("text") if p == per else rgba("textDim")
    G["ch.l"] = "0,0 | LineTo 0,0"
    G["ch.a"] = "0,0 | LineTo 0,0 | ClosePath 1"
    G["ch.dot"], G["ch.cury"] = NONE_SHAPE, "0"
    G["ch.col"], G["ch.cola"] = rgba("accent"), rgba("accent", 0.12)
    T["ch.title"] = "%s · %s" % (sym, usd(fmt_price(d["price"]))) if d else sym
    series = {"24h": d.get("s24"), "7d": d.get("s7"), "30d": d.get("s30")}.get(per) if d else None
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
        T["ch.current"] = usd(fmt_price(d["price"]))
        T["ch.minmax"] = tr("minmax") % (usd(fmt_price(min(series))), usd(fmt_price(max(series))))
    else:
        T["ch.minmax"], T["ch.current"] = tr("no_data"), ""

    # --- компактный режим
    upcoming = []
    if connected:
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
    T["cp.empty"] = tr("no_events") if connected else tr("cp_disconnected")
    tiles = [(cfg["fx"][0], "fx0"), (cfg["fx"][1], "fx1")] if len(cfg["fx"]) > 1 else []
    for i in range(3):
        if i < 2 and i < len(cfg["fx"]) and cfg["fx"][i] in fx:
            sym = cfg["fx"][i]
            dd = fx[sym]
            T[f"cp.f{i}.p"], T[f"cp.f{i}.r"], T[f"cp.f{i}.c"] = "%s/%s" % (sym, base), fmt_rate(dd["rate"]), fmt_change(dd["chg"])
            line, area = spark_paths(dd["s7"], TILE_SPARK_W, TILE_SPARK_H)
            ch = trend_hex(dd["chg"])
        elif i == 2 and coins and cr.get(coins[0][0]):
            dd = cr[coins[0][0]]
            T[f"cp.f{i}.p"], T[f"cp.f{i}.r"], T[f"cp.f{i}.c"] = coins[0][1], usd(fmt_price(dd["price"])), fmt_change(dd["chg"])
            line, area = spark_paths(dd["s7"], TILE_SPARK_W, TILE_SPARK_H)
            ch = trend_hex(dd["chg"])
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
    G["hid.cal"] = H1(compact or not connected)
    G["hid.sync"] = H1(compact or not connected)
    G["hid.ag"] = H1(compact or chart or not connected)
    G["hid.go"] = H1(compact or connected or chart)
    G["hid.lists"] = H1(compact or chart)
    G["hid.ch"] = H1(not chart)
    G["hid.k"] = H1(not compact)
    G["hid.kev"] = H1(not (compact and connected and upcoming))
    G["hid.kempty"] = H1(not (compact and not (connected and upcoming)))
    G["hid.kgo"] = H1(not (compact and not connected))

    write_chunks("text", text_keys(), T)
    write_chunks("geo", geo_keys(), G)


def write_chunks(prefix, keys, values):
    for n, ks in enumerate(chunks(keys)):
        lines = [str(values.get(k, "")).replace("\r", "").replace("\n", " ") for k in ks]
        path = os.path.join(DATA, "%s%d.txt" % (prefix, n))
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, path)


# ---------------------------------------------------------------- действия
def act(name, arg=None):
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
        state["coin"] = int(arg)
        state["period"] = "7d"
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
    elif name in ("fxsettings", "cryptosettings"):
        subprocess.Popen(["notepad.exe", CONFIG])
    save_json(STATE, state)
    render()


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


if __name__ == "__main__":
    main()
