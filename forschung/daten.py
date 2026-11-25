#!/usr/bin/env python3
"""
Lädt historische Kursdaten für die Strategie-Forschung (Bert 3.0). Nicht für den Live-Betrieb.
Läuft auf GitHub (Workflow „Forschung: Daten laden“), Ergebnis als Artefakt (npz-Dateien).

  python3 forschung/daten.py kern      – 5-Min-Kerzen (SIP, inkl. vor-/nachbörslich) + Tageskerzen für
                                         ~48 Aktien/ETFs ab 2018, dazu Krypto (BTC, ETH, SOL) ab 2021
  python3 forschung/daten.py scanner   – „Stocks in Play“: Tageskerzen aller US-Aktien, Eröffnungskerzen
                                         (9:30–9:45 New York) der Kandidaten, Intraday der Top 30 nach
                                         relativem Volumen (1-Min bis 11:00, 5-Min ganzer Tag)
Kein echtes Geld, keine Orders – nur Kursdaten.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import date, datetime, time as dtime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

KEY, SECRET = os.environ.get("ALPACA_API_KEY", ""), os.environ.get("ALPACA_SECRET_KEY", "")
DATA, API = "https://data.alpaca.markets", "https://paper-api.alpaca.markets"
OUT = os.environ.get("OUT", "forschung_daten")
NY = ZoneInfo("America/New_York")
START = os.environ.get("START", "2018-01-01")
END = os.environ.get("ENDE", "") or (datetime.now(timezone.utc) - timedelta(minutes=20)).strftime("%Y-%m-%d")
MAX_PER_MIN = int(os.environ.get("MAX_PER_MIN", "170"))   # Alpaca erlaubt 200/Min.

KERN = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "SMH", "TLT", "GLD",
        "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "GOOGL", "AMD", "NFLX", "AVGO", "PLTR", "COIN", "MU",
        "BA", "JPM", "XOM", "UBER", "DIS", "INTC", "CRM", "ORCL", "ADBE", "QCOM", "PYPL", "SHOP", "MSTR",
        "SMCI", "BAC", "WMT", "COST", "CVX", "UNH", "LLY", "V", "TQQQ"]
KRYPTO = ["BTC/USD", "ETH/USD", "SOL/USD"]

_calls = deque()
stats = {"calls": 0, "retries": 0}


def call(base, path, params=None):
    url = base + path + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(12):
        while True:
            t = time.time()
            while _calls and t - _calls[0] > 60:
                _calls.popleft()
            if len(_calls) < MAX_PER_MIN:
                break
            time.sleep(60.05 - (t - _calls[0]))
        _calls.append(time.time())
        stats["calls"] += 1
        req = urllib.request.Request(url, headers={"APCA-API-KEY-ID": KEY, "APCA-API-SECRET-KEY": SECRET})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                stats["retries"] += 1
                time.sleep(min(60, 2 ** attempt))
                continue
            raise RuntimeError(f"HTTP {e.code} {url[:250]}: {e.read()[:300]!r}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            stats["retries"] += 1
            time.sleep(min(60, 2 ** attempt))
    raise RuntimeError("zu viele Fehler: " + url[:250])


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ny_dt(d, hh, mm):
    return datetime.combine(d, dtime(hh, mm), tzinfo=NY)


def bars(symbols, timeframe, start, end, feed="sip", crypto=False):
    """Alle Kerzen (mit Seiten) -> {symbol: Liste von Dicts}."""
    out, token = {}, None
    while True:
        p = {"symbols": ",".join(symbols), "timeframe": timeframe, "start": start, "end": end,
             "limit": 10000, "sort": "asc"}
        if not crypto:
            p.update(feed=feed, adjustment="raw")
        if token:
            p["page_token"] = token
        r = call(DATA, "/v1beta3/crypto/us/bars" if crypto else "/v2/stocks/bars", p) or {}
        for s, lst in (r.get("bars") or {}).items():
            out.setdefault(s, []).extend(lst)
        token = r.get("next_page_token")
        if not token:
            return out


def to_arrays(lst):
    t = np.array([b["t"][:19] for b in lst], dtype="datetime64[s]").astype(np.int64)
    f = lambda k, dt=np.float64: np.array([b.get(k, 0) or 0 for b in lst], dtype=dt)
    return dict(t=t, o=f("o"), h=f("h"), l=f("l"), c=f("c"), v=f("v"), vw=f("vw"), n=f("n", np.int64))


def kern():
    os.makedirs(os.path.join(OUT, "kern"), exist_ok=True)
    start, end = iso(ny_dt(date.fromisoformat(START), 0, 0)), iso(ny_dt(date.fromisoformat(END), 23, 59))
    for s in KERN:
        t0 = time.time()
        d5 = bars([s], "5Min", start, end).get(s, [])
        d1 = bars([s], "1Day", start, end).get(s, [])
        if not d5:
            print(f"{s}: keine Daten")
            continue
        a5, a1 = to_arrays(d5), to_arrays(d1)
        np.savez_compressed(os.path.join(OUT, "kern", f"{s}.npz"),
                            **{f"m5_{k}": v for k, v in a5.items()}, **{f"d_{k}": v for k, v in a1.items()})
        print(f"{s}: {len(d5)} 5-Min-Kerzen, {len(d1)} Tage, ab {d5[0]['t'][:10]} ({time.time() - t0:.0f}s, "
              f"Aufrufe {stats['calls']})", flush=True)
    os.makedirs(os.path.join(OUT, "krypto"), exist_ok=True)
    for s in KRYPTO:
        d5 = bars([s], "5Min", "2021-01-01T00:00:00Z", end, crypto=True).get(s, [])
        if d5:
            np.savez_compressed(os.path.join(OUT, "krypto", s.replace("/", "") + ".npz"),
                                **{f"m5_{k}": v for k, v in to_arrays(d5).items()})
        print(f"{s}: {len(d5)} 5-Min-Kerzen", flush=True)


def scanner():
    """Stocks in Play wie bei Zarattini/Barbon/Aziz (2024): Preis > 5 $, Ø-Volumen (14 T.) > 1 Mio.,
    ATR (14 T.) > 0,50 $; relatives Volumen der ersten 5 Minuten vs. Ø der letzten 14 Tage."""
    os.makedirs(OUT, exist_ok=True)
    assets = []
    for status in ("active", "inactive"):
        assets += call(API, "/v2/assets", {"status": status, "asset_class": "us_equity"}) or []
    syms = sorted({a["symbol"] for a in assets
                   if a.get("exchange") in ("NYSE", "NASDAQ", "ARCA", "AMEX", "BATS")
                   and re.fullmatch(r"[A-Z]{1,5}", a["symbol"])})
    sym_id = {s: i for i, s in enumerate(syms)}
    print(f"{len(syms)} Symbole", flush=True)
    # 1) Tageskerzen aller Symbole
    d_start = iso(ny_dt(date.fromisoformat(START) - timedelta(days=40), 0, 0))
    d_end = iso(ny_dt(date.fromisoformat(END), 23, 59))
    daily = {}
    for i in range(0, len(syms), 200):
        for s, lst in bars(syms[i:i + 200], "1Day", d_start, d_end).items():
            if len(lst) < 20:
                continue
            a = to_arrays(lst)
            daily[s] = dict(d=a["t"] // 86400, o=a["o"], h=a["h"], l=a["l"], c=a["c"], v=a["v"])
        print(f"Tageskerzen: {min(i + 200, len(syms))}/{len(syms)} Symbole, {len(daily)} mit Daten, "
              f"Aufrufe {stats['calls']}", flush=True)
    day0 = (date.fromisoformat(START) - date(1970, 1, 1)).days
    cal = [int(d) for d in sorted(set(daily["SPY"]["d"].tolist())) if d >= day0]
    # Kandidaten je Tag (Kennzahlen nur aus Vortagen -> keine Zukunftsinfo)
    parts = []
    for s, a in daily.items():
        c, h, l, v = a["c"], a["h"], a["l"], a["v"]
        if len(c) < 16:
            continue
        pc = np.r_[c[0], c[:-1]]
        tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
        k = 14
        atr = np.convolve(tr, np.ones(k) / k, "full")[:len(tr)]
        av = np.convolve(v, np.ones(k) / k, "full")[:len(v)]
        j = np.arange(k + 1, len(c))
        p_, at_, av_ = c[j - 1], atr[j - 1], av[j - 1]
        ok = (p_ > 5) & (av_ > 1e6) & (at_ > 0.5) & (a["d"][j] >= day0)
        if ok.any():
            parts.append(np.column_stack([a["d"][j][ok], np.full(ok.sum(), sym_id[s]), p_[ok], at_[ok], av_[ok]]))
        a.update(atr=atr, av=av)
    cand = np.concatenate(parts)
    cand = cand[np.argsort(cand[:, 0], kind="stable")]
    print(f"Kandidaten: {len(cand)} Symbol-Tage, Median pro Tag "
          f"{int(np.median(np.bincount(cand[:, 0].astype(int) - day0)[np.bincount(cand[:, 0].astype(int) - day0) > 0]))}",
          flush=True)
    # 2) erste 5-Min-Kerze (9:30) aller Kandidaten, 3) Intraday der Top 30 nach relativem Volumen
    hist = {}
    open_parts, m1_parts, m5_parts = [], [], []
    for n_day, d in enumerate(cal):
        day = date(1970, 1, 1) + timedelta(days=d)
        lo_i, hi_i = np.searchsorted(cand[:, 0], d, "left"), np.searchsorted(cand[:, 0], d, "right")
        rows = cand[lo_i:hi_i]
        cs = [syms[int(x)] for x in rows[:, 1]]
        t930 = iso(ny_dt(day, 9, 30))
        ob = {}
        for i in range(0, len(cs), 400):
            ob.update(bars(cs[i:i + 400], "5Min", t930, iso(ny_dt(day, 9, 30) + timedelta(seconds=299))))
        out = np.full((len(cs), 12), np.nan)
        scored = []
        for r, (s, row) in enumerate(zip(cs, rows)):
            first = [b for b in ob.get(s, []) if b["t"][:19] == t930[:19]]
            v0 = float(first[0]["v"]) if first else 0.0
            h_ = hist.setdefault(s, deque(maxlen=14))
            rv = v0 / (sum(h_) / len(h_)) if len(h_) >= 5 and sum(h_) > 0 else np.nan
            h_.append(v0)
            out[r, :5] = row
            if first:
                b = first[0]
                out[r, 5:10] = (b["o"], b["h"], b["l"], b["c"], b["v"])
            out[r, 10] = rv
            out[r, 11] = n_day
            if first and rv == rv:
                scored.append((rv, s))
        open_parts.append(out)
        top = [s for _, s in sorted(scored, reverse=True)[:30]]
        for tf, end_hm, store, k in (("1Min", (10, 29), m1_parts, 20), ("5Min", (15, 55), m5_parts, 30)):
            if not top[:k]:
                continue
            got = bars(top[:k], tf, t930, iso(ny_dt(day, *end_hm)))
            arr = []
            for s, lst in got.items():
                a = to_arrays(lst)
                arr.append(np.column_stack([np.full(len(lst), d), np.full(len(lst), sym_id[s]), a["t"],
                                            a["o"], a["h"], a["l"], a["c"], a["v"], a["vw"]]))
            if arr:
                store.append(np.concatenate(arr))
        if n_day % 50 == 0:
            print(f"{day}: {len(cs)} Kandidaten, Top 5: {top[:5]} | Aufrufe {stats['calls']}, "
                  f"Wiederholungen {stats['retries']}", flush=True)
    m1 = np.concatenate(m1_parts) if m1_parts else np.zeros((0, 9))
    m5 = np.concatenate(m5_parts) if m5_parts else np.zeros((0, 9))
    np.savez_compressed(os.path.join(OUT, "scanner.npz"), syms=np.array(syms),
                        open=np.concatenate(open_parts).astype(np.float64),
                        m1_meta=m1[:, :3].astype(np.int64), m1=m1[:, 3:].astype(np.float32),
                        m5_meta=m5[:, :3].astype(np.int64), m5=m5[:, 3:].astype(np.float32))
    # Tageskerzen (nur Symbole, die je Kandidat waren) für ATR, Gaps, Folgetage
    used = set(int(x) for x in np.unique(cand[:, 1]))
    dl = [np.column_stack([a["d"], np.full(len(a["d"]), sym_id[s]), a["o"], a["h"], a["l"], a["c"], a["v"]])
          for s, a in daily.items() if sym_id[s] in used or s in KERN]
    np.savez_compressed(os.path.join(OUT, "scanner_tage.npz"), daily=np.concatenate(dl))
    print(f"fertig: Eröffnungskerzen {sum(len(x) for x in open_parts)}, 1-Min {len(m1)}, 5-Min {len(m5)}, "
          f"Aufrufe {stats['calls']}", flush=True)


if __name__ == "__main__":
    {"kern": kern, "scanner": scanner}[sys.argv[1]]()
