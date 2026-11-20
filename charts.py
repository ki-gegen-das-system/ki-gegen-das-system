#!/usr/bin/env python3
"""
Speichert die ECHTEN Kursdaten für die Videos: 15-Minuten-Kerzen jedes Handelstags
plus Berts Linien (EMA 9 = "blau", EMA 21 = "gelb"), genau so, wie Bert sie berechnet.

Ergebnis: data/charts/JJJJ-MM-TT.json (Datum = US-Handelstag), Uhrzeiten in deutscher Zeit.
Wird von bert.py nach Börsenschluss automatisch aufgerufen.
Per Hand (z. B. zum Nachladen): python3 charts.py   oder   python3 charts.py --neu  (überschreibt)
Quelle: Alpaca Market Data, IEX-Feed.
"""
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import bert

NY = ZoneInfo("America/New_York")
CHART_DIR = os.path.join(bert.DATA_DIR, "charts")
DAYS_BACK = 10          # so weit zurück Kerzen laden (Vorlauf für die Linien)
KEEP_SESSIONS = 7       # für so viele letzte Handelstage Dateien anlegen, falls sie fehlen


def traded_symbols():
    syms = set()
    if os.path.exists(bert.TRADES_FILE):
        with open(bert.TRADES_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                syms.add(row["symbol"])
    return syms


def fetch_bars(symbols, start, end):
    bars = {s: [] for s in symbols}
    token = None
    for _ in range(40):
        p = {"symbols": ",".join(sorted(symbols)), "timeframe": "15Min", "start": bert.iso_z(start),
             "end": bert.iso_z(end), "feed": "iex", "limit": 10000, "adjustment": "raw", "sort": "asc"}
        if token:
            p["page_token"] = token
        r = bert.call("GET", bert.DATA_API, "/v2/stocks/bars", p) or {}
        for s, lst in (r.get("bars") or {}).items():
            bars.setdefault(s, []).extend(lst)
        token = r.get("next_page_token")
        if not token:
            break
    for s in bars:
        bars[s].sort(key=lambda b: b["t"])
    return bars


def in_session(t_utc):
    ny = t_utc.astimezone(NY)
    minutes = ny.hour * 60 + ny.minute
    return ny.weekday() < 5 and 9 * 60 + 30 <= minutes < 16 * 60


def session_done(ny_date, now):
    now_ny = now.astimezone(NY)
    if ny_date < now_ny.date():
        return True
    return ny_date == now_ny.date() and (now_ny.hour * 60 + now_ny.minute) >= 16 * 60 + 5


def save_missing(now=None, overwrite=False):
    now = now or datetime.now(timezone.utc)
    os.makedirs(CHART_DIR, exist_ok=True)
    symbols = set(bert.SYMBOLS) | traded_symbols()
    bars = fetch_bars(symbols, now - timedelta(days=DAYS_BACK), now)
    sessions = sorted({bert.parse_ts(b["t"]).astimezone(NY).date()
                       for lst in bars.values() for b in lst if in_session(bert.parse_ts(b["t"]))})
    written = []
    for day in sessions[-KEEP_SESSIONS:]:
        path = os.path.join(CHART_DIR, f"{day.isoformat()}.json")
        if (os.path.exists(path) and not overwrite) or not session_done(day, now):
            continue
        out = {"datum": day.isoformat(), "quelle": "Alpaca Market Data (IEX), 15-Minuten-Kerzen",
               "zeitzone": "Europe/Berlin", "linien": "EMA 9 (blau) und EMA 21 (gelb) wie bei Bert",
               "symbole": {}}
        for sym, lst in bars.items():
            # Linien über alle Kerzen bis Ende dieses Tages berechnen (wie Bert), dann nur den Tag zeigen
            upto = [b for b in lst if bert.parse_ts(b["t"]).astimezone(NY).date() <= day]
            if not upto:
                continue
            closes = [float(b["c"]) for b in upto]
            e9, e21 = bert.ema(closes, 9), bert.ema(closes, 21)
            rows, l9, l21 = [], [], []
            for b, a, c in zip(upto, e9, e21):
                t = bert.parse_ts(b["t"])
                if t.astimezone(NY).date() == day and in_session(t):
                    rows.append([t.astimezone(bert.BERLIN).strftime("%H:%M"), round(float(b["o"]), 2),
                                 round(float(b["h"]), 2), round(float(b["l"]), 2), round(float(b["c"]), 2),
                                 int(b.get("v", 0))])
                    l9.append(round(a, 3))
                    l21.append(round(c, 3))
            if rows:
                out["symbole"][sym] = {"kerzen": rows, "ema9": l9, "ema21": l21}
        if out["symbole"]:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
            written.append(day.isoformat())
    print("Chartdaten gespeichert:", ", ".join(written) if written else "nichts Neues")
    return written


if __name__ == "__main__":
    save_missing(overwrite="--neu" in sys.argv)
