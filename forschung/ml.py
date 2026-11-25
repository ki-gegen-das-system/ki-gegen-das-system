"""S11: Maschinelles Lernen (Gradient Boosting) – sagt die Rendite der nächsten 30 Min. voraus.
Ehrlicher Test: Training nur auf früheren Jahren, Test auf dem Folgejahr (2020–2023), Kosten wie oben."""
import os, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from labor import Raster, auswerten, kosten_bp
import strategien as S
syms = [f[:-4] for f in sorted(os.listdir(os.environ["DATEN"] + "/kern")) if f[:-4] != "TQQQ"]
R = {s: Raster(s) for s in syms}
spy = R["SPY"]; spy_i = {t: i for i, t in enumerate(spy.tage)}
def sigma(r, lb=14):
    mv = np.abs(r.c / r.do[:, None] - 1); out = np.full_like(mv, np.nan)
    for d in range(lb, len(mv)): out[d] = np.nanmean(mv[d - lb:d], 0)
    return out
SIG = {s: sigma(R[s]) for s in syms}
rows = []
for s in syms:
    r = R[s]; sg = SIG[s]; vw = S.vwap(r); vol = S.vol_tag(r)
    cumv = np.cumsum(r.v, 1); avgc = np.full_like(cumv, np.nan)
    for d in range(14, len(cumv)): avgc[d] = cumv[d - 14:d].mean(0)
    for d in range(15, len(r.tage)):
        j = spy_i.get(r.tage[d])
        if j is None or not np.isfinite(r.pc[d]): continue
        for k in range(5, 66, 6):
            c = r.c[d, k]
            feat = [c / r.do[d] - 1, (c / r.do[d] - 1) / max(sg[d, k], 1e-6), r.do[d] / r.pc[d] - 1,
                    c / r.c[d, k - 1] - 1, c / r.c[d, k - 3] - 1, c / r.c[d, max(k - 6, 0)] - 1,
                    c / vw[d, k] - 1, cumv[d, k] / max(avgc[d, k], 1), vol[d], k,
                    (spy.c[j, k] / spy.do[j] - 1) / max(SIG["SPY"][j, k], 1e-6)]
            ein, aus = r.o[d, k + 1], r.o[d, k + 7]
            rows.append([r.tage[d], s] + feat + [ein, aus])
cols = ["tag", "sym", "r_open", "rausch", "gap", "r5", "r15", "r30", "vwap", "rvol", "vol", "zeit", "spy_rausch", "ein", "aus"]
df = pd.DataFrame(rows, columns=cols).dropna()
df["y"] = (df.aus / df.ein - 1) * 1e4
F = cols[2:13]
alle = []
for testjahr in ("2020", "2021", "2022", "2023"):
    tr = df[df.tag < testjahr]; te = df[df.tag.str[:4] == testjahr].copy()
    m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=200)
    m.fit(tr[F], tr.y.clip(-200, 200))
    te["p"] = m.predict(te[F])
    alle.append(te)
te = pd.concat(alle)
print(f"Korrelation Vorhersage/Ergebnis (2020–2023, nie gesehen): {np.corrcoef(te.p, te.y)[0, 1]:.3f}")
for schwelle in (2, 5, 10):
    sel = te[te.p.abs() > schwelle].copy()
    sel["seite"] = np.sign(sel.p).astype(int)
    sel["gewicht"] = 1 / 8; sel["kosten_bp"] = [kosten_bp(s) for s in sel.sym]
    auswerten(sel, f"ML GBM 30min Schwelle {schwelle}bp", zeitraum=("2020-01-01", "2023-12-31"))
