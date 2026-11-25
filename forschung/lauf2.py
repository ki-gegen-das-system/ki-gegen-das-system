"""Runde 2: Robustheit Rauschzonen-Momentum (nur Entwicklung 2018–2023)."""
import pandas as pd
from labor import Raster, auswerten
import strategien as S
KORB = {"SPY+QQQ": ["SPY", "QQQ"], "Bert-8": ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA"]}
R = {s: Raster(s) for k in KORB.values() for s in k}
def lauf(name, syms, kf=1.0, **kw):
    tr = pd.concat([S.rauschzone(R[s], n_assets=len(syms), **kw) for s in syms], ignore_index=True)
    return auswerten(tr, name, kosten_faktor=kf)
for k, syms in KORB.items():
    print(f"\n=== {k} ===")
    lauf(f"{k} Basis (lb14 takt6 10:00 VWAP)", syms)
    lauf(f"{k} Kosten x2", syms, kf=2.0)
    lauf(f"{k} Kosten x3", syms, kf=3.0)
    for lb in (10, 20):
        lauf(f"{k} lookback {lb}", syms, lookback=lb)
    for tk in (4, 12):
        lauf(f"{k} takt {tk}", syms, takt=tk)
    lauf(f"{k} Start 10:30", syms, start=11)
    lauf(f"{k} ohne VWAP-Stop", syms, vwap_stop=False)
    lauf(f"{k} Hebel max 2", syms, lev_max=2.0)
    lauf(f"{k} nur Kauf", syms, nur_kauf=True)
