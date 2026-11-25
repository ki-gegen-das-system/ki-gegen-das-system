#!/usr/bin/env python3
"""Runde 1: alle Strategie-Familien auf den Kern-Daten, NUR Entwicklungszeitraum 2018–2023."""
import os, sys, time
import numpy as np
import pandas as pd
from labor import Raster, auswerten
import strategien as S

KERN = [f[:-4] for f in sorted(os.listdir(os.path.join(os.environ.get("DATEN", "/home/claude/fl/daten"), "kern")))]
ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLI", "SMH", "TLT", "GLD"]
AKTIEN = [s for s in KERN if s not in ETFS and s != "TQQQ"]
ACHT = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA"]
ZWANZIG = ACHT + ["AMD", "GOOGL", "NFLX", "AVGO", "PLTR", "COIN", "MU", "BA", "JPM", "XOM", "UBER", "DIS"]
R = {s: Raster(s) for s in KERN}
print(f"{len(R)} Symbole geladen: {len(ETFS)} ETFs, {len(AKTIEN)} Aktien", flush=True)
ERG = []


def lauf(name, fn, syms, **kw):
    t0 = time.time()
    tr = pd.concat([fn(R[s], n_assets=len(syms), **kw) for s in syms if s in R], ignore_index=True)
    r = auswerten(tr, name)
    if r:
        ERG.append(r)
    return tr


teil = sys.argv[1] if len(sys.argv) > 1 else "alle"
if teil in ("alle", "kontext"):
    print("\n--- Kontext: über Nacht vs. tagsüber (SPY, QQQ) ---")
    for s in ("SPY", "QQQ"):
        lauf(f"nur Nacht halten {s}", S.nacht, [s])
        lauf(f"nur tagsüber halten {s}", S.tagsueber, [s])
if teil in ("alle", "rausch"):
    print("\n--- S1 Rauschzonen-Momentum (Zarattini 2024) ---")
    for takt in (6, 3, 1):
        lauf(f"Rausch SPY takt{takt}", S.rauschzone, ["SPY"], takt=takt)
    lauf("Rausch SPY takt6 ohne VWAP-Stop", S.rauschzone, ["SPY"], takt=6, vwap_stop=False)
    lauf("Rausch QQQ takt6", S.rauschzone, ["QQQ"], takt=6)
    lauf("Rausch 13 ETFs takt6", S.rauschzone, ETFS, takt=6)
    lauf("Rausch 8 (Bert) takt6", S.rauschzone, ACHT, takt=6)
    lauf("Rausch 20 takt6", S.rauschzone, ZWANZIG, takt=6)
    lauf("Rausch Aktien takt6", S.rauschzone, AKTIEN, takt=6)
    lauf("Rausch alle 48 takt6", S.rauschzone, KERN, takt=6)
    lauf("Rausch alle 48 takt3", S.rauschzone, KERN, takt=3)
    lauf("Rausch alle 48 takt1", S.rauschzone, KERN, takt=1)
if teil in ("alle", "schluss"):
    print("\n--- S7 letzte halbe Stunde (Gao 2018) ---")
    lauf("Schluss SPY", S.schluss, ["SPY"])
    lauf("Schluss 13 ETFs", S.schluss, ETFS)
    lauf("Schluss alle 48", S.schluss, KERN)
if teil in ("alle", "mr"):
    print("\n--- S5 RSI(2) Rückkehr zum Mittelwert ---")
    lauf("RSI2 ETFs", S.rsi2, ETFS)
    lauf("RSI2 ETFs Trend", S.rsi2, ETFS, trend=True)
    lauf("RSI2 Aktien", S.rsi2, AKTIEN)
    lauf("RSI2 Aktien Trend", S.rsi2, AKTIEN, trend=True)
if teil in ("alle", "gap"):
    print("\n--- S6 Gaps ---")
    for art in ("fade", "go"):
        for sw in (0.01, 0.02):
            lauf(f"Gap {art} {sw:.0%} alle 48", S.gap, KERN, schwelle=sw, art=art)
if teil in ("alle", "orbqqq"):
    print("\n--- S3b ORB QQQ (Zarattini & Aziz 2023): Einstieg 9:35 in Richtung der 1. Kerze ---")
    for s in ("QQQ", "SPY"):
        lauf(f"ORB-QQQ-Regel {s}", S.orb_qqq, [s])
    lauf("ORB-QQQ-Regel 13 ETFs", S.orb_qqq, ETFS)
    lauf("ORB-QQQ-Regel alle 48", S.orb_qqq, KERN)
if teil in ("alle", "orb"):
    print("\n--- S3 Opening Range Breakout, fester Korb (Auswahl: höchstes rel. Volumen) ---")
    for or_s in (1, 3, 6):
        for st in (0.1, 0.25, 0.5):
            alle = pd.concat([S.orb(R[s], or_slots=or_s, stop_atr=st) for s in KERN], ignore_index=True)
            for top in (5, 20):
                sel = alle[alle.rvol >= 1].sort_values("rvol", ascending=False).groupby("tag").head(top).copy()
                sel["gewicht"] = np.minimum(sel.gewicht, 4.0 / top)
                r = auswerten(sel, f"ORB {or_s * 5}min stop{st}ATR top{top}")
                ERG.append(r)
if teil in ("alle", "quer"):
    print("\n--- S10 Querschnitt: Gewinner/Verlierer seit Eröffnung unter den Aktien ---")
    from labor import kosten_bp
    tage = sorted(set.intersection(*[set(R[s].tage) for s in ACHT]))
    for k0 in (5, 11):
        for art in ("momentum", "umkehr"):
            for q in (3, 5):
                rows = []
                idx = {s: {t: i for i, t in enumerate(R[s].tage)} for s in AKTIEN}
                for t in tage:
                    werte = []
                    for s in AKTIEN:
                        i = idx[s].get(t)
                        if i is None:
                            continue
                        r_ = R[s]
                        werte.append((r_.c[i, k0] / r_.do[i] - 1, s, i))
                    if len(werte) < 2 * q + 2:
                        continue
                    werte.sort()
                    lang = werte[-q:] if art == "momentum" else werte[:q]
                    kurz = werte[:q] if art == "momentum" else werte[-q:]
                    for grp, seite in ((lang, 1), (kurz, -1)):
                        for _, s, i in grp:
                            r_ = R[s]
                            rows.append((t, s, seite, r_.o[i, k0 + 1], r_.dc[i], 1.0 / q, kosten_bp(s), k0 + 1, 78))
                tr = pd.DataFrame(rows, columns=["tag", "sym", "seite", "ein", "aus", "gewicht", "kosten_bp", "t_ein", "t_aus"])
                ERG.append(auswerten(tr, f"Quer {art} ab {'10:00' if k0 == 5 else '10:30'} {q}+{q}"))
pd.DataFrame(ERG).to_pickle(f"/home/claude/fl/ergebnis1_{teil}.pkl")
