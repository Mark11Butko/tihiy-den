"""Котировки для списков виджета: валюты, крипта, металлы, нефть, акции, индексы.

Источники (без ключей):
  валюты      — ЦБ РФ (если база RUB) или ЕЦБ через Frankfurter
  крипта      — CoinGecko
  всё остальное (золото, нефть, акции, индексы, фьючерсы) — Yahoo Finance (публичный chart API)

Элемент списка:  {"k": "fx", "s": "USD"} | {"k": "coin", "id": "bitcoin", "s": "BTC"} | {"k": "y", "id": "GC=F", "s": "GOLD"}
Данные элемента: {"price", "chg" (% за сутки), "s24", "s7", "s30" (ряды для графиков), "cur", "t"}
"""
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (compatible; TihiyDen/1.1)"

CBR_CODES = {"USD": "R01235", "EUR": "R01239", "PLN": "R01565", "CZK": "R01760", "UAH": "R01720", "GBP": "R01035",
             "CHF": "R01775", "JPY": "R01820", "CNY": "R01375", "TRY": "R01700J", "KZT": "R01335", "BYN": "R01090B"}
FIAT = set("USD EUR GBP CHF JPY CNY PLN CZK UAH TRY KZT BYN SEK NOK DKK HUF RON BGN CAD AUD NZD INR BRL MXN ZAR KRW SGD HKD ILS THB AED SAR".split())
# понятные имена -> (тикер Yahoo, короткая подпись)
ALIASES = {
    "gold": ("GC=F", "GOLD"), "золото": ("GC=F", "GOLD"), "xau": ("GC=F", "GOLD"),
    "silver": ("SI=F", "SILVER"), "серебро": ("SI=F", "SILVER"), "xag": ("SI=F", "SILVER"),
    "platinum": ("PL=F", "PLATINUM"), "платина": ("PL=F", "PLATINUM"),
    "copper": ("HG=F", "COPPER"), "медь": ("HG=F", "COPPER"),
    "oil": ("BZ=F", "BRENT"), "нефть": ("BZ=F", "BRENT"), "brent": ("BZ=F", "BRENT"), "брент": ("BZ=F", "BRENT"),
    "wti": ("CL=F", "WTI"), "gas": ("NG=F", "GAS"), "газ": ("NG=F", "GAS"),
    "s&p": ("^GSPC", "S&P 500"), "s&p500": ("^GSPC", "S&P 500"), "sp500": ("^GSPC", "S&P 500"), "s&p 500": ("^GSPC", "S&P 500"),
    "nasdaq": ("^IXIC", "NASDAQ"), "dow": ("^DJI", "DOW"), "dax": ("^GDAXI", "DAX"),
}
CUR_SYMBOL = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥", "RUB": "₽", "UAH": "₴", "PLN": "zł", "CHF": "CHF", "CZK": "Kč"}


