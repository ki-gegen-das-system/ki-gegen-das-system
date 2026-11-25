#!/usr/bin/env python3
"""Krypto rund um die Uhr: Tage = UTC-Tage mit 288 Fünf-Minuten-Kerzen. Kosten: Alpaca-Gebühr 0,25 % (Taker)
+ ca. 2 bp Spread pro Seite."""
import os
import numpy as np
import pandas as pd
from labor import DATEN, auswerten
import strategien as S

GEBUEHR_BP = 25 + 2


class KRaster:
    def __init__(self, sym):
        z = np.load(os.path.join(DATEN, "krypto", f"{sym}.npz"))
        t = z["m5_t"]
        day = t // 86400
        slot = (t % 86400) // 300
        ud = np.unique(day)
        di = np.searchsorted(ud, day)
        for k in ("o", "h", "l", "c", "v", "vw"):
            g = np.full((len(ud), 288), np.nan)
            g[di, slot] = z["m5_" + k]
            setattr(self, k, g)
        self.v = np.nan_to_num(self.v)
        c = self.c
        first = np.where(np.isnan(c[:, 0]), np.nan, c[:, 0])
        for j in range(288):
            if j == 0:
                prev = np.r_[np.nan, np.nan * np.ones(len(ud) - 1)]
                c[:, 0] = np.where(np.isnan(c[:, 0]), self.o[:, 0], c[:, 0])
            else:
                c[:, j] = np.where(np.isnan(c[:, j]), c[:, j - 1], c[:, j])
        # Lücken am Tagesanfang: mit erstem bekannten Kurs füllen
        for k in ("o", "h", "l"):
            g = getattr(self, k)
            setattr(self, k, np.where(np.isnan(g), c, g))
        self.vw = np.where(np.isnan(self.vw), c, self.vw)
        self.c = c
        self.do = self.o[:, 0]
        self.dc = c[:, -1]
        self.dh, self.dl = np.nanmax(self.h, 1), np.nanmin(self.l, 1)
        self.tage = np.array([str(np.datetime64(int(d), "D")) for d in ud])
        self.sym = sym
        self.kosten = GEBUEHR_BP

    @property
    def pc(self):
        return np.r_[np.nan, self.dc[:-1]]


if __name__ == "__main__":
    syms = [f[:-4] for f in sorted(os.listdir(os.path.join(DATEN, "krypto")))]
    R = {s: KRaster(s) for s in syms}
    print("\n--- S9 Krypto rund um die Uhr (Gebühr 0,25 % + Spread je Seite) ---")
    for takt in (6, 12):
        for s in syms:
            auswerten(S.rauschzone(R[s], takt=takt, lev_max=2.0), f"Krypto Rausch {s} takt{takt}")
        auswerten(pd.concat([S.rauschzone(R[s], takt=takt, lev_max=2.0, n_assets=len(syms)) for s in syms]),
                  f"Krypto Rausch alle takt{takt}")
    # Vergleich ohne Gebühr (zeigt, wie viel die Gebühr frisst)
    for s in syms:
        R[s].kosten = 2
    auswerten(pd.concat([S.rauschzone(R[s], takt=6, lev_max=2.0, n_assets=len(syms)) for s in syms]),
              "Krypto Rausch alle takt6 OHNE Gebühr")
