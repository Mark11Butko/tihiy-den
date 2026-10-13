"""Календарь Google через секретные iCal-адреса (только чтение, без OAuth) + локальные задачи.

Файл calendars.txt: по одной строке «URL [#цвет] [название]». Строки с # в начале — комментарии.
Файл tasks.txt: по одной задаче в строке; «x » в начале — выполнена.
Файл events.txt: свои события, которые добавляются прямо из виджета (кнопка «Событие»).
"""
import datetime as dt
import json
import os
import re
import time
import urllib.request

import icalendar
import recurring_ical_events

from i18n import tr
from td_common import DATA, ROOT

CAL_FILE = os.path.join(ROOT, "calendars.txt")
TASK_FILE = os.path.join(ROOT, "tasks.txt")
EVENT_FILE = os.path.join(ROOT, "events.txt")   # свои события: ГГГГ-ММ-ДД|ЧЧ:ММ|ЧЧ:ММ|название
LOCAL_COLOR = "#8BD4E8FF"
META = os.path.join(DATA, "gmeta.json")
PALETTE = ["#8ACBFFFF", "#E8C487FF", "#91D6B1FF", "#F0A5A5FF", "#C3B1F0FF"]
EVERY = 300



def calendars():
    if not os.path.exists(CAL_FILE):
        os.makedirs(os.path.dirname(CAL_FILE), exist_ok=True)
        with open(CAL_FILE, "w", encoding="utf-8") as f:
            f.write(tr("cal_template"))
    out = []
    with open(CAL_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            url = parts[0]
            if not url.startswith("http"):
                continue
            color = next((p for p in parts[1:] if re.fullmatch(r"#[0-9A-Fa-f]{6}", p)), None)
            name = " ".join(p for p in parts[1:] if p != color)
            out.append({"url": url, "color": (color + "FF") if color else PALETTE[len(out) % len(PALETTE)], "name": name or tr("cal_name") % (len(out) + 1)})
    return out


def _load_meta():
    try:
        with open(META, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sync(force=False):
    cals = calendars()
    meta = _load_meta()
    now = time.time()
    if not cals:
        meta = {"ok": False, "n": 0}
        _save_meta(meta)
        return meta
    if not force and meta.get("n") == len(cals) and meta.get("urls") == [c["url"] for c in cals] and now - meta.get("t", 0) < EVERY and meta.get("ok"):
        return meta
    ok = 0
    for i, c in enumerate(cals):
        try:
            req = urllib.request.Request(c["url"], headers={"User-Agent": "TihiyDen/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            icalendar.Calendar.from_ical(data)  # проверка
            with open(os.path.join(DATA, "ics_%d.ics" % i), "wb") as f:
                f.write(data)
            ok += 1
        except Exception as e:
            meta["err"] = str(e)[:80]
    if ok:
        meta.update({"ok": True, "t": now, "n": len(cals), "urls": [c["url"] for c in cals], "synced": dt.datetime.now().strftime("%H:%M")})
        meta.pop("err", None)
    else:
        meta.update({"ok": False, "n": len(cals)})
    _save_meta(meta)
    return meta


def _save_meta(meta):
    tmp = META + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    os.replace(tmp, META)


def _local(d):
    if isinstance(d, dt.datetime):
        if d.tzinfo is None:
            return d
        return d.astimezone()
    return d


def month_events(y, m):
    """{день: [ {sort, time, title, color} ]} по всем подключённым календарям."""
    cals = calendars()
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), (m % 12) + 1, 1)
    tz = dt.datetime.now().astimezone().tzinfo
    start = dt.datetime.combine(first, dt.time.min, tzinfo=tz)
    end = dt.datetime.combine(last, dt.time.min, tzinfo=tz)
    days = {}
    for i, c in enumerate(cals):
        path = os.path.join(DATA, "ics_%d.ics" % i)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "rb") as f:
                cal = icalendar.Calendar.from_ical(f.read())
            evs = recurring_ical_events.of(cal).between(start, end)
        except Exception:
            continue
        for ev in evs:
            try:
                s = ev.decoded("DTSTART")
                e = ev.decoded("DTEND") if ev.get("DTEND") is not None else s
            except Exception:
                continue
            title = str(ev.get("SUMMARY", tr("no_title")))
            allday = not isinstance(s, dt.datetime)
            s_l, e_l = _local(s), _local(e)
            d0 = s_l if allday else s_l.date()
            d1 = (e_l - dt.timedelta(days=1)) if allday else (e_l.date() if e_l > s_l else s_l.date())
            if isinstance(d0, dt.datetime):
                d0 = d0.date()
            if isinstance(d1, dt.datetime):
                d1 = d1.date()
            if d1 < d0:
                d1 = d0
            day = max(d0, first)
            while day <= min(d1, last - dt.timedelta(days=1)):
                if allday:
                    label, srt, st, en = tr("all_day"), "0", None, None
                elif day == d0:
                    end_t = e_l.strftime("%H:%M") if e_l.date() == d0 and e_l > s_l else ""
                    label = s_l.strftime("%H:%M") + ((" – " + end_t) if end_t else "")
                    srt, st, en = s_l.strftime("%H:%M"), s_l.replace(tzinfo=None).isoformat(), (e_l.replace(tzinfo=None).isoformat() if e_l > s_l else None)
                else:
                    label, srt, st, en = "…", "00:00", None, None
                days.setdefault(day.day, []).append({"sort": srt, "time": label, "title": title, "color": c["color"], "start": st, "end": en})
                day += dt.timedelta(days=1)
    for day_n, items in local_events(y, m).items():
        days.setdefault(day_n, []).extend(items)
    for d in days.values():
        d.sort(key=lambda x: x["sort"])
    return days


def tasks():
    if not os.path.exists(TASK_FILE):
        return []
    out = []
    with open(TASK_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            done = line.lower().startswith("x ")
            out.append({"title": line[2:].strip() if done else line.strip(), "done": done})
    return out


def _write_tasks(ts):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        for t in ts:
            f.write(("x " if t["done"] else "") + t["title"] + "\n")


def add_task(title):
    title = title.strip()
    if not title:
        return
    ts = tasks()
    ts.append({"title": title, "done": False})
    _write_tasks(ts)


def delete_task(i):
    ts = tasks()
    if 0 <= i < len(ts):
        del ts[i]
        _write_tasks(ts)


def _read_local():
    out = []
    if not os.path.exists(EVENT_FILE):
        return out
    with open(EVENT_FILE, encoding="utf-8") as f:
        for n, line in enumerate(f):
            p = line.rstrip("\n").split("|", 3)
            if len(p) == 4 and p[3].strip():
                out.append(p)
            else:
                out.append(None)  # пустая/битая строка сохраняет нумерацию
    return out


def _write_local(rows):
    with open(EVENT_FILE, "w", encoding="utf-8") as f:
        for p in rows:
            if p:
                f.write("|".join(p) + "\n")


def add_local_event(day, start, end, title):
    title = title.strip().replace("|", "/")
    if not title:
        return
    rows = [r for r in _read_local() if r]
    rows.append([day.isoformat(), start or "", end or "", title])
    _write_local(rows)


def delete_local_event(lid):
    rows = _read_local()
    if 0 <= lid < len(rows):
        rows[lid] = None
        _write_local(rows)


def local_events(y, m):
    """Свои события месяца в том же формате, что и события Google (+ lid — номер строки для удаления)."""
    days = {}
    for lid, p in enumerate(_read_local()):
        if not p:
            continue
        try:
            d = dt.date.fromisoformat(p[0])
        except ValueError:
            continue
        if d.year != y or d.month != m:
            continue
        st, en, title = p[1], p[2], p[3]
        if st:
            label = st + ((" – " + en) if en else "")
            start_iso = dt.datetime.combine(d, dt.time.fromisoformat(st)).isoformat()
            end_iso = dt.datetime.combine(d, dt.time.fromisoformat(en)).isoformat() if en else None
            item = {"sort": st, "time": label, "title": title, "color": LOCAL_COLOR, "start": start_iso, "end": end_iso, "lid": lid}
        else:
            item = {"sort": "0", "time": tr("all_day"), "title": title, "color": LOCAL_COLOR, "start": None, "end": None, "lid": lid}
        days.setdefault(d.day, []).append(item)
    return days


def toggle_task(i):
    ts = tasks()
    if 0 <= i < len(ts):
        ts[i]["done"] = not ts[i]["done"]
        with open(TASK_FILE, "w", encoding="utf-8") as f:
            for t in ts:
                f.write(("x " if t["done"] else "") + t["title"] + "\n")


def view(y, m, sel):
    """Данные для отрисовки: connected, synced, events выбранного дня, цвета точек по дням, задачи."""
    meta = _load_meta()
    connected = bool(meta.get("ok"))
    res = {"connected": connected, "synced": meta.get("synced"), "events": [], "days": {}, "tasks": tasks(), "err": meta.get("err")}
    days = month_events(y, m)
    for d, evs in days.items():
        seen = []
        for e in evs:
            if e["color"] not in seen:
                seen.append(e["color"])
        res["days"][d] = seen[:3]
    if sel.year == y and sel.month == m:
        res["events"] = days.get(sel.day, [])
    else:
        res["events"] = month_events(sel.year, sel.month).get(sel.day, [])
    return res