def http(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/xml,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def item_key(it):
    if it["k"] == "fx":
        return "fx:" + it["s"]
    return "%s:%s" % (it["k"], it["id"])


def resample(vals, n):
    if len(vals) <= n:
        return list(vals)
    step = (len(vals) - 1) / (n - 1)
    return [vals[int(round(i * step))] for i in range(n)]


# ---------------------------------------------------------------- валюты
def fetch_fx_one(sym, base):
    """Сколько базовой валюты стоит 1 единица sym."""
    if base == "RUB":
        end = dt.date.today() + dt.timedelta(days=1)
        start = end - dt.timedelta(days=36)
        url = ("https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1=%s&date_req2=%s&VAL_NM_RQ=%s"
               % (start.strftime("%d/%m/%Y"), end.strftime("%d/%m/%Y"), CBR_CODES[sym]))
        vals = []
        for rec in ET.fromstring(http(url)).findall("Record"):
            nominal = float(rec.find("Nominal").text.replace(",", "."))
            vals.append(float(rec.find("Value").text.replace(",", ".")) / nominal)
    else:
        end = dt.date.today()
        start = end - dt.timedelta(days=36)
        rates = json.loads(http("https://api.frankfurter.dev/v1/%s..%s?base=%s&symbols=%s" % (start, end, sym, base)))["rates"]
        vals = [rates[d][base] for d in sorted(rates)]
    if len(vals) < 2:
        raise ValueError("not enough FX data for " + sym)
    return {"price": vals[-1], "chg": (vals[-1] / vals[-2] - 1) * 100, "s7": vals[-7:], "s30": resample(vals[-30:], 30), "s24": None, "cur": base}


# ---------------------------------------------------------------- крипта
def fetch_coins(ids, old=None):
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=%s&sparkline=true&price_change_percentage=24h" % ",".join(ids)
    data = {d["id"]: d for d in json.loads(http(url))}
    out = {}
    for cid in ids:
        d = data[cid]
        sp = d["sparkline_in_7d"]["price"]
        prev = (old or {}).get(cid) or {}
        out[cid] = {"price": d["current_price"], "chg": d.get("price_change_percentage_24h") or 0.0, "s24": sp[-24:], "s7": resample(sp, 56),
                    "s30": prev.get("s30"), "cur": "USD"}
    return out


def fetch_coin_series30(cid):
    j = json.loads(http("https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=30" % cid))
    return resample([p[1] for p in j["prices"]], 60)


# ---------------------------------------------------------------- Yahoo Finance
def fetch_yahoo(sym):
    q = urllib.parse.quote(sym)
    d1 = json.loads(http("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=1mo&interval=1d" % q))["chart"]["result"][0]
    meta = d1["meta"]
    off = meta.get("gmtoffset") or 0
    pairs = [(t, c) for t, c in zip(d1.get("timestamp") or [], d1["indicators"]["quote"][0]["close"]) if c is not None]
    if not pairs:
        raise ValueError("no data for " + sym)
    price = meta.get("regularMarketPrice") or pairs[-1][1]
    day = lambda ts: dt.datetime.utcfromtimestamp(ts + off).date()  # noqa: E731
    today_bar = day(pairs[-1][0]) == day(meta.get("regularMarketTime") or pairs[-1][0])
    prev = pairs[-2][1] if (today_bar and len(pairs) > 1) else pairs[-1][1]
    closes = [c for _, c in pairs]
    out = {"price": price, "chg": (price / prev - 1) * 100 if prev else 0.0, "s30": resample(closes, 30), "s7": closes[-7:], "s24": None,
           "cur": meta.get("currency", "USD")}
    try:
        d2 = json.loads(http("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=5d&interval=60m" % q))["chart"]["result"][0]
        cl = [c for c in d2["indicators"]["quote"][0]["close"] if c is not None]
        if len(cl) >= 8:
            out["s7"], out["s24"] = resample(cl, 56), cl[-24:]
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- разбор того, что ввёл пользователь
def resolve(text, base):
    """'золото' | 'CHF' | 'SOL' | 'AAPL' | 'нефть' -> (элемент списка, None) либо (None, 'не нашли')."""
    t = text.strip()
    if not t:
        return None, "empty"
    low = t.lower()
    if low in ALIASES:
        sym, label = ALIASES[low]
        return {"k": "y", "id": sym, "s": label}, None
    up = t.upper()
    if re.fullmatch(r"[A-Z]{3}", up) and up in FIAT and up != base:
        if base == "RUB" and up not in CBR_CODES:
            return None, "nofx"
        return {"k": "fx", "s": up}, None
    if low in ("ton", "toncoin", "the open network"):  # CoinGecko ведёт его под тикером GRAM
        return {"k": "coin", "id": "the-open-network", "s": "TON"}, None
    # крипта (настоящие монеты из топ-500), затем акции/индексы/фьючерсы, затем любая монета с таким тикером
    exact = []
    try:
        res = json.loads(http("https://api.coingecko.com/api/v3/search?query=" + urllib.parse.quote(t))).get("coins", [])
        exact = [c for c in res if c.get("symbol", "").lower() == low or c.get("name", "").lower() == low]
        exact.sort(key=lambda c: c.get("market_cap_rank") or 10 ** 9)
        if exact and (exact[0].get("market_cap_rank") or 10 ** 9) <= 500:
            return {"k": "coin", "id": exact[0]["id"], "s": exact[0]["symbol"].upper()}, None
    except Exception:
        pass
    try:
        qs = json.loads(http("https://query1.finance.yahoo.com/v1/finance/search?quotesCount=6&newsCount=0&q=" + urllib.parse.quote(t))).get("quotes", [])
        for q in qs:
            if q.get("quoteType") in ("EQUITY", "ETF", "INDEX", "FUTURE", "MUTUALFUND"):
                label = q["symbol"].replace("=F", "").replace("^", "").upper()
                return {"k": "y", "id": q["symbol"], "s": label[:8]}, None
    except Exception:
        pass
    if exact:
        return {"k": "coin", "id": exact[0]["id"], "s": exact[0]["symbol"].upper()}, None
    return None, "notfound"


# ---------------------------------------------------------------- обновление
EVERY = {"fx": 3600, "coin": 300, "y": 600}


def refresh(cfg, store, force=False, now=None):
    """Обновляет store[ключ] для всех элементов списков. Ошибка одного элемента не ломает остальные."""
    now = now or time.time()
    base = cfg.get("fx_base", "RUB")
    items = [it for lst in cfg.get("lists", []) for it in lst]
    errors = {}
    coins = [it for it in items if it["k"] == "coin"]
    for it in items:
        k = item_key(it)
        cur = store.get(k)
        if it["k"] == "coin":
            continue
        if not force and cur and now - cur.get("t", 0) < EVERY[it["k"]] and (it["k"] != "fx" or cur.get("cur") == base):
            continue
        try:
            d = fetch_fx_one(it["s"], base) if it["k"] == "fx" else fetch_yahoo(it["id"])
            d["t"] = now
            store[k] = d
        except Exception as e:
            errors[k] = str(e)[:80]
    if coins:
        need = [c for c in coins if force or item_key(c) not in store or now - store[item_key(c)].get("t", 0) >= EVERY["coin"]]
        if need:
            try:
                got = fetch_coins([c["id"] for c in coins], {c["id"]: store.get(item_key(c)) for c in coins})
                for c in coins:
                    got[c["id"]]["t"] = now
                    got[c["id"]]["t30"] = (store.get(item_key(c)) or {}).get("t30", 0)
                    store[item_key(c)] = got[c["id"]]
            except Exception as e:
                errors["coins"] = str(e)[:80]
        for c in coins:
            d = store.get(item_key(c))
            if d and (d.get("s30") is None or now - d.get("t30", 0) >= 3600):
                try:
                    d["s30"] = fetch_coin_series30(c["id"])
                    d["t30"] = now
                except Exception:
                    d["t30"] = now - 3000  # повторить попозже
                time.sleep(1.2)
    # убрать данные элементов, которых больше нет в списках
    alive = {item_key(it) for it in items}
    for k in list(store):
        if k not in alive:
            del store[k]
    return errors
