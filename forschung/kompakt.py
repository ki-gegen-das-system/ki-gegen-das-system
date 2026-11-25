#!/usr/bin/env python3
"""Macht die Forschungsdaten kompakt (float32, nur reguläre Börsenzeit außer SPY/QQQ), damit sie per Git
(eigener Zweig, wird danach gelöscht) in die Arbeitsumgebung kommen. Aufruf: kompakt.py <roh> <ziel> <teil>"""
import os
import sys
import numpy as np

roh, ziel, teil = sys.argv[1:4]
os.makedirs(ziel, exist_ok=True)


def ny_minuten(t):
    # New York: Sommerzeit grob über UTC-Offset der US-Regel (2. So im März bis 1. So im November)
    import pandas as pd
    ts = pd.to_datetime(t, unit="s", utc=True).tz_convert("America/New_York")
    return (ts.hour * 60 + ts.minute).to_numpy()


if teil == "kern":
    for sub in ("kern", "krypto"):
        os.makedirs(os.path.join(ziel, sub), exist_ok=True)
        for f in sorted(os.listdir(os.path.join(roh, sub))):
            z = np.load(os.path.join(roh, sub, f))
            t = z["m5_t"]
            keep = np.ones(len(t), bool)
            if sub == "kern" and f[:-4] not in ("SPY", "QQQ"):
                m = ny_minuten(t)
                keep = (m >= 570) & (m < 960)
            out = {"m5_t": t[keep].astype(np.int64)}
            for k in ("o", "h", "l", "c", "vw"):
                out["m5_" + k] = z["m5_" + k][keep].astype(np.float32)
            out["m5_v"] = z["m5_v"][keep].astype(np.float32)
            for k in z.files:
                if k.startswith("d_"):
                    out[k] = z[k]
            np.savez_compressed(os.path.join(ziel, sub, f), **out)
            print(f, keep.sum(), "von", len(t), flush=True)
elif teil == "scanner":
    z = np.load(os.path.join(roh, "scanner.npz"))
    op = z["open"]
    # nur Zeilen mit erster Kerze; Spalten: d, sid, pc, atr, avgvol, o, h, l, c, v, rvol (float32 genügt außer d/sid)
    op = op[~np.isnan(op[:, 5])]
    np.savez_compressed(os.path.join(ziel, "scanner.npz"), syms=z["syms"],
                        open_ds=op[:, :2].astype(np.int32), open=op[:, 2:11].astype(np.float32),
                        m1_meta=z["m1_meta"].astype(np.int64), m1=z["m1"], m5_meta=z["m5_meta"].astype(np.int64),
                        m5=z["m5"])
    t = np.load(os.path.join(roh, "scanner_tage.npz"))["daily"]
    np.savez_compressed(os.path.join(ziel, "scanner_tage.npz"), ds=t[:, :2].astype(np.int32),
                        ohlcv=t[:, 2:].astype(np.float32))
else:
    for f in os.listdir(roh):
        os.replace(os.path.join(roh, f), os.path.join(ziel, f))
for dp, dn, fn in os.walk(ziel):
    for f in fn:
        p = os.path.join(dp, f)
        print(p, round(os.path.getsize(p) / 1e6, 1), "MB")
