#!/usr/bin/env python3
"""
Bert 2.0 – die Checkliste (seit 26.11.2026). Wird von bert.py (live) UND backtest.py (Test) benutzt,
damit beide garantiert dieselben Regeln haben.

Bert kauft (oder geht short), wenn ALLE 5 Punkte passen – geprüft am Ende jeder 5-Minuten-Kerze:
  1. Markt-Ampel: S&P 500 (SPY) über seinem Tages-Durchschnittspreis (VWAP)   (Short: darunter)
  2. Ausbruch:    Kurs schließt über dem Hoch der ersten 30 Minuten           (Short: unter dem Tief)
                  – aber höchstens 0,5 ATR darüber (nicht hinterherlaufen)
  3. Volumen:     mind. 1,5× so viel wie sonst um diese Uhrzeit (Ø der letzten 10 Tage)
  4. Trend:       Kurs über VWAP und schnelle Linie über langsamer             (Short: umgekehrt)
  5. Nicht überhitzt: RSI unter 70                                            (Short: über 30)
Risiko: Stop am Rand der Eröffnungsspanne, höchstens 1 ATR entfernt; Ziel = 2× Risiko;
max. 50 $ Risiko pro Trade, max. 3.000 $ pro Position, 3 Positionen, 1 Trade pro Aktie und Tag,
Tageslimit −150 $, neue Trades nur bis 14:30 New York (20:30 Uhr), um 15:45 New York (21:45 Uhr) alles zu.
"""
import math
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

V2 = dict(
    or_bars=6,            # Eröffnungsspanne = erste 30 Minuten (6 × 5 Min.)
    vol_factor=1.5,       # Volumen ≥ 1,5× des üblichen Volumens um diese Uhrzeit (Ø 10 Tage)
    max_chase_atr=0.5,    # höchstens 0,5 ATR über dem Ausbruchsniveau
    rsi_max=70, rsi_min=30,
    ema_fast=27, ema_slow=63,   # auf 5-Min-Kerzen ≈ Berts Linien (EMA 9/21 auf 15 Min.)
    atr_stop=1.0,
    reward=2.0,
    risk_usd=50.0,
    max_pos_usd=3000.0,
    max_positions=3,
    day_loss_limit=-150.0,
    last_entry="14:30",   # New York
    flat_time="15:45",    # New York
)


def to_session(lst, parse_ts):
    """Nur reguläre Börsenzeit (9:30–16:00 New York) als Kerzen-Dicts (d, hm in New-York-Zeit)."""
    out = []
    for b in lst:
        t = parse_ts(b["t"])
        n = t.astimezone(NY)
        m = n.hour * 60 + n.minute
        if 9 * 60 + 30 <= m < 16 * 60 and n.weekday() < 5:
            out.append({"t": t, "d": n.date().isoformat(), "hm": n.strftime("%H:%M"), "o": float(b["o"]),
                        "h": float(b["h"]), "l": float(b["l"]), "c": float(b["c"]), "v": float(b.get("v", 0))})
    return out


def ema_series(vals, n):
    k, e, out = 2 / (n + 1), None, []
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


def rsi_series(vals, n=14):
    out, ag, al = [50.0] * len(vals), None, None
    for i in range(1, len(vals)):
        d = vals[i] - vals[i - 1]
        g, l = max(d, 0), max(-d, 0)
        if ag is None:
            if i == n:
                diffs = [vals[j] - vals[j - 1] for j in range(1, n + 1)]
                ag = sum(max(x, 0) for x in diffs) / n
                al = sum(max(-x, 0) for x in diffs) / n
            else:
                continue
        else:
            ag = (ag * (n - 1) + g) / n
            al = (al * (n - 1) + l) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def atr_series(bars, n=14):
    out, a = [], None
    for i, b in enumerate(bars):
        pc = bars[i - 1]["c"] if i else b["c"]
        tr = max(b["h"] - b["l"], abs(b["h"] - pc), abs(b["l"] - pc))
        a = tr if a is None else (a * (n - 1) + tr) / n
        out.append(a)
    return out


