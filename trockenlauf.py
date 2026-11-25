#!/usr/bin/env python3
"""Trockenlauf Bert 2.0: holt die ECHTEN Kurse von heute und zeigt, was die Checkliste gemacht HÄTTE.
Keine Orders, keine Dateien. Prüft, ob Datenabruf und Rechnung live funktionieren."""
from datetime import datetime, timezone
import bert
import strategie

now = datetime.now(timezone.utc)
acc = bert.call("GET", bert.API, "/v2/account")
print("Short erlaubt (Konto):", acc.get("shorting_enabled"), "| Multiplikator:", acc.get("multiplier"))
for s in bert.SYMBOLS:
    a = bert.call("GET", bert.API, f"/v2/assets/{s}")
    print(f"  {s}: shortable={a.get('shortable')} easy_to_borrow={a.get('easy_to_borrow')}")
data = bert.get_bars5(bert.SYMBOLS, now)
today = max(b["d"] for b in data["SPY"])
spy = {(b["d"], b["hm"]): b for b in data["SPY"]}
print(f"\nKerzen geladen: { {s: len(v) for s, v in data.items()} } | Handelstag {today}")
for s in bert.SYMBOLS:
    bars = [b for b in data[s] if b["d"] == today]
    if not bars:
        continue
    last = bars[-1]
    print(f"\n{s}: {len(bars)} Kerzen heute, letzte {last['hm']} Kurs {last['c']:.2f} VWAP {last['vwap']:.2f} "
          f"RSI {last['rsi']:.0f} ATR {last['atr']:.2f} rVol {last['rvol']} Spanne {last.get('or_lo')}–{last.get('or_hi')}")
    for b in bars:
        side, pts = strategie.signal(b, spy.get((b["d"], b["hm"])), True)
        if side:
            stop, target, risk, qty = strategie.plan(side, b["c"], b)
            print(f"  -> {b['hm']} {side.upper()} {qty} Stück zu ~{b['c']:.2f}, Stop {stop:.2f}, Ziel {target:.2f}  "
                  f"[{' | '.join(t for _, _, t in pts)}]")
            break  # nur der erste Trade pro Aktie und Tag
