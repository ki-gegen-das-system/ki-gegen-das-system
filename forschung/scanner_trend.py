"""Variante: Trend auf Stocks in Play mit VWAP-Stop (Prüfung alle 30 Min. wie bei der Rauschzone)."""
import numpy as np, pandas as pd
from labor import auswerten
from scanner_lab import OPEN, M5, SCHLUSS, SYMS, tag_str
G = {k: g.sort_values("min") for k, g in M5.groupby(["d", "sid"])}
def lauf(top=20, kosten_cent=1.0, kosten_bp=2.0):
    sel = OPEN[(OPEN.rvol >= 1) & (OPEN.pc >= 5)].sort_values(["d", "rvol"], ascending=[True, False]).groupby("d").head(top)
    rows = []
    for x in sel.itertuples():
        g = G.get((x.d, x.sid))
        if g is None or len(g) < 20: continue
        mn, o, h, l, c, v, vw = (g[k].to_numpy() for k in ("min", "o", "h", "l", "c", "v", "vw"))
        vwap = np.cumsum(vw * v) / np.maximum(np.cumsum(v), 1)
        pos, ein = 0, 0.0
        for i in range(len(mn) - 1):
            ende = mn[i] + 5
            if ende % 30 != 0 or ende < 600 or ende > 930: continue
            p = c[i]
            if pos == 1 and p < vwap[i]: rows.append((x.d, x.sid, 1, ein, o[i + 1])); pos = 0
            elif pos == -1 and p > vwap[i]: rows.append((x.d, x.sid, -1, ein, o[i + 1])); pos = 0
            if pos == 0 and ende == 600:
                if p > x.h and p > vwap[i]: pos, ein = 1, o[i + 1]
                elif p < x.l and p < vwap[i]: pos, ein = -1, o[i + 1]
        if pos: rows.append((x.d, x.sid, pos, ein, SCHLUSS.get((x.d, x.sid), c[-1])))
    t = pd.DataFrame(rows, columns=["d", "sid", "seite", "ein", "aus"])
    t["tag"] = [tag_str(d) for d in t.d]; t["sym"] = SYMS[t.sid]
    t["kosten_bp"] = 1e4 * (kosten_cent / 100) / t.ein + kosten_bp
    t["gewicht"] = 4.0 / top
    return t
auswerten(lauf(), "InPlay-Trend 10:00 + VWAP-Stop top20")
auswerten(lauf(kosten_cent=0, kosten_bp=0), "InPlay-Trend ... ohne Kosten")
