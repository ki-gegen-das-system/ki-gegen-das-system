#!/usr/bin/env python3
"""
Nachrechnung für Börsen-Bert: „Was wäre, wenn Bert nie geschlafen hätte?“

Spielt Berts Regeln (bert.py, unverändert) mit den ECHTEN Kursen aus data/charts/ nach –
so, als hätte er an jedem Handelstag nach jeder 15-Minuten-Kerze nachgeschaut.
Das sind KEINE echten Trades. Echte Trades stehen nur in data/bert_trades.csv.

Regeln wie in bert.py:
- Kauf: blaue Linie (EMA 9) kreuzt die gelbe (EMA 21) nach oben (in den letzten 2 Kerzen), RSI unter 70,
  nicht in den letzten 90 Minuten, höchstens 4 Aktien gleichzeitig, 2.500 $ pro Kauf (ganze Stück).
- Verkauf: blau unter gelb, −1,5 % (Stop-Loss), +3 % (Gewinnmitnahme), 30 Min. vor Schluss alles.

Vereinfachungen (ehrlich):
- Geprüft wird nur am Ende jeder 15-Min-Kerze (Bert prüft alle 5 Min.), Preis = Schlusskurs der Kerze.
- Linien = die in data/charts gespeicherten (genau wie Bert sie berechnet). Der RSI wird nur aus
  Kerzen der Börsenzeit berechnet (Bert nimmt auch vor-/nachbörsliche Kerzen dazu).
- Kreuzungen über Nacht (zwischen Schluss und erster Kerze) zählen nicht – die vorbörslichen Kerzen
  fehlen in data/charts. Dadurch eher zu wenige als zu viele Käufe.
- Keine Gebühren, kein Schlupf (bei Alpaca-Demo ohnehin fast null).

Aufruf: python3 nachrechnung.py 2026-11-18 2026-11-20
        -> schreibt data/nachrechnung/bert_2026-11-18_bis_2026-11-20.csv (wird im Video gezeigt)
"""
import csv
import glob
import json
import math
import os
import sys

import bert

CHART_DIR = os.path.join(bert.DATA_DIR, "charts")
OUT_DIR = os.path.join(bert.DATA_DIR, "nachrechnung")
HEADER = ["tag", "symbol", "kauf_zeit", "kauf_preis_usd", "stueck", "verkauf_zeit", "verkauf_preis_usd",
          "gewinn_usd", "gewinn_prozent", "verkaufsgrund"]
CLOSE_MIN = 22 * 60  # Börsenschluss 22:00 deutsche Zeit (stimmt für diese Wochen)


def minutes(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def load_series():
    """Alle Kerzen aller Tage hintereinander: {symbol: [(tag, zeit, schluss, ema9, ema21), ...]}"""
    series = {}
    for path in sorted(glob.glob(os.path.join(CHART_DIR, "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        for sym, v in d["symbole"].items():
            for k, e9, e21 in zip(v["kerzen"], v["ema9"], v["ema21"]):
                series.setdefault(sym, []).append((d["datum"], k[0], float(k[4]), e9, e21))
    return series


def simulate(von, bis):
    series = load_series()
    # Zeitachse: alle (tag, zeit) im Zeitraum
    steps = sorted({(b[0], b[1]) for lst in series.values() for b in lst if von <= b[0] <= bis})
    index = {s: {(b[0], b[1]): i for i, b in enumerate(lst)} for s, lst in series.items()}
    cash, positions, trades, rsi_blocked, full_blocked = bert.START_BUDGET, {}, [], 0, 0
    for day, hhmm in steps:
        left = CLOSE_MIN - (minutes(hhmm) + 15)  # Prüfung am Ende der Kerze
        prices = {}
        for s in series:
            i = index[s].get((day, hhmm))
            if i is not None:
                prices[s] = (i, series[s][i][2])
        # 1) Verkaufen
        sold = set()
        for s in list(positions):
            if s not in prices:
                continue
            i, price = prices[s]
            p = positions[s]
            change = price / p["preis"] - 1
            _, _, _, e9, e21 = series[s][i]
            grund = None
            if left <= bert.CLOSE_ALL_MIN:
                grund = "Börsenschluss naht"
            elif change <= bert.STOP_LOSS:
                grund = "Stop-Loss"
            elif change >= bert.TAKE_PROFIT:
                grund = "Gewinnmitnahme"
            elif e9 < e21:
                grund = "blau unter gelb"
            if grund:
                cash += p["stueck"] * price
                gewinn = (price - p["preis"]) * p["stueck"]
                trades.append([day, s, p["zeit"], f"{p['preis']:.2f}", p["stueck"], hhmm_end(hhmm), f"{price:.2f}",
                               f"{gewinn:.2f}", f"{change * 100:.2f}", grund])
                del positions[s]
                sold.add(s)
        # 2) Kaufen
        if left <= bert.NO_NEW_BUYS_MIN:
            continue
        for s in bert.SYMBOLS:
            if s in positions or s in sold or s not in prices:
                continue
            i, price = prices[s]
            if i < 30:
                continue
            lst = series[s]
            e9 = [b[3] for b in lst[i - 2:i + 1]]
            e21 = [b[4] for b in lst[i - 2:i + 1]]
            days = [b[0] for b in lst[i - 2:i + 1]]
            # Kreuzung nur zählen, wenn beide Kerzen vom selben Börsentag sind: Über Nacht fehlen uns die
            # vor-/nachbörslichen Kerzen, die Bert mitrechnet – ob er da gekauft hätte, wissen wir nicht.
            crossed = any(e9[k - 1] <= e21[k - 1] and e9[k] > e21[k] and days[k - 1] == days[k]
                          for k in (2, 1))
            if not (e9[2] > e21[2] and crossed):
                continue
            if bert.rsi([b[2] for b in lst[max(0, i - 200):i + 1]]) >= 70:
                rsi_blocked += 1
                continue
            if len(positions) >= bert.MAX_POSITIONS:
                full_blocked += 1
                continue
            qty = math.floor(min(bert.POSITION_SIZE, cash) / price)
            if qty < 1:
                full_blocked += 1
                continue
            cash -= qty * price
            positions[s] = {"preis": price, "stueck": qty, "zeit": hhmm_end(hhmm)}
    return trades, rsi_blocked, full_blocked


def hhmm_end(hhmm):
    m = minutes(hhmm) + 15
    return f"{m // 60:02d}:{m % 60:02d}"


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    von, bis = sys.argv[1], sys.argv[2]
    trades, rsi_blocked, full_blocked = simulate(von, bis)
    trades.sort(key=lambda t: (t[0], t[2], t[1]))  # nach Kaufzeit
    os.makedirs(OUT_DIR, exist_ok=True)
    out_file = os.path.join(OUT_DIR, f"bert_{von}_bis_{bis}.csv")
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(trades)
    plus = sum(float(t[7]) > 0 for t in trades)
    total = sum(float(t[7]) for t in trades)
    print(f"Nachrechnung {von} bis {bis} (keine echten Trades):")
    for t in trades:
        print(f"  {t[0]} {t[1]:<5} {t[2]}→{t[5]}  {t[3]}→{t[6]} $  {float(t[7]):+8.2f} $ ({float(t[8]):+.2f} %)  {t[9]}")
    print(f"{len(trades)} Trades, {plus} im Plus, Summe {total:+.2f} $ "
          f"({total / bert.START_BUDGET * 100:+.2f} %). RSI-Sperre: {rsi_blocked}×, Depot voll: {full_blocked}×")
    print("Gespeichert:", out_file)


if __name__ == "__main__":
    main()
