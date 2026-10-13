"""Общее для виджета «Тихий день / Quiet Day»: конфиг, пути, цвета, списки слотов данных."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
CONFIG_PATH = os.path.join(DATA, "config.json")

DEFAULT_CONFIG = {
    "lang": "ru",                      # ru | en
    "label": "Bratislava",             # подпись города в виджете
    "lat": 48.1486, "lon": 17.1077,    # координаты для прогноза (Open-Meteo)
    "fx_base": "RUB",                  # RUB -> курсы ЦБ РФ; иначе (EUR/USD/PLN...) -> курсы ЕЦБ (Frankfurter)
    "fx": ["USD", "EUR", "PLN"],
    "coins": [["bitcoin", "BTC"], ["ethereum", "ETH"], ["the-open-network", "TON"]],
    "scale": 0.9,                      # размер виджета (0.7 .. 1.2)
    "clock24": True,
    "skin_name": "TihiyDen",
    "weather_every": 900, "fx_every": 3600, "crypto_every": 300, "series_every": 3600,
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    os.makedirs(DATA, exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_PATH)


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
SKIN_DIR = os.path.join(SKINS, SKIN_NAME)
RAINMETER = rainmeter_exe()

# Палитра (из JSON v2 + цвета с картинки)
COLORS = {
    "background": "#0D1624E6", "surface": "#FFFFFF0D", "surface2": "#FFFFFF08", "stroke": "#FFFFFF26",
    "text": "#F4F7FBFF", "textDim": "#AEBBCCFF", "textFaint": "#7F8CA0FF",
    "accent": "#8BD4E8FF", "blue": "#2F7BFFFF", "up": "#4ADE80FF", "down": "#F87171FF", "warning": "#E8C88EFF",
    "sun": "#FFC83DFF",
}


def hex_rgba(h, alpha_mul=1.0):
    """#RRGGBBAA -> 'R,G,B,A' для Rainmeter."""
    h = h.lstrip("#")
    if len(h) == 6:
        h += "FF"
    r, g, b, a = (int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
    return f"{r},{g},{b},{int(round(a * alpha_mul))}"


CHUNK = 24
NF = 3  # валют
NC = 3  # монет
NE = 3  # событий
NT = 3  # задач


def text_keys():
    k = ["date1", "date2", "w.loc", "w.temp", "w.feels", "w.hi", "w.lo", "w.wind", "w.hum"]
    for i in range(6):
        k += [f"h{i}.l", f"h{i}.t"]
    for i in range(5):
        k += [f"d{i}.n", f"d{i}.d", f"d{i}.h", f"d{i}.l"]
    k += ["cal.title", "cal.sync"] + [f"c{i}" for i in range(42)]
    k += ["ag.title", "ag.empty"]
    for i in range(NE):
        k += [f"ev{i}.t", f"ev{i}.n"]
    k += [f"tk{i}" for i in range(NT)]
    k += ["status"]
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
    k += ["stale"]
    return k


def safe(key):
    return key.replace(".", "_")


def chunks(keys):
    return [keys[i:i + CHUNK] for i in range(0, len(keys), CHUNK)]
