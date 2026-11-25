#!/usr/bin/env python3
"""S2: Opening Range Breakout auf „Stocks in Play“ (Zarattini/Barbon/Aziz 2024) mit den Scanner-Daten.
Jeden Morgen: Aktien mit Preis > 5 $, Ø-Volumen > 1 Mio., ATR > 0,50 $ -> Top N nach relativem Volumen der
ersten 5 Minuten. Grüne erste Kerze -> Kauf-Stop über ihrem Hoch, rote -> Short-Stop unter ihrem Tief.
Stop = x * ATR. Ausstieg: Stop oder Börsenschluss. Simulation: 1-Min-Kerzen bis 10:29, danach 5-Min."""
import os
import numpy as np
import pandas as pd
from labor import DATEN, auswerten

Z = np.load(os.path.join(DATEN, "scanner.npz"))
SYMS = Z["syms"]
OPEN = pd.DataFrame(Z["open"], columns=["d", "sid", "pc", "atr", "avgvol", "o", "h", "l", "c", "v", "rvol", "n"])
OPEN = OPEN.dropna(subset=["o"])
OPEN[["d", "sid"]] = OPEN[["d", "sid"]].astype(int)
TAGE = pd.DataFrame(np.load(os.path.join(DATEN, "scanner_tage.npz"))["daily"],
                    columns=["d", "sid", "do", "dh", "dl", "dc", "dv"])
TAGE[["d", "sid"]] = TAGE[["d", "sid"]].astype(int)
SCHLUSS = {(d, s): c for d, s, c in zip(TAGE.d, TAGE.sid, TAGE.dc)}


def _bars(meta, arr):
    m = pd.DataFrame(meta, columns=["d", "sid", "t"])
    ts = pd.to_datetime(m.t, unit="s", utc=True).dt.tz_convert("America/New_York")
    m["min"] = ts.dt.hour * 60 + ts.dt.minute
    for i, k in enumerate(["o", "h", "l", "c", "v", "vw"]):
        m[k] = arr[:, i].astype(float)
    return m


M1 = _bars(Z["m1_meta"], Z["m1"])
M5 = _bars(Z["m5_meta"], Z["m5"])
# Kerzenfolge je (Tag, Aktie): 1-Min ab 9:35 bis 10:29, dann 5-Min ab 10:30
SEQ = {}
for (d, s), g in M1[M1["min"] >= 575].groupby(["d", "sid"]):
    SEQ[(d, s)] = [g[["min", "o", "h", "l", "c"]].to_numpy()]
for (d, s), g in M5[M5["min"] >= 630].groupby(["d", "sid"]):
    SEQ.setdefault((d, s), []).append(g[["min", "o", "h", "l", "c"]].to_numpy())
SEQ = {k: np.concatenate(v) for k, v in SEQ.items()}
print(f"Scanner: {OPEN.d.nunique()} Tage, {len(OPEN)} Kandidaten-Tage, {len(SEQ)} Aktien-Tage mit Intraday",
      flush=True)


def tag_str(d):
    return str(np.datetime64(int(d), "D"))


def orb_inplay(top=20, stop_atr=0.10, ziel_r=None, rvol_min=1.0, preis_min=5.0, seiten=(1, -1),
               kosten_cent=1.0, kosten_bp=2.0, hebel_max=4.0, risiko=0.01, ende_min=None):
    sel = OPEN[(OPEN.rvol >= rvol_min) & (OPEN.pc >= preis_min)]
    sel = sel.sort_values(["d", "rvol"], ascending=[True, False]).groupby("d").head(top)
    rows = []
    for x in sel.itertuples():
        richtung = 1 if x.c > x.o else -1 if x.c < x.o else 0
        if richtung == 0 or richtung not in seiten:
            continue
        bars = SEQ.get((x.d, x.sid))
        if bars is None or len(bars) == 0:
            continue
        trig = x.h if richtung > 0 else x.l
        stopw = stop_atr * x.atr
        ein = None
        for i in range(len(bars)):
            mn, o, h, l, c = bars[i]
            if ende_min and mn >= ende_min:
                break
            if ein is None:
                if (richtung > 0 and h >= trig) or (richtung < 0 and l <= trig):
                    ein = max(trig, o) if richtung > 0 else min(trig, o)
                    stop = ein - richtung * stopw
                    ziel = ein + richtung * ziel_r * stopw if ziel_r else None
                    t_ein = mn
                    # gleiche Kerze: Reihenfolge unbekannt -> vorsichtig: Stop zuerst
                    if (richtung > 0 and l <= stop) or (richtung < 0 and h >= stop):
                        rows.append((x.d, x.sid, richtung, ein, stop, t_ein, mn, x.pc, x.atr, x.rvol)); ein = "fertig"
                        break
                continue
            if (richtung > 0 and l <= stop) or (richtung < 0 and h >= stop):
                aus = min(stop, o) if richtung > 0 else max(stop, o)
                rows.append((x.d, x.sid, richtung, ein, aus, t_ein, mn, x.pc, x.atr, x.rvol)); ein = "fertig"
                break
            if ziel is not None and ((richtung > 0 and h >= ziel) or (richtung < 0 and l <= ziel)):
                aus = max(ziel, o) if richtung > 0 else min(ziel, o)
                rows.append((x.d, x.sid, richtung, ein, aus, t_ein, mn, x.pc, x.atr, x.rvol)); ein = "fertig"
                break
        if ein is not None and ein != "fertig":
            if ende_min:
                aus = bars[min(i, len(bars) - 1)][1]
            else:
                aus = SCHLUSS.get((x.d, x.sid), bars[-1][4])
            rows.append((x.d, x.sid, richtung, ein, aus, t_ein, 960, x.pc, x.atr, x.rvol))
    t = pd.DataFrame(rows, columns=["d", "sid", "seite", "ein", "aus", "t_ein", "t_aus", "pc", "atr", "rvol"])
    t["tag"] = [tag_str(d) for d in t.d]
    t["sym"] = SYMS[t.sid.astype(int)]
    t["kosten_bp"] = 1e4 * (kosten_cent / 100) / t.ein + kosten_bp
    t["gewicht"] = np.minimum(risiko * t.ein / (stop_atr * t.atr), hebel_max / top)
    return t


if __name__ == "__main__":
    import sys
    print("\n--- S2 ORB auf Stocks in Play (Entwicklung 2018–2023) ---")
    for top in (20, 10, 5):
        for st in (0.05, 0.10, 0.20, 0.50):
            auswerten(orb_inplay(top=top, stop_atr=st), f"InPlay top{top} stop{st}ATR")
