"""Общее для виджета «Тихий день / Quiet Day»: конфиг, пути, цвета, списки слотов данных."""
import json
import os
import sys
import math
import re
from td_storage import write_json

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.environ.get("TD_DATA_DIR", os.path.join(ROOT, "data")))
USER_ROOT = os.path.abspath(os.environ.get("TD_USER_DIR", ROOT))
CONFIG_PATH = os.path.join(DATA, "config.json")

DEFAULT_CONFIG = {
    "lang": "ru",                      # ru | en
    "label": "Bratislava",             # подпись города в виджете
    "lat": 48.1486, "lon": 17.1077,    # координаты для прогноза (Open-Meteo)
    "fx_base": "RUB",                  # RUB -> курсы ЦБ РФ; иначе (EUR/USD/PLN...) -> курсы ЕЦБ (Frankfurter)
    # два списка котировок (по 3 строки): валюты / золото / нефть / крипта / акции / индексы — что интересно пользователю
    "lists": [
        [{"k": "fx", "s": "USD"}, {"k": "fx", "s": "EUR"}, {"k": "fx", "s": "PLN"}],
        [{"k": "coin", "id": "bitcoin", "s": "BTC"}, {"k": "coin", "id": "ethereum", "s": "ETH"}, {"k": "coin", "id": "the-open-network", "s": "TON"}],
    ],
    "titles": [None, None],            # свои названия карточек; None = стандартные
    "scale": 1.0,                      # размер виджета (0.7 .. 1.3)
    "accent": "#8BD4E8FF", "opacity": 232, "reduced_motion": True,
    "clock24": True,
    "skin_name": "TihiyDen",
    "weather_every": 900, "fx_every": 3600, "crypto_every": 300, "series_every": 3600,
}


def normalize_config(saved):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if not isinstance(saved, dict):
        return cfg
    cfg.update(saved)
    cfg['lang'] = cfg['lang'] if cfg.get('lang') in ('ru', 'en') else 'ru'
    for key, lo, hi in [('scale', .7, 1.3), ('lat', -90, 90), ('lon', -180, 180), ('opacity', 180, 255), ('weather_every', 60, 86400), ('fx_every', 300, 86400), ('crypto_every', 60, 86400), ('series_every', 300, 86400)]:
        try:
            value = float(cfg[key])
            if not math.isfinite(value): raise ValueError(key)
            cfg[key] = max(lo, min(hi, value))
        except (TypeError, ValueError): cfg[key] = DEFAULT_CONFIG[key]
    cfg['opacity'] = int(cfg['opacity'])
    cfg['fx_base'] = str(cfg.get('fx_base', 'RUB')).upper()
    if not re.fullmatch('[A-Z]{3}', cfg['fx_base']): cfg['fx_base'] = 'RUB'
    cfg['label'] = str(cfg.get('label') or 'Bratislava').replace('\n', ' ')[:80]
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', str(cfg.get('skin_name', ''))): cfg['skin_name'] = 'TihiyDen'
    accent = str(cfg.get('accent', ''))
    cfg['accent'] = accent.upper() + ('FF' if len(accent) == 7 else '') if re.fullmatch('#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', accent) else DEFAULT_CONFIG['accent']
    cfg['clock24'] = cfg.get('clock24') if isinstance(cfg.get('clock24'), bool) else True
    cfg['reduced_motion'] = cfg.get('reduced_motion') if isinstance(cfg.get('reduced_motion'), bool) else True
    titles = cfg.get('titles')
    cfg['titles'] = [(str(titles[i]).replace('\n', ' ')[:40] if i < len(titles) and titles[i] else None) for i in range(2)] if isinstance(titles, list) else [None, None]
    lists = cfg.get('lists')
    if not isinstance(lists, list): lists = DEFAULT_CONFIG['lists']
    normalized = []
    for i in range(2):
        rows = lists[i] if i < len(lists) and isinstance(lists[i], list) else []
        clean, seen = [], set()
        for item in rows:
            if not isinstance(item, dict): continue
            kind, symbol = item.get('k'), str(item.get('s') or '')
            if kind not in ('fx', 'coin', 'y') or not re.fullmatch(r'[A-Za-z0-9 .^=_&+-]{1,16}', symbol): continue
            identity = str(item.get('id') or symbol)
            if kind != 'fx' and not re.fullmatch(r'[A-Za-z0-9.^=_-]{1,80}', identity): continue
            if kind == 'fx' and (not re.fullmatch('[A-Z]{3}', symbol) or symbol == cfg['fx_base']): continue
            key = kind + ':' + identity
            if key in seen: continue
            seen.add(key)
            clean.append({'k':kind, 's':symbol, **({'id':identity} if kind != 'fx' else {})})
        normalized.append(clean[:40])
    cfg['lists'] = normalized
    return cfg


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            saved = json.load(f)
        if not isinstance(saved, dict): return normalize_config(cfg)
        cfg.update(saved)
        if "lists" not in saved and ("fx" in saved or "coins" in saved):
            cfg["lists"] = [[{"k": "fx", "s": c} for c in saved.get("fx", ["USD", "EUR", "PLN"])],
                            [{"k": "coin", "id": c[0], "s": c[1]} for c in saved.get("coins", [])]]
        cfg.pop("fx", None)
        cfg.pop("coins", None)
    except Exception:
        pass
    return normalize_config(cfg)


