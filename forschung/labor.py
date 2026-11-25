#!/usr/bin/env python3
"""
Strategie-Labor für Bert 3.0 (Forschung, keine Orders).
Lädt die Kern-Daten (forschung/daten.py kern) in Raster: Tage x 78 Fünf-Minuten-Kerzen (9:30–16:00 New York)
und testet Strategien mit Kosten. Entwicklung: 2018–2023. Endtest (erst ganz am Schluss): 2024–2026.
"""
import os
import numpy as np
import pandas as pd

DATEN = os.environ.get("DATEN", "/home/claude/fl/daten")
CACHE = os.environ.get("CACHE", "/home/claude/fl/cache")
SLOTS = 78
ETF = {"SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "SMH", "TLT", "GLD", "TQQQ"}
WILD = {"TSLA", "AMD", "PLTR", "COIN", "MSTR", "SMCI", "SHOP", "MU", "NVDA"}


def kosten_bp(sym):
    """Kosten pro Kauf ODER Verkauf in Basispunkten (0,01 %): halber Spread + Schlupf, eher vorsichtig."""
    return 1.0 if sym in ETF else 3.0 if sym in WILD else 2.0


class Raster:
    """Regulärer Handel als Raster: o/h/l/c/v/vw[tag, slot], dazu offizielle Tageskerzen."""

    def __init__(self, sym):
        os.makedirs(CACHE, exist_ok=True)
        cp = os.path.join(CACHE, f"{sym}.npz")
        if os.path.exists(cp):
            z = np.load(cp, allow_pickle=True)
            for k in z.files:
                setattr(self, k, z[k])
            self.sym = sym
            return
        z = np.load(os.path.join(DATEN, "kern", f"{sym}.npz"))
        ts = pd.to_datetime(z["m5_t"], unit="s", utc=True).tz_convert("America/New_York")
        mins = ts.hour * 60 + ts.minute
        reg = (mins >= 570) & (mins < 960)
        days = np.array(ts.date)[reg]
        udays = np.array(sorted(set(days)))
        di = np.searchsorted(udays, days)
        sl = ((mins[reg] - 570) // 5).astype(int)
        shape = (len(udays), SLOTS)
        for k in ("o", "h", "l", "c", "v", "vw"):
            g = np.full(shape, np.nan)
            g[di, sl] = z["m5_" + k][reg]
            setattr(self, k, g)
        self.v = np.nan_to_num(self.v)
        self.tage = np.array([d.isoformat() for d in udays])
        dts = pd.to_datetime(z["d_t"], unit="s", utc=True).tz_convert("America/New_York")
        dd = np.array([d.isoformat() for d in dts.date])
        pos = {d: i for i, d in enumerate(dd)}
        idx = np.array([pos.get(d, -1) for d in self.tage])
        self.do = np.where(idx >= 0, z["d_o"][np.maximum(idx, 0)], self.o[:, 0])
        self.dc = np.where(idx >= 0, z["d_c"][np.maximum(idx, 0)], self.c[:, -1])
        self.dh = np.where(idx >= 0, z["d_h"][np.maximum(idx, 0)], np.nanmax(self.h, 1))
        self.dl = np.where(idx >= 0, z["d_l"][np.maximum(idx, 0)], np.nanmin(self.l, 1))
        # Lücken im Raster füllen (keine Kerze = kein Handel): Kurs bleibt, Volumen 0
        c = self.c.copy()
        for j in range(SLOTS):
            if j == 0:
                c[:, 0] = np.where(np.isnan(c[:, 0]), self.do, c[:, 0])
            else:
                c[:, j] = np.where(np.isnan(c[:, j]), c[:, j - 1], c[:, j])
        for k in ("o", "h", "l"):
            g = getattr(self, k)
            setattr(self, k, np.where(np.isnan(g), c, g))
        self.vw = np.where(np.isnan(self.vw), c, self.vw)
        self.c = c
        self.sym = sym
        np.savez(cp, **{k: getattr(self, k) for k in ("o", "h", "l", "c", "v", "vw", "tage", "do", "dc", "dh", "dl")})

    @property
    def pc(self):
        return np.r_[np.nan, self.dc[:-1]]


def jahr(tage):
    return np.array([t[:4] for t in tage])


ENTWICKLUNG = ("2018-01-01", "2023-12-31")
ENDTEST = ("2024-01-01", "2026-12-31")   # gesperrt bis zum Schluss!


def auswerten(tr, name="", kap=10_000.0, zeigen=True, zeitraum=ENTWICKLUNG, kosten_faktor=1.0):
    """tr: DataFrame mit tag, sym, seite(+1/-1), ein, aus, gewicht (Anteil am Kapital, z. B. 0.5 = 5.000 $),
    kosten_bp (pro Seite). Gibt Kennzahlen für den Zeitraum zurück (Standard: Entwicklung 2018–2023)."""
    if len(tr) == 0:
        return None
    t = tr.copy()
    t = t[(t.tag >= zeitraum[0]) & (t.tag <= zeitraum[1])]
    if len(t) == 0:
        return None
    t["kosten_bp"] = t.kosten_bp * kosten_faktor
    brutto = t.seite * (t.aus / t.ein - 1)
    netto = brutto - 2 * t.kosten_bp / 1e4
    t["netto"] = netto
    t["pnl"] = netto * t.gewicht * kap
    tage_alle = t.tag.unique()
    tg = t.groupby("tag").pnl.sum()
    n_tage = len(pd.bdate_range(t.tag.min(), t.tag.max()))  # Börsentage grob
    jahre = t.groupby(t.tag.str[:4]).pnl.sum()
    eq = tg.cumsum()
    dd = (eq - eq.cummax()).min()
    sharpe = tg.mean() / tg.std() * np.sqrt(252) * len(tg) / max(n_tage, 1) if tg.std() > 0 else 0
    r = dict(name=name, trades=len(t), pro_tag=len(t) / max(n_tage, 1), netto_bp=netto.mean() * 1e4,
             brutto_bp=brutto.mean() * 1e4, treffer=(netto > 0).mean(), summe=t.pnl.sum(), maxdd=dd,
             sharpe=sharpe, jahre=jahre.round(0).to_dict(), plus_jahre=int((jahre > 0).sum()), n_jahre=len(jahre))
    if zeigen:
        js = " ".join(f"{k[2:]}:{v:+.0f}" for k, v in r["jahre"].items())
        print(f"{name:<38} {r['trades']:>6} T ({r['pro_tag']:4.1f}/Tag) netto {r['netto_bp']:+6.1f}bp "
              f"(brutto {r['brutto_bp']:+5.1f}) Treffer {r['treffer']:.0%} | Summe {r['summe']:+8.0f}$ "
              f"DD {r['maxdd']:+6.0f} Sh {r['sharpe']:+.2f} | {js}", flush=True)
    return r
