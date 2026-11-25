"""ENDTEST: die vorab festgelegten Kandidaten EINMAL auf dem gesperrten Zeitraum 2024-01-01 bis 2026-11-24.
Nichts hieran wird danach noch angepasst."""
import sys
import numpy as np
import pandas as pd
from labor import Raster, auswerten, ENTWICKLUNG, ENDTEST
import strategien as S

KANDIDATEN = {
    "K1 Rauschzone SPY+QQQ": ["SPY", "QQQ"],
    "K2 Rauschzone Berts 8": ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA"],
}
R = {s: Raster(s) for v in KANDIDATEN.values() for s in v}
ergebnis = {}
for name, syms in KANDIDATEN.items():
    tr = pd.concat([S.rauschzone(R[s], n_assets=len(syms)) for s in syms], ignore_index=True)
    tr["tag"] = tr.tag.astype(str)
    print(f"\n=== {name} ===")
    auswerten(tr, "Entwicklung 2018–2023", zeitraum=ENTWICKLUNG)
    auswerten(tr, "ENDTEST 2024–2026", zeitraum=ENDTEST)
    auswerten(tr, "ENDTEST Kosten x2", zeitraum=ENDTEST, kosten_faktor=2)
    tr.to_pickle(f"/home/claude/fl/trades_{name.split()[0]}.pkl")
# Vergleich: SPY kaufen und halten
spy = R["SPY"]
for a, b in (("2018-01-01", "2023-12-31"), ENDTEST):
    i0 = np.searchsorted(spy.tage, a); i1 = np.searchsorted(spy.tage, b, "right") - 1
    print(f"SPY kaufen & halten {a[:4]}–{b[:4]}: {spy.dc[i1] / spy.pc[i0] * 100 - 100:+.1f} %")
for y in range(2018, 2027):
    i = [j for j, t in enumerate(spy.tage) if t.startswith(str(y)) and t <= ENDTEST[1]]
    print(y, f"SPY {spy.dc[i[-1]] / spy.pc[i[0]] * 100 - 100:+.1f} %", end=" | ")