def save_config(cfg):
    write_json(CONFIG_PATH, normalize_config(cfg))


CFG = load_config()
SKIN_NAME = CFG["skin_name"]
PYTHONW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
if not os.path.exists(PYTHONW):
    PYTHONW = sys.executable


def _read_text_guess(path):
    raw = open(path, "rb").read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", "replace")
    for enc in ("utf-8", "cp1251", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def documents_dir():
    """Папка «Документы» пользователя (учитывает перенос в OneDrive и т.п.)."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(0, 5, 0, 0, buf) == 0:  # CSIDL_PERSONAL
            return buf.value
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def skins_dir():
    """Папка Skins из настроек Rainmeter, иначе стандартная."""
    ini = os.path.join(os.environ.get("APPDATA", ""), "Rainmeter", "Rainmeter.ini")
    try:
        for line in _read_text_guess(ini).splitlines():
            if line.strip().lower().startswith("skinpath="):
                p = line.split("=", 1)[1].strip()
                if p:
                    return p.rstrip("\\/")
    except Exception:
        pass
    return os.path.join(documents_dir(), "Rainmeter", "Skins")


def rainmeter_exe():
    for p in (r"C:\Program Files\Rainmeter\Rainmeter.exe", r"C:\Program Files (x86)\Rainmeter\Rainmeter.exe"):
        if os.path.exists(p):
            return p
    try:
        import winreg
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for sub in (r"SOFTWARE\Rainmeter", r"SOFTWARE\WOW6432Node\Rainmeter"):
                try:
                    with winreg.OpenKey(root, sub) as k:
                        d = winreg.QueryValueEx(k, None)[0]
                        p = os.path.join(d, "Rainmeter.exe")
                        if os.path.exists(p):
                            return p
                except OSError:
                    continue
    except Exception:
        pass
    return r"C:\Program Files\Rainmeter\Rainmeter.exe"


def screen_size():
    try:
        import ctypes
        return ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
    except Exception:
        return 1920, 1080


SKINS = skins_dir()
SKIN_DIR = os.path.abspath(os.environ.get("TD_SKIN_DIR", os.path.join(SKINS, SKIN_NAME)))
RAINMETER = os.path.abspath(os.environ.get('TD_RAINMETER_EXE', rainmeter_exe()))

# Палитра (из JSON v2 + цвета с картинки)
COLORS = {
    "background": "#0D1624E6", "surface": "#FFFFFF0D", "surface2": "#FFFFFF08", "stroke": "#FFFFFF26",
    "text": "#F4F7FBFF", "textDim": "#AEBBCCFF", "textFaint": "#7F8CA0FF",
    "accent": "#8BD4E8FF", "blue": "#2F7BFFFF", "up": "#4ADE80FF", "down": "#F87171FF", "warning": "#E8C88EFF",
    "sun": "#FFC83DFF",
}
COLORS.update(accent=CFG['accent'], blue=CFG['accent'], up='#9EDBB6FF', down='#F1AAA5FF', textFaint='#B4BEC9FF')
COLORS['background'] = '#111820%02X' % CFG['opacity']


def hex_rgba(h, alpha_mul=1.0):
    """#RRGGBBAA -> 'R,G,B,A' для Rainmeter."""
    h = h.lstrip("#")
    if len(h) == 6:
        h += "FF"
    r, g, b, a = (int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
    return f"{r},{g},{b},{int(round(a * alpha_mul))}"


CHUNK = 24
NF = 2  # visible quotes per page
NC = 2
NE = 2  # visible events per page
NT = 1  # visible tasks per page


def text_keys():
    k = ["date1", "date2", "w.loc", "w.temp", "w.feels", "w.hi", "w.lo", "w.wind", "w.hum"]
    for i in range(6):
        k += [f"h{i}.l", f"h{i}.t"]
    for i in range(5):
        k += [f"d{i}.n", f"d{i}.d", f"d{i}.h", f"d{i}.l"]
    k += ["cal.title", "cal.sync"] + [f"c{i}" for i in range(42)]
    k += ["ag.title", "ag.empty", "tk.empty", "fx.title", "cr.title", "in.hint"]
    for i in range(NE):
        k += [f"ev{i}.t", f"ev{i}.n"]
    k += [f"tk{i}" for i in range(NT)]
    k += ["status", "w.precip", "w.summary", "fx.page", "cr.page", "ag.page", "tk.page", "cal.state", "ch.status"]
    for i in range(NF):
        k += [f"fx{i}.p", f"fx{i}.r", f"fx{i}.c"]
    for i in range(NC):
        k += [f"cr{i}.s", f"cr{i}.p", f"cr{i}.c"]
    k += ["ch.title", "ch.minmax", "ch.current"]
    for i in range(2):
        k += [f"cp.ev{i}.t", f"cp.ev{i}.n", f"cp.ev{i}.in"]
    k += ["cp.empty"]
    for i in range(3):
        k += [f"cp.f{i}.p", f"cp.f{i}.r", f"cp.f{i}.c"]
    return k


def geo_keys():
    k = []
    for n in ("fx0", "fx1", "fx2", "c0", "c1", "c2", "t0", "t1", "t2"):
        k += [f"sp.{n}.l", f"sp.{n}.a", f"col.{n}", f"cola.{n}"]
    k += ["ch.l", "ch.a", "ch.dot", "ch.cury", "ch.col", "ch.cola", "pc0", "pc1", "pc2"]
    k += [f"col.ev{i}" for i in range(NE)] + [f"cpcol.ev{i}" for i in range(2)]
    k += [f"tkcol{i}" for i in range(NT)]
    k += [f"cc{i}" for i in range(42)]
    k += [f"dot{i}" for i in range(60)]
    k += ["sel", "today"]
    for i in range(NT):
        k += [f"chk{i}a", f"chk{i}b"]
    k += ["ic.cur"] + [f"ic.h{i}" for i in range(6)] + [f"ic.d{i}" for i in range(5)]
    k += [f"fl.fx{i}" for i in range(NF)] + [f"lg.c{i}" for i in range(NC)] + [f"fl.t{i}" for i in range(3)]
    k += ["hid.ex", "hid.cal", "hid.ag", "hid.go", "hid.lists", "hid.ch", "hid.k", "hid.kev", "hid.kempty", "hid.kgo", "hid.sync"]
    k += ["stale", "hid.fx0", "hid.fx1", "hid.cr0", "hid.cr1", "ch.pill", "ch.pillx"] + [f"hid.evx{i}" for i in range(NE)] + [f"hid.tkx{i}" for i in range(NT)]
    k += ["hid.btn", "hid.fxadd", "hid.inag", "hid.infx", "hid.incr", "hid.tkempty", "hid.inwx"]
    return k


def safe(key):
    return key.replace(".", "_")


def chunks(keys):
    return [keys[i:i + CHUNK] for i in range(0, len(keys), CHUNK)]
