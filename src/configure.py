"""Первичная настройка: python configure.py --lang ru --city Bratislava --base RUB
Ищет координаты города через Open-Meteo Geocoding и сохраняет data/config.json."""
import argparse
import json
import urllib.parse
import urllib.request

from td_common import load_config, save_config

ap = argparse.ArgumentParser()
ap.add_argument("--lang", choices=["ru", "en"])
ap.add_argument("--city")
ap.add_argument("--lat", type=float)
ap.add_argument("--lon", type=float)
ap.add_argument("--base")
ap.add_argument("--scale", type=float)
ap.add_argument("--skin-name")
a = ap.parse_args()

cfg = load_config()
if a.lang:
    cfg["lang"] = a.lang
if a.base:
    cfg["fx_base"] = a.base.upper()
    if cfg["fx_base"] != "RUB":
        cfg["fx"] = [c for c in ("USD", "EUR", "GBP", "PLN", "CZK") if c != cfg["fx_base"]][:3]
    else:
        cfg["fx"] = ["USD", "EUR", "PLN"]
if a.scale:
    cfg["scale"] = a.scale
if a.skin_name:
    cfg["skin_name"] = a.skin_name
if a.lat is not None and a.lon is not None:
    cfg["lat"], cfg["lon"] = a.lat, a.lon
    cfg["label"] = a.city or cfg["label"]
elif a.city:
    url = "https://geocoding-api.open-meteo.com/v1/search?count=1&language=%s&name=%s" % (cfg["lang"], urllib.parse.quote(a.city))
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            res = json.load(r).get("results") or []
        if res:
            cfg["lat"], cfg["lon"], cfg["label"] = res[0]["latitude"], res[0]["longitude"], res[0]["name"]
            print("City found: %s (%.3f, %.3f)" % (cfg["label"], cfg["lat"], cfg["lon"]))
        else:
            print("City not found, keeping default: %s" % cfg["label"])
    except Exception as e:
        print("Geocoding failed (%s), keeping default: %s" % (e, cfg["label"]))
save_config(cfg)
print("config saved")
