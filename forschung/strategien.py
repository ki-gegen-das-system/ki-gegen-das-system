#!/usr/bin/env python3
"""Strategien für das Labor. Jede gibt einen DataFrame mit Trades zurück:
tag, sym, seite (+1 Kauf / -1 Short), ein, aus (Preise), gewicht (Anteil am Kapital), kosten_bp, extra Spalten."""
import numpy as np
import pandas as pd
from labor import kosten_bp, SLOTS


def _df(rows, cols=("tag", "sym", "seite", "ein", "aus", "gewicht", "kosten_bp", "t_ein", "t_aus")):
    return pd.DataFrame(rows, columns=list(cols)) if rows else pd.DataFrame(columns=list(cols))


def atr_tag(r, n=14):
    pc = r.pc
    tr = np.fmax(r.dh - r.dl, np.fmax(np.abs(r.dh - pc), np.abs(r.dl - pc)))
    out = np.full(len(tr), np.nan)
    for i in range(n + 1, len(tr)):
        out[i] = np.nanmean(tr[i - n:i])      # nur Vortage
    return out


def vol_tag(r, n=14):
    ret = r.dc / r.pc - 1
    out = np.full(len(ret), np.nan)
    for i in range(n + 1, len(ret)):
        out[i] = np.nanstd(ret[i - n:i])
    return out


def vwap(r):
    pv = np.cumsum(r.vw * r.v, axis=1)
    vv = np.cumsum(r.v, axis=1)
    return np.where(vv > 0, pv / np.maximum(vv, 1e-9), r.c)


# ------------------------------------------------------------------ S1: Rauschzonen-Momentum
def rauschzone(r, takt=6, lookback=14, vwap_stop=True, lev_ziel=0.02, lev_max=4.0, start=5, n_assets=1,
               nur_kauf=False, ende_slot=None):
    """Zarattini/Aziz/Barbon (2024) „Beat the Market“: Ausbruch aus der üblichen Schwankungszone seit
    Eröffnung; Stop = Rauschgrenze bzw. VWAP; Entscheidung alle `takt` Kerzen; Ausstieg zum Schluss."""
    o, c, do, pc, dc = r.o, r.c, r.do, r.pc, r.dc
    n = len(r.tage)
    move = np.abs(c / do[:, None] - 1)
    sig = np.full_like(move, np.nan)
    for d in range(lookback, n):
        sig[d] = np.nanmean(move[d - lookback:d], axis=0)
    up = np.fmax(do, pc)[:, None] * (1 + sig)
    dn = np.fmin(do, pc)[:, None] * (1 - sig)
    vw = vwap(r)
    lev = np.minimum(lev_max, lev_ziel / vol_tag(r)) / n_assets
    kb = getattr(r, "kosten", None) or kosten_bp(r.sym)
    ns = c.shape[1]
    ende_slot = ende_slot or ns - 2
    rows = []
    for d in range(lookback + 1, n):
        if not np.isfinite(lev[d]) or not np.isfinite(pc[d]):
            continue
        pos, ein, t0 = 0, 0.0, 0
        for k in range(start, ende_slot + 1, takt):
            p = c[d, k]
            if pos == 1 and p < (max(up[d, k], vw[d, k]) if vwap_stop else up[d, k]):
                rows.append((r.tage[d], r.sym, 1, ein, o[d, k + 1], lev[d], kb, t0, k + 1)); pos = 0
            elif pos == -1 and p > (min(dn[d, k], vw[d, k]) if vwap_stop else dn[d, k]):
                rows.append((r.tage[d], r.sym, -1, ein, o[d, k + 1], lev[d], kb, t0, k + 1)); pos = 0
            if pos == 0 and k < ende_slot:
                if p > up[d, k]:
                    pos, ein, t0 = 1, o[d, k + 1], k + 1
                elif p < dn[d, k] and not nur_kauf:
                    pos, ein, t0 = -1, o[d, k + 1], k + 1
        if pos:
            rows.append((r.tage[d], r.sym, pos, ein, dc[d], lev[d], kb, t0, ns))
    return _df(rows)


