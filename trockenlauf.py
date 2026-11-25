#!/usr/bin/env python3
"""
Probelauf Bert 2.0: rechnet mit den ECHTEN 5-Min-Kerzen eines Handelstags nach, was Bert 2.0 nach seinen
Regeln (strategie.py) gemacht HÄTTE – mit demselben Simulator wie der Backtest (backtest.py,
0,02 % Kursabweichung je Kauf/Verkauf). Keine Orders, kein echtes Geld.

Ergebnis (vollständig erst nach Börsenschluss):
  data/trockenlauf/<Tag>_trades.csv      – wie bert_trades.csv (Kauf/Short/Verkauf/Eindecken)
  data/trockenlauf/<Tag>_checkliste.csv  – wie bert_checkliste.csv (erfüllte und fast erfüllte Checklisten)
  data/trockenlauf/<Tag>.json            – Zusammenfassung
Ab Bert 2.0 ist das die Gegenprobe: echte Trades und Probelauf sollten fast gleich sein.
Aufruf: python3 trockenlauf.py [JJJJ-MM-TT]   (ohne Datum: letzter Handelstag)
"""
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import backtest
import bert
import strategie

OUT = os.path.join(bert.DATA_DIR, "trockenlauf")
TRADES_HEADER = ["zeit", "symbol", "aktion", "stueck", "preis_usd", "gewinn_usd", "gewinn_prozent"]


def berlin(day, hm, plus_min=0):
    dt = datetime.strptime(f"{day} {hm}", "%Y-%m-%d %H:%M").replace(tzinfo=strategie.NY)
    return (dt + timedelta(minutes=plus_min)).astimezone(bert.BERLIN).strftime("%Y-%m-%d %H:%M")


def ny_plus(hm, minutes):
    h, m = map(int, hm.split(":"))
    t = h * 60 + m + minutes
    return f"{t // 60:02d}:{t % 60:02d}"


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    now = datetime.now(timezone.utc)
    acc = bert.call("GET", bert.API, "/v2/account")
    print("Short erlaubt (Konto):", acc.get("shorting_enabled"))
    data = bert.get_bars5(bert.SYMBOLS, now)
    days = sorted({b["d"] for b in data["SPY"]})
    day = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else days[-1]
    if day not in days:
        raise SystemExit(f"Keine Kerzen für {day} (vorhanden: {days[0]} bis {days[-1]})")
    spy_day = [b for b in data["SPY"] if b["d"] == day]
    fertig = spy_day[-1]["hm"] >= "15:55"
    print(f"Handelstag {day}: {len(spy_day)} Kerzen, {'vollständig' if fertig else 'noch nicht fertig'}")

    sim, _ = backtest.run_days(data, bert.SYMBOLS,
                               lambda s, i, b, ctx: backtest.v2_signal(s, i, b, ctx, True), mode="v2")
    sim = [t for t in sim if t["tag"] == day]

    rows = []
    for t in sim:
        long = t["seite"] == "long"
        sgn = 1 if long else -1
        pct = (t["ausstieg"] / t["einstieg"] - 1) * 100 * sgn
        rows.append([berlin(day, t["ein"]), t["symbol"], "Kauf" if long else "Short", t["stueck"],
                     f"{t['einstieg']:.2f}", "", ""])
        rows.append([berlin(day, t["aus"]), t["symbol"], "Verkauf" if long else "Eindecken", t["stueck"],
                     f"{t['ausstieg']:.2f}", f"{t['gewinn']:.2f}", f"{pct:.2f}"])
    rows.sort(key=lambda r: r[0])

    spy = {(b["d"], b["hm"]): b for b in data["SPY"]}
    entries = {(t["symbol"], t["ein"]): t for t in sim}
    first_entry = {}
    for t in sim:
        first_entry.setdefault(t["symbol"], t["ein"])
    checks = []
    for sym in bert.SYMBOLS:
        for b in [x for x in data[sym] if x["d"] == day]:
            side, pts = strategie.signal(b, spy.get((b["d"], b["hm"])), True)
            n_ok = sum(1 for k, ok, _ in pts if k != "seite" and ok)
            if side:
                nxt = ny_plus(b["hm"], 5)
                if (sym, nxt) in entries:
                    decision = "KAUF" if side == "long" else "SHORT"
                elif sym in first_entry and first_entry[sym] < nxt:
                    decision = "erfüllt – heute schon gehandelt"
                else:
                    decision = "erfüllt – schon 3 Positionen oder Tageslimit"
            elif n_ok >= 3:
                side = next((txt for k, _, txt in pts if k == "seite"), "")
                decision = f"{n_ok}/5 – kein Trade"
            else:
                continue
            vals = {k: ("ja" if ok else "nein") for k, ok, _ in pts if k != "seite"}
            checks.append([berlin(day, b["hm"], 5), sym, side, vals.get("markt", ""), vals.get("ausbruch", ""),
                           vals.get("volumen", ""), vals.get("trend", ""), vals.get("rsi", ""), n_ok, decision,
                           " | ".join(txt for k, _, txt in pts if k != "seite")])
    checks.sort(key=lambda r: (r[0], r[1]))

    os.makedirs(OUT, exist_ok=True)
    write_csv(os.path.join(OUT, f"{day}_trades.csv"), TRADES_HEADER, rows)
    write_csv(os.path.join(OUT, f"{day}_checkliste.csv"), bert.CHECK_HEADER, checks)
    summe = round(sum(t["gewinn"] for t in sim), 2)
    info = {"datum": day, "vollstaendig": fertig, "stand_kerze_ny": spy_day[-1]["hm"],
            "hinweis": "PROBELAUF – keine echten Trades. So hätte Bert 2.0 nach seinen Regeln (strategie.py) mit "
                       "den echten Kursen gehandelt. Simulator wie im Backtest (backtest.py), 0,02 % "
                       "Kursabweichung je Kauf/Verkauf.",
            "trades": [{**t, "ein_berlin": berlin(day, t["ein"]), "aus_berlin": berlin(day, t["aus"])} for t in sim],
            "summe_usd": summe, "checklisten_erfuellt": sum(1 for c in checks if c[8] == 5),
            "checklisten_knapp": sum(1 for c in checks if c[8] == 4)}
    with open(os.path.join(OUT, f"{day}.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    print(f"\nPROBELAUF {day} – {len(sim)} Trades, zusammen {summe:+.2f} $")
    for t in sim:
        print(f"  {berlin(day, t['ein'])[11:]}–{berlin(day, t['aus'])[11:]} {t['symbol']:<5} {t['seite']:<5} "
              f"{t['stueck']:>3} Stück {t['einstieg']:.2f} → {t['ausstieg']:.2f} ({t['grund']}) {t['gewinn']:+.2f} $")
    print(f"Checklisten: {info['checklisten_erfuellt']}× 5/5, {info['checklisten_knapp']}× 4/5")


if __name__ == "__main__":
    main()
