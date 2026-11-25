#!/usr/bin/env python3
"""
Backtest: Bert 1.0 (Linien-Kreuzung) gegen Bert 2.0 (Checkliste mit Ausbruch) – auf ECHTEN 5-Minuten-Kerzen.

Wichtig: Alle Einstellungen sind VORHER festgelegt (Standardwerte), nichts wird auf diese Daten optimiert.
Sonst sähe der Test besser aus, als die Strategie in Zukunft wirklich ist.

Läuft auf GitHub Actions (.github/workflows/backtest.yml), lädt Kurse von Alpaca (IEX, kostenlos).
Ergebnis: data/backtest/ergebnis.json, ergebnis.md, tage_<variante>.csv
"""
import csv
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import bert

NY = ZoneInfo("America/New_York")
START = os.environ.get("BT_START") or "2026-05-26"
END = os.environ.get("BT_END") or "2026-11-24"
OUT = os.path.join(bert.DATA_DIR, "backtest", f"{START}_bis_{END}")
BASE = list(bert.SYMBOLS)                       # die 8 bisherigen
EXTRA = ["AMD", "GOOGL", "NFLX", "AVGO", "PLTR", "COIN", "MU", "BA", "JPM", "XOM", "UBER", "DIS"]
CAPITAL = 10_000.0
SLIP = 0.0002                                   # 0,02 % Kursabweichung pro Kauf/Verkauf

# ---------------------------------------------------------------- Bert 2.0: Regeln aus strategie.py (dieselben wie live)
import strategie
from strategie import V2, ema_series, rsi_series, enrich


# ---------------------------------------------------------------- Daten
def fetch(symbols, start, end):
    bars = {s: [] for s in symbols}
    token = None
    while True:
        p = {"symbols": ",".join(symbols), "timeframe": "5Min", "start": start, "end": end, "feed": "iex",
             "limit": 10000, "adjustment": "split", "sort": "asc"}
        if token:
            p["page_token"] = token
        r = bert.call("GET", bert.DATA_API, "/v2/stocks/bars", p) or {}
        for s, lst in (r.get("bars") or {}).items():
            bars.setdefault(s, []).extend(lst)
        token = r.get("next_page_token")
        if not token:
            break
    return bars


def to_session(lst):
    return strategie.to_session(lst, bert.parse_ts)


def by_day(bars):
    days = {}
    for i, b in enumerate(bars):
        days.setdefault(b["d"], []).append(i)
    return days