# ------------------------------------------------------------------ S3: Opening Range Breakout
def orb(r, or_slots=1, stop_atr=0.10, ziel_r=None, pessimistisch=True):
    """Richtung aus der ersten Kerze (grün = Kauf-Stop über dem Hoch, rot = Short-Stop unter dem Tief),
    Stop = stop_atr x Tages-ATR, Ausstieg Stop/Ziel/Schluss. Liefert ALLE Setups mit rvol (Auswahl später)."""
    o, h, l, c, v, dc = r.o, r.h, r.l, r.c, r.v, r.dc
    n = len(r.tage)
    atr = atr_tag(r)
    v0 = v[:, :or_slots].sum(1)
    rv = np.full(n, np.nan)
    for d in range(15, n):
        m = np.mean(v0[d - 14:d])
        rv[d] = v0[d] / m if m > 0 else np.nan
    kb = kosten_bp(r.sym)
    rows = []
    for d in range(15, n):
        if not np.isfinite(atr[d]) or not np.isfinite(rv[d]):
            continue
        hi, lo = h[d, :or_slots].max(), l[d, :or_slots].min()
        richtung = np.sign(c[d, or_slots - 1] - o[d, 0])
        if richtung == 0:
            continue
        trig = hi if richtung > 0 else lo
        stopw = stop_atr * atr[d]
        for k in range(or_slots, SLOTS):
            if (richtung > 0 and h[d, k] >= trig) or (richtung < 0 and l[d, k] <= trig):
                ein = max(trig, o[d, k]) if richtung > 0 else min(trig, o[d, k])
                stop = ein - richtung * stopw
                ziel = ein + richtung * ziel_r * stopw if ziel_r else None
                aus, t_aus = dc[d], SLOTS
                for j in range(k, SLOTS):
                    lo_j, hi_j = l[d, j], h[d, j]
                    hit_stop = lo_j <= stop if richtung > 0 else hi_j >= stop
                    hit_ziel = ziel is not None and (hi_j >= ziel if richtung > 0 else lo_j <= ziel)
                    if j == k and not pessimistisch:
                        # in der Einstiegskerze: nur zählen, wenn der Schluss jenseits des Stops liegt
                        hit_stop = (c[d, j] <= stop) if richtung > 0 else (c[d, j] >= stop)
                        hit_ziel = False
                    if hit_stop:
                        aus = (min(stop, o[d, j]) if richtung > 0 else max(stop, o[d, j])) if j > k else stop
                        t_aus = j
                        break
                    if hit_ziel:
                        aus = (max(ziel, o[d, j]) if richtung > 0 else min(ziel, o[d, j])) if j > k else ziel
                        t_aus = j
                        break
                gew = min(0.01 * ein / stopw, 4.0)   # 1 % Risiko, max. 4x Hebel (pro Trade, wird später gedeckelt)
                rows.append((r.tage[d], r.sym, int(richtung), ein, aus, gew, kb, k, t_aus, rv[d]))
                break
    return _df(rows, ("tag", "sym", "seite", "ein", "aus", "gewicht", "kosten_bp", "t_ein", "t_aus", "rvol"))


# ------------------------------------------------------------------ S5: Rückkehr zum Mittelwert (RSI 2)
def rsi_wilder(x, n=2):
    d = np.diff(x, prepend=x[0])
    g, l_ = np.maximum(d, 0), np.maximum(-d, 0)
    ag, al = np.zeros_like(x), np.zeros_like(x)
    a = 1.0 / n
    for i in range(1, len(x)):
        ag[i] = ag[i - 1] + a * (g[i] - ag[i - 1])
        al[i] = al[i - 1] + a * (l_[i] - al[i - 1])
    return np.where(al > 0, 100 - 100 / (1 + ag / np.maximum(al, 1e-12)), 100.0)


def rsi2(r, unten=5, oben=95, raus_kauf=70, raus_short=30, trend=False, n_assets=1, letzter=70):
    o, c, dc = r.o, r.c, r.dc
    flat = c.reshape(-1)
    rs = rsi_wilder(flat, 2).reshape(c.shape)
    sma = pd.Series(flat).rolling(200, min_periods=50).mean().to_numpy().reshape(c.shape)
    kb = kosten_bp(r.sym)
    rows = []
    for d in range(1, len(r.tage)):
        pos, ein, t0 = 0, 0.0, 0
        for k in range(0, SLOTS - 1):
            x = rs[d, k]
            if pos == 1 and x > raus_kauf:
                rows.append((r.tage[d], r.sym, 1, ein, o[d, k + 1], 1.0 / n_assets, kb, t0, k + 1)); pos = 0
            elif pos == -1 and x < raus_short:
                rows.append((r.tage[d], r.sym, -1, ein, o[d, k + 1], 1.0 / n_assets, kb, t0, k + 1)); pos = 0
            elif pos == 0 and k <= letzter:
                if x < unten and (not trend or c[d, k] > sma[d, k]):
                    pos, ein, t0 = 1, o[d, k + 1], k + 1
                elif x > oben and (not trend or c[d, k] < sma[d, k]):
                    pos, ein, t0 = -1, o[d, k + 1], k + 1
        if pos:
            rows.append((r.tage[d], r.sym, pos, ein, dc[d], 1.0 / n_assets, kb, t0, SLOTS))
    return _df(rows)