def enrich(bars):
    """Rechnet alle Werte der Checkliste an jede Kerze: VWAP, Linien, RSI, ATR, relatives Volumen,
    Eröffnungsspanne (or_hi/or_lo, ab Kerze 7 des Tages)."""
    closes = [b["c"] for b in bars]
    ef, es = ema_series(closes, V2["ema_fast"]), ema_series(closes, V2["ema_slow"])
    rs, at = rsi_series(closes), atr_series(bars)
    cum_pv = cum_v = 0.0
    day, hist, today, pos, or_hi, or_lo = None, {}, {}, 0, None, None
    for i, b in enumerate(bars):
        if b["d"] != day:
            for hm, v in today.items():
                hist.setdefault(hm, []).append(v)
                hist[hm] = hist[hm][-10:]
            day, cum_pv, cum_v, today, pos, or_hi, or_lo = b["d"], 0.0, 0.0, {}, 0, None, None
        tp = (b["h"] + b["l"] + b["c"]) / 3
        cum_pv += tp * b["v"]
        cum_v += b["v"]
        b["vwap"] = cum_pv / cum_v if cum_v else b["c"]
        b["ef"], b["es"], b["rsi"], b["atr"] = ef[i], es[i], rs[i], at[i]
        past = hist.get(b["hm"], [])
        b["rvol"] = b["v"] / (sum(past) / len(past)) if len(past) >= 5 and sum(past) > 0 else None
        today[b["hm"]] = b["v"]
        b["pos"] = pos  # Nummer der Kerze im Tag (0 = 9:30)
        if pos < V2["or_bars"]:
            or_hi = b["h"] if or_hi is None else max(or_hi, b["h"])
            or_lo = b["l"] if or_lo is None else min(or_lo, b["l"])
            b["or_hi"] = b["or_lo"] = None
        else:
            b["or_hi"], b["or_lo"] = or_hi, or_lo
        pos += 1
    return bars


def de(x, n=2):
    """Zahl mit deutschem Komma."""
    return f"{x:.{n}f}".replace(".", ",")


def checklist(b, spy, side):
    """Prüft die 5 Punkte für eine Richtung. Gibt (alle_ok, punkte) zurück; punkte = Liste (Name, ok, Text)."""
    if b.get("or_hi") is None or spy is None:
        return False, []
    long = side == "long"
    hi, lo, atr = b["or_hi"], b["or_lo"], b["atr"]
    markt = spy["c"] > spy["vwap"] if long else spy["c"] < spy["vwap"]
    if long:
        ausbruch = b["c"] > hi and b["c"] - hi <= V2["max_chase_atr"] * atr
    else:
        ausbruch = b["c"] < lo and lo - b["c"] <= V2["max_chase_atr"] * atr
    rv = b.get("rvol")
    volumen = rv is not None and rv >= V2["vol_factor"]
    trend = (b["c"] > b["vwap"] and b["ef"] > b["es"]) if long else (b["c"] < b["vwap"] and b["ef"] < b["es"])
    rsi_ok = b["rsi"] < V2["rsi_max"] if long else b["rsi"] > V2["rsi_min"]
    pts = [
        ("markt", markt, f"S&P 500 {'über' if spy['c'] > spy['vwap'] else 'unter'} Tagesdurchschnitt"),
        ("ausbruch", ausbruch, (f"Kurs {de(b['c'])} " + (f"über 30-Min-Hoch {de(hi)}" if long else f"unter 30-Min-Tief {de(lo)}"))
         if (b["c"] > hi if long else b["c"] < lo) else (f"kein Ausbruch (Spanne {de(lo)}–{de(hi)})")),
        ("volumen", volumen, f"Volumen {de(rv, 1)}× normal" if rv is not None else "Volumen unbekannt"),
        ("trend", trend, ("über" if b["c"] > b["vwap"] else "unter") + " Tagesdurchschnitt, Blau "
         + ("über" if b["ef"] > b["es"] else "unter") + " Gelb"),
        ("rsi", rsi_ok, f"RSI {b['rsi']:.0f}"),
    ]
    return all(p[1] for p in pts), pts


def signal(b, spy, shorts=True):
    """('long'|'short', punkte) oder (None, beste_punkte) – nur innerhalb der Einstiegszeit."""
    if b.get("or_hi") is None or b["hm"] > V2["last_entry"]:
        return None, []
    ok_l, p_l = checklist(b, spy, "long")
    if ok_l:
        return "long", p_l
    if shorts:
        ok_s, p_s = checklist(b, spy, "short")
        if ok_s:
            return "short", p_s
        if sum(x[1] for x in p_s) > sum(x[1] for x in p_l):
            return None, [("seite", False, "short")] + p_s
    return None, [("seite", False, "long")] + p_l


def plan(side, entry, b):
    """Stop, Ziel, Risiko pro Aktie und Stückzahl für einen Einstieg zum Preis entry."""
    atr = b["atr"]
    if side == "long":
        stop = max(b["or_lo"], entry - V2["atr_stop"] * atr)
        risk = max(entry - stop, 0.002 * entry)
        stop, target = entry - risk, entry + V2["reward"] * risk
    else:
        stop = min(b["or_hi"], entry + V2["atr_stop"] * atr)
        risk = max(stop - entry, 0.002 * entry)
        stop, target = entry + risk, entry - V2["reward"] * risk
    qty = math.floor(min(V2["risk_usd"] / risk, V2["max_pos_usd"] / entry))
    return stop, target, risk, qty