# ---------------------------------------------------------------- Bert 1.0 (wie bisher)
def agg15(bars):
    """5-Min-Kerzen -> 15-Min-Kerzen; merkt sich den Index der letzten 5-Min-Kerze jeder 15-Min-Kerze."""
    res, key = [], None
    for i, b in enumerate(bars):
        h, m = map(int, b["hm"].split(":"))
        k = (b["d"], h, m // 15)
        if k != key:
            res.append({"end_i": i, "c": b["c"]})
            key = k
        else:
            res[-1]["end_i"], res[-1]["c"] = i, b["c"]
    return res


def sim_v1(data, symbols):
    """Bert 1.0: Kreuzung EMA9/21 (15 Min.) + RSI<70, Stop −1,5 %, Ziel +3 %, Gegen-Kreuzung, 21:30 alles raus."""
    sig = {}
    for s in symbols:
        bars = data[s]
        b15 = agg15(bars)
        closes = [x["c"] for x in b15]
        e9, e21, r = ema_series(closes, 9), ema_series(closes, 21), rsi_series(closes)
        buy, sell = set(), set()
        for k in range(2, len(b15)):
            if b15[k]["end_i"] >= len(bars):
                continue
            up = any(e9[j - 1] <= e21[j - 1] and e9[j] > e21[j] for j in (k, k - 1))
            if e9[k] > e21[k] and up and r[k] < 70:
                buy.add(b15[k]["end_i"])
            if e9[k] < e21[k]:
                sell.add(b15[k]["end_i"])
        sig[s] = (buy, sell)
    return run_days(data, symbols, lambda s, i, b, ctx: "buy" if i in sig[s][0] else None,
                    v1_exit=sig, mode="v1")


# ---------------------------------------------------------------- Bert 2.0
def v2_signal(s, i, b, ctx, shorts):
    side, _ = strategie.signal(b, ctx["spy"].get((b["d"], b["hm"])), shorts)
    return side


def sim_v2(data, symbols, shorts):
    return run_days(data, symbols, lambda s, i, b, ctx: v2_signal(s, i, b, ctx, shorts), mode="v2")


# ---------------------------------------------------------------- gemeinsamer Tages-Simulator
def run_days(data, symbols, signal, mode, v1_exit=None):
    days_sym = {s: by_day(data[s]) for s in symbols}
    spy_map = {(b["d"], b["hm"]): b for b in data["SPY"]}
    ctx = {"data": data, "days": days_sym, "spy": spy_map}
    all_days = sorted({d for s in symbols for d in days_sym[s]})
    trades, daily = [], []
    for d in all_days:
        # Zeitachse des Tages: alle 5-Min-Zeitpunkte
        times = sorted({data[s][i]["hm"] for s in symbols if d in days_sym[s] for i in days_sym[s][d]})
        idx_at = {s: {data[s][i]["hm"]: i for i in days_sym[s].get(d, [])} for s in symbols}
        open_pos, done_today, realized = {}, set(), 0.0
        for hm in times:
            # 1) offene Positionen prüfen (an dieser Kerze)
            for s in list(open_pos):
                i = idx_at[s].get(hm)
                if i is None:
                    continue
                b, p = data[s][i], open_pos[s]
                exit_px, why = None, None
                if mode == "v2":
                    if hm >= V2["flat_time"]:
                        exit_px, why = b["o"], "Börsenschluss"
                    elif p["side"] == "long":
                        if b["l"] <= p["stop"]:
                            exit_px, why = min(p["stop"], b["o"]), "Stop-Loss"
                        elif b["h"] >= p["target"]:
                            exit_px, why = max(p["target"], b["o"]), "Gewinnziel"
                    else:
                        if b["h"] >= p["stop"]:
                            exit_px, why = max(p["stop"], b["o"]), "Stop-Loss"
                        elif b["l"] <= p["target"]:
                            exit_px, why = min(p["target"], b["o"]), "Gewinnziel"
                else:  # v1: Prüfung am Kerzenende wie bei Bert (alle 5 Min.)
                    ch = b["c"] / p["entry"] - 1
                    if hm >= "15:30":
                        exit_px, why = b["c"], "Börsenschluss"
                    elif ch <= -0.015:
                        exit_px, why = b["c"], "Stop-Loss"
                    elif ch >= 0.03:
                        exit_px, why = b["c"], "Gewinnziel"
                    elif i in v1_exit[s][1]:
                        exit_px, why = b["c"], "Gegen-Kreuzung"
                if exit_px is not None:
                    sgn = 1 if p["side"] == "long" else -1
                    exit_px *= (1 - SLIP * sgn)
                    pnl = (exit_px - p["entry"]) * p["qty"] * sgn
                    realized += pnl
                    trades.append({"tag": d, "symbol": s, "seite": p["side"], "ein": p["t"], "aus": hm,
                                   "einstieg": round(p["entry"], 2), "ausstieg": round(exit_px, 2),
                                   "stueck": p["qty"], "gewinn": round(pnl, 2), "grund": why})
                    del open_pos[s]
            # 2) neue Signale (Einstieg zum Eröffnungskurs der NÄCHSTEN Kerze)
            limit_pos = V2["max_positions"] if mode == "v2" else 4
            if mode == "v2" and realized <= V2["day_loss_limit"]:
                continue
            if mode == "v1" and hm > "14:30":
                continue
            for s in symbols:
                if s in open_pos or len(open_pos) >= limit_pos:
                    continue
                if mode == "v2" and s in done_today:
                    continue
                i = idx_at[s].get(hm)
                if i is None or i + 1 >= len(data[s]) or data[s][i + 1]["d"] != d:
                    continue
                b = data[s][i]
                sig = signal(s, i, b, ctx)
                if not sig:
                    continue
                nxt = data[s][i + 1]
                if mode == "v1":
                    entry = nxt["o"] * (1 + SLIP)
                    qty = math.floor(2500 / entry)
                    if qty < 1:
                        continue
                    open_pos[s] = {"side": "long", "entry": entry, "qty": qty, "t": nxt["hm"]}
                else:
                    side = sig
                    sgn = 1 if side == "long" else -1
                    entry = nxt["o"] * (1 + SLIP * sgn)
                    stop, target, risk, qty = strategie.plan(side, entry, b)
                    if qty < 1:
                        continue
                    open_pos[s] = {"side": side, "entry": entry, "qty": qty, "t": nxt["hm"], "stop": stop,
                                   "target": target}
                    done_today.add(s)
        # Sicherheitsnetz: was jetzt noch offen ist, zum letzten Kurs schließen
        for s, p in list(open_pos.items()):
            last = data[s][days_sym[s][d][-1]]
            sgn = 1 if p["side"] == "long" else -1
            px = last["c"] * (1 - SLIP * sgn)
            pnl = (px - p["entry"]) * p["qty"] * sgn
            realized += pnl
            trades.append({"tag": d, "symbol": s, "seite": p["side"], "ein": p["t"], "aus": last["hm"],
                           "einstieg": round(p["entry"], 2), "ausstieg": round(px, 2), "stueck": p["qty"],
                           "gewinn": round(pnl, 2), "grund": "Tagesende"})
        daily.append({"tag": d, "gewinn": round(realized, 2)})
    return trades, daily


# ---------------------------------------------------------------- Auswertung
def stats(trades, daily):
    eq, peak, mdd = CAPITAL, CAPITAL, 0.0
    for x in daily:
        eq += x["gewinn"]
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
    wins = [t["gewinn"] for t in trades if t["gewinn"] > 0]
    losses = [t["gewinn"] for t in trades if t["gewinn"] <= 0]
    total = sum(t["gewinn"] for t in trades)
    months = {}
    for x in daily:
        months[x["tag"][:7]] = round(months.get(x["tag"][:7], 0) + x["gewinn"], 2)
    reasons = {}
    for t in trades:
        reasons[t["grund"]] = reasons.get(t["grund"], 0) + 1
    return {
        "gewinn_usd": round(total, 2), "rendite_prozent": round(total / CAPITAL * 100, 2),
        "trades": len(trades), "trefferquote_prozent": round(len(wins) / len(trades) * 100, 1) if trades else 0,
        "schnitt_gewinner": round(sum(wins) / len(wins), 2) if wins else 0,
        "schnitt_verlierer": round(sum(losses) / len(losses), 2) if losses else 0,
        "profitfaktor": round(sum(wins) / -sum(losses), 2) if losses and sum(losses) < 0 else None,
        "max_rueckgang_usd": round(mdd, 2), "tage": len(daily),
        "tage_im_plus": sum(1 for x in daily if x["gewinn"] > 0),
        "tage_im_minus": sum(1 for x in daily if x["gewinn"] < 0),
        "bester_tag": max(daily, key=lambda x: x["gewinn"]) if daily else None,
        "schlechtester_tag": min(daily, key=lambda x: x["gewinn"]) if daily else None,
        "monate": months, "ausstiegsgruende": reasons,
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    symbols_all = sorted(set(BASE + EXTRA + ["SPY"]))
    print(f"Lade 5-Min-Kerzen {START} bis {END} für {len(symbols_all)} Werte …", flush=True)
    raw = fetch(symbols_all, START + "T00:00:00Z", (datetime.fromisoformat(END) + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z"))
    data = {s: enrich(to_session(raw.get(s, []))) for s in symbols_all}
    print({s: len(v) for s, v in data.items()}, flush=True)
    spy = data["SPY"]
    spy_ret = (spy[-1]["c"] / spy[0]["o"] - 1) * 100 if spy else 0
    variants = {
        "bert_1_0": ("Bert 1.0 (bisher): Linien-Kreuzung, 8 Aktien", lambda: sim_v1(data, BASE)),
        "bert_2_0_long_8": ("Bert 2.0: Checkliste, nur Kauf, 8 Aktien", lambda: sim_v2(data, BASE, False)),
        "bert_2_0_short_8": ("Bert 2.0: Checkliste, Kauf + Short, 8 Aktien", lambda: sim_v2(data, BASE, True)),
        "bert_2_0_long_20": ("Bert 2.0: Checkliste, nur Kauf, 20 Aktien", lambda: sim_v2(data, BASE + EXTRA, False)),
        "bert_2_0_short_20": ("Bert 2.0: Checkliste, Kauf + Short, 20 Aktien", lambda: sim_v2(data, BASE + EXTRA, True)),
    }
    result = {"zeitraum": [START, END], "spy_kursveraenderung_prozent": round(spy_ret, 2),
              "einstellungen_bert_2_0": V2, "kursabweichung_pro_seite": SLIP, "varianten": {}}
    for key, (label, fn) in variants.items():
        trades, daily = fn()
        st = stats(trades, daily)
        st["name"] = label
        result["varianten"][key] = st
        with open(os.path.join(OUT, f"tage_{key}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tag", "gewinn_usd", "kontostand_usd"])
            eq = CAPITAL
            for x in daily:
                eq += x["gewinn"]
                w.writerow([x["tag"], x["gewinn"], round(eq, 2)])
        with open(os.path.join(OUT, f"trades_{key}.csv"), "w", newline="", encoding="utf-8") as f:
            if trades:
                w = csv.DictWriter(f, fieldnames=list(trades[0].keys()))
                w.writeheader()
                w.writerows(trades)
        print(f"{label}: {st['gewinn_usd']:+.2f} $ ({st['rendite_prozent']:+.2f} %), {st['trades']} Trades, "
              f"Treffer {st['trefferquote_prozent']} %, PF {st['profitfaktor']}, max. Rückgang {st['max_rueckgang_usd']} $",
              flush=True)
    with open(os.path.join(OUT, "ergebnis.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    lines = [f"# Backtest {START} bis {END}", "", f"SPY im Zeitraum: {spy_ret:+.2f} %", "",
             "| Variante | Gewinn | Trades | Trefferquote | Profitfaktor | max. Rückgang | Tage +/− |",
             "|---|---|---|---|---|---|---|"]
    for k, st in result["varianten"].items():
        lines.append(f"| {st['name']} | {st['gewinn_usd']:+.2f} $ ({st['rendite_prozent']:+.2f} %) | {st['trades']} | "
                     f"{st['trefferquote_prozent']} % | {st['profitfaktor']} | {st['max_rueckgang_usd']} $ | "
                     f"{st['tage_im_plus']}/{st['tage_im_minus']} |")
    open(os.path.join(OUT, "ergebnis.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