# ------------------------------------------------------------------ S6: Gaps
def gap(r, schwelle=0.01, art="fade", n_assets=1):
    o, h, l, dc, do, pc = r.o, r.h, r.l, r.dc, r.do, r.pc
    kb = kosten_bp(r.sym)
    rows = []
    for d in range(1, len(r.tage)):
        if not np.isfinite(pc[d]):
            continue
        g = do[d] / pc[d] - 1
        if abs(g) < schwelle:
            continue
        seite = -int(np.sign(g)) if art == "fade" else int(np.sign(g))
        ein = o[d, 1]
        aus, t_aus = dc[d], SLOTS
        if art == "fade":   # Ziel: Lücke geschlossen (Vortagesschluss)
            for k in range(1, SLOTS):
                if (seite == 1 and h[d, k] >= pc[d]) or (seite == -1 and l[d, k] <= pc[d]):
                    aus, t_aus = pc[d], k
                    break
        rows.append((r.tage[d], r.sym, seite, ein, aus, 1.0 / n_assets, kb, 1, t_aus))
    return _df(rows)


# ------------------------------------------------------------------ S7: letzte halbe Stunde (Gao et al. 2018)
def schluss(r, n_assets=1):
    c, o, dc, pc = r.c, r.o, r.dc, r.pc
    kb = kosten_bp(r.sym)
    rows = []
    for d in range(1, len(r.tage)):
        if not np.isfinite(pc[d]):
            continue
        s = np.sign(c[d, 5] / pc[d] - 1)
        if s:
            rows.append((r.tage[d], r.sym, int(s), o[d, 72], dc[d], 1.0 / n_assets, kb, 72, SLOTS))
    return _df(rows)


# ------------------------------------------------------------------ S8: über Nacht halten (nur Vergleich)
def nacht(r, n_assets=1):
    kb = kosten_bp(r.sym)
    rows = [(r.tage[d], r.sym, 1, r.dc[d - 1], r.do[d], 1.0 / n_assets, kb, -1, 0)
            for d in range(1, len(r.tage)) if np.isfinite(r.dc[d - 1])]
    return _df(rows)


def tagsueber(r, n_assets=1):
    kb = kosten_bp(r.sym)
    rows = [(r.tage[d], r.sym, 1, r.do[d], r.dc[d], 1.0 / n_assets, kb, 0, SLOTS) for d in range(len(r.tage))]
    return _df(rows)


# ------------------------------------------------------------------ S3b: ORB QQQ (Zarattini & Aziz 2023)
def orb_qqq(r, ziel_r=10.0, risiko=0.01, lev_max=4.0, n_assets=1):
    """Erste 5-Min-Kerze grün -> Kauf zur Eröffnung der zweiten Kerze, Stop = Tief der ersten Kerze
    (rot: Short, Stop = Hoch). Ziel 10R, sonst Ausstieg zum Schluss. 1 % Risiko, max. 4x Hebel."""
    o, h, l, c, dc = r.o, r.h, r.l, r.c, r.dc
    kb = kosten_bp(r.sym)
    rows = []
    for d in range(1, len(r.tage)):
        s = np.sign(c[d, 0] - o[d, 0])
        if not s:
            continue
        ein = o[d, 1]
        stop = l[d, 0] if s > 0 else h[d, 0]
        risk = (ein - stop) * s
        if risk <= 0:
            continue
        ziel = ein + s * ziel_r * risk
        aus, t_aus = dc[d], SLOTS
        for k in range(1, SLOTS):
            if (s > 0 and l[d, k] <= stop) or (s < 0 and h[d, k] >= stop):
                aus = (min(stop, o[d, k]) if s > 0 else max(stop, o[d, k])) if k > 1 else stop
                t_aus = k
                break
            if (s > 0 and h[d, k] >= ziel) or (s < 0 and l[d, k] <= ziel):
                aus, t_aus = ziel, k
                break
        gew = min(risiko * ein / risk, lev_max) / n_assets
        rows.append((r.tage[d], r.sym, int(s), ein, aus, gew, kb, 1, t_aus))
    return _df(rows)
