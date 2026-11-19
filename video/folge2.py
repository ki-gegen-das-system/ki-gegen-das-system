#!/usr/bin/env python3
"""Folge 2 – Tag 1. Nutzt die Bausteine aus Folge 1."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import folge1 as f1
from folge1 import (W, H, background, txt, pop, rrect, place, text_img, robot, BERT, KURT, font, prog,
                    ease_out, ease_back, WHITE, GREY, BLUE, GREEN, YELLOW, RED, PANEL, BLACK, BOLD, SEMI, MONO)
from PIL import Image, ImageDraw

f1.OUT = os.environ.get("RENDER_DIR", "/tmp/render")
os.makedirs(f1.OUT, exist_ok=True)


def money(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def header(b):
    pill = text_img("KI GEGEN DAS SYSTEM  ·  FOLGE 2  ·  TAG 1", SEMI, 34, GREY)
    w = pill.width + 60
    rrect(b, (W / 2 - w / 2, 230, W / 2 + w / 2, 300), 35, (18, 25, 45), 0.9, outline=(45, 58, 92), width=2)
    place(b, pill, W / 2, 265)


def lines_layer(b, series, box, p, lo=None, hi=None, widths=None, glow=True):
    """Zeichnet mehrere Linien (Liste aus (werte, farbe)) bis Fortschritt p in box."""
    x0, y0, x1, y1 = box
    allv = [v for s, _ in series for v in s]
    lo = min(allv) if lo is None else lo
    hi = max(allv) if hi is None else hi
    layer = Image.new("RGBA", b.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    out = []
    for k, (vals, col) in enumerate(series):
        pts = [(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * (v - lo) / (hi - lo)) for i, v in enumerate(vals)]
        n = max(2, int(len(pts) * p))
        w = (widths or [8] * len(series))[k]
        if glow:
            d.line(pts[:n], fill=col + (70,), width=w * 3, joint="curve")
        d.line(pts[:n], fill=col + (255,), width=w, joint="curve")
        out.append(pts)
    b.alpha_composite(layer)
    return out


# ------------------------------------------------------------------ Szenen
def s1(t):
    b = background(t); header(b)
    pop(b, "TAG 1", 220, YELLOW, 620, t, 0.0)
    pop(b, "Bert hat gekauft.", 100, WHITE, 830, t, 0.6)
    pop(b, "…und einen Fehler", 100, RED, 990, t, 1.8)
    pop(b, "gemacht.", 100, RED, 1110, t, 2.1)
    return b


# Illustration für die Erklärung: Preis fällt, dreht, steigt
_price = []
for i in range(60):
    base = 100 - 0.25 * i if i < 28 else 93 + 0.32 * (i - 28)
    _price.append(base + 1.2 * math.sin(i * 0.9) + 0.6 * math.sin(i * 2.3))
def _ema(vals, n):
    k, out, e = 2 / (n + 1), [], None
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


_fast = _ema(_price, 9)
_slow = _ema(_price, 21)
_cross = next(i for i in range(25, 60) if _fast[i - 1] <= _slow[i - 1] and _fast[i] > _slow[i])


def s2(t):  # So entscheidet Bert
    b = background(t); header(b)
    pop(b, "So entscheidet Bert:", 92, WHITE, 410, t, 0.0)
    box = (110, 560, 970, 1090)
    p = prog(t, 0.6, 0.3)
    if p > 0:
        rrect(b, (80, 520, 1000, 1130), 36, PANEL, ease_out(p))
        txt(b, "Illustration", 30, GREY, 915, 1105, SEMI, alpha=ease_out(p))
    q = ease_out(prog(t, 0.9, 3.2))
    if q > 0:
        lo, hi = min(_price) - 1, max(_price) + 1
        pts = lines_layer(b, [(_price, (110, 122, 150)), (_slow, YELLOW), (_fast, BLUE)], box, q, lo, hi,
                          widths=[4, 9, 9])
        if q > _cross / 59 + 0.02:
            cx, cy = pts[2][_cross]
            r = prog(t, 0.9 + 3.2 * (_cross / 59) + 0.1, 0.35)
            layer = Image.new("RGBA", b.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            rad = 26 * ease_back(r)
            d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=GREEN + (255,), outline=WHITE + (255,), width=5)
            b.alpha_composite(layer)
            txt(b, "KAUF", 54, GREEN, cx, cy - 75, alpha=ease_out(r))
    # Legende
    pop(b, "Blau = Durchschnitt letzte ~2 Std.", 50, BLUE, 1220, t, 1.2, BOLD)
    pop(b, "Gelb = Durchschnitt letzte ~5 Std.", 50, YELLOW, 1295, t, 1.8, BOLD)
    pop(b, "Blau kreuzt Gelb nach oben", 66, WHITE, 1420, t, 4.4, BOLD)
    pop(b, "= Trend dreht → KAUF", 66, GREEN, 1505, t, 4.9)
    pop(b, "Fällt Blau wieder drunter → VERKAUF", 50, RED, 1610, t, 6.4, BOLD)
    return b


def s3(t):  # Notbremsen
    b = background(t); header(b)
    pop(b, "Dazu 3 feste", 100, WHITE, 470, t, 0.0)
    pop(b, "Notbremsen:", 100, YELLOW, 590, t, 0.15)
    rows = [("−1,5 %", "Verlust? Sofort raus.", RED), ("+3 %", "Gewinn? Sichern.", GREEN),
            ("22:00", "Börse zu? Alles raus.", BLUE)]
    for i, (a, txt_, col) in enumerate(rows):
        st = 0.8 + i * 1.1
        p = ease_out(prog(t, st, 0.4))
        if p <= 0:
            continue
        y = 790 + i * 210
        rrect(b, (90, y - 80 + (1 - p) * 40, 990, y + 80 + (1 - p) * 40), 36, PANEL, p, outline=col, width=4)
        txt(b, a, 76, col, 130, y + (1 - p) * 40, BLACK, alpha=p, anchor="l")
        txt(b, txt_, 50, WHITE, 420, y + (1 - p) * 40, BOLD, alpha=p, anchor="l")
    pop(b, "Keine Gefühle. Nur Regeln.", 72, WHITE, 1520, t, 4.4)
    return b


def s4(t):  # Der Trade
    b = background(t); header(b)
    pop(b, "Berts erster Trade:", 92, WHITE, 410, t, 0.0)
    p = ease_out(prog(t, 0.5, 0.4))
    if p > 0:
        dy = (1 - p) * 60
        rrect(b, (90, 520 + dy, 990, 1260 + dy), 44, PANEL, p, outline=BLUE, width=4)
        txt(b, "18:28 Uhr  (12:28 in New York)", 44, GREY, W / 2, 600 + dy, BOLD, alpha=p)
        txt(b, "KAUF: TESLA", 110, BLUE, W / 2, 730 + dy, alpha=p)
    pop(b, "6 Aktien × 384,71 $", 72, WHITE, 880, t, 1.4, BOLD)
    pop(b, "= 2.308 $ investiert", 72, YELLOW, 980, t, 2.2)
    pop(b, "Grund: Trend dreht nach oben", 52, WHITE, 1120, t, 3.2, BOLD)
    pop(b, "(Blau über Gelb)", 46, GREY, 1190, t, 3.6, BOLD)
    pop(b, "Und dann?", 92, WHITE, 1430, t, 5.2)
    return b


EQ = [("16:13", 10000.00), ("17:18", 10000.00), ("18:28", 10000.00), ("19:20", 9997.03),
      ("20:28", 9988.96), ("21:28", 9991.60), ("22:25", 9987.52)]


def s5(t):  # Kontoverlauf (echte Daten)
    b = background(t); header(b)
    pop(b, "Berts Konto heute:", 92, WHITE, 410, t, 0.0)
    p = ease_out(prog(t, 0.4, 0.3))
    if p > 0:
        rrect(b, (80, 520, 1000, 1130), 36, PANEL, p)
    box = (150, 600, 930, 1020)
    q = ease_out(prog(t, 0.7, 2.6))
    if q > 0:
        vals = [v for _, v in EQ]
        pts = lines_layer(b, [(vals, BLUE)], box, q, 9984, 10002, widths=[10])
        # Startlinie 10.000
        layer = Image.new("RGBA", b.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ys = box[3] - (box[3] - box[1]) * (10000 - 9984) / (10002 - 9984)
        for x in range(box[0], box[2], 30):
            d.line([(x, ys), (x + 15, ys)], fill=GREY + (160,), width=3)
        n = max(1, int(len(pts[0]) * q))
        ex, ey = pts[0][n - 1]
        d.ellipse((ex - 14, ey - 14, ex + 14, ey + 14), fill=WHITE + (255,))
        b.alpha_composite(layer)
        txt(b, "Start 10.000 $", 34, GREY, box[0], ys - 30, SEMI, alpha=q, anchor="l")
        txt(b, "16 Uhr", 32, GREY, box[0], 1075, SEMI, alpha=q, anchor="l")
        txt(b, "22 Uhr", 32, GREY, box[2] - 90, 1075, SEMI, alpha=q, anchor="l")
    pop(b, money(9987.52) + " $", 120, WHITE, 1280, t, 3.2)
    pop(b, "−12,48 $  (−0,12 %)", 72, RED, 1410, t, 3.7)
    pop(b, "Tesla fiel nach dem Kauf leicht.", 56, GREY, 1530, t, 4.6, BOLD)
    return b


def s6(t):  # Der Fehler
    b = background(t); header(b)
    pop(b, "22:00 Uhr:", 110, WHITE, 470, t, 0.0)
    pop(b, "Börse schließt.", 110, WHITE, 590, t, 0.3)
    pop(b, "Bert hätte Tesla", 80, WHITE, 770, t, 1.3, BOLD)
    pop(b, "verkaufen müssen.", 80, WHITE, 860, t, 1.5, BOLD)
    q = prog(t, 2.6, 0.35)
    if q > 0:
        st = text_img("HAT ER NICHT", BLACK, 110, RED)
        pad = 30
        bx = Image.new("RGBA", (st.width + pad * 2, st.height + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(bx).rounded_rectangle((4, 4, bx.width - 4, bx.height - 4), 24, outline=RED + (255,), width=12)
        bx.alpha_composite(st, (pad, pad))
        bx = bx.rotate(-7, expand=True, resample=Image.BICUBIC)
        place(b, bx, W / 2, 1040, alpha=min(1, q * 2), scale=2.2 - 1.2 * ease_out(q))
    pop(b, "Sein Wecker kam nur", 66, WHITE, 1250, t, 4.0, BOLD)
    pop(b, "ca. jede Stunde statt", 66, WHITE, 1335, t, 4.2, BOLD)
    pop(b, "alle 15 Minuten.", 66, WHITE, 1420, t, 4.4, BOLD)
    pop(b, "Er hat den Schluss verschlafen.", 66, YELLOW, 1540, t, 5.6)
    return b


def s7(t):  # Update #1
    b = background(t); header(b)
    p = prog(t, 0.0, 0.4)
    if p > 0:
        tag = text_img("UPDATE #1", BLACK, 120, (10, 14, 26))
        w, h = tag.width + 100, tag.height + 50
        bx = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(bx).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=YELLOW + (255,))
        bx.alpha_composite(tag, ((w - tag.width) // 2, (h - tag.height) // 2))
        place(b, bx, W / 2, 470, alpha=ease_out(p), scale=0.6 + 0.4 * ease_back(p))
    pop(b, "Nach jedem Kauf stellt Bert", 64, WHITE, 680, t, 0.9, BOLD)
    pop(b, "sofort eine Verkaufsorder", 64, WHITE, 765, t, 1.1, BOLD)
    pop(b, "zum Börsenschluss.", 64, YELLOW, 850, t, 1.3)
    pop(b, "Egal wann er aufwacht:", 64, WHITE, 1010, t, 2.8, BOLD)
    pop(b, "Er verkauft rechtzeitig.", 64, GREEN, 1095, t, 3.1)
    pop(b, "Und Tesla?", 80, WHITE, 1290, t, 4.6)
    pop(b, "Fliegt morgen zum", 64, WHITE, 1400, t, 5.2, BOLD)
    pop(b, "Börsenstart raus.", 64, WHITE, 1485, t, 5.4, BOLD)
    return b


def s8(t):  # Kurt
    b = background(t); header(b)
    robot(b, KURT, W / 2, 560, t, 0.0, 0.75)
    pop(b, "Und Kurt?", 120, GREEN, 820, t, 0.3)
    pop(b, "0 Tipps.", 100, WHITE, 960, t, 1.2)
    pop(b, "Bayern – Köln am Freitag:", 60, WHITE, 1110, t, 2.2, BOLD)
    pop(b, "ausgelassen. Zu riskant.", 60, GREY, 1190, t, 2.6, BOLD)
    pop(b, "Morgen sucht er Tipps", 66, YELLOW, 1340, t, 3.8)
    pop(b, "fürs Wochenende.", 66, YELLOW, 1425, t, 4.0)
    return b


def s9(t):  # Zwischenstand
    b = background(t); header(b)
    pop(b, "ZWISCHENSTAND", 110, YELLOW, 450, t, 0.0)
    data = [("BERT", BERT, money(9987.52) + " $", "−0,12 %", BLUE, RED),
            ("KURT", KURT, "10.000,00 €", "±0,00 %", GREEN, GREY)]
    for i, (name, img, amt, pct, col, pcol) in enumerate(data):
        cx = 290 + i * 500
        p = prog(t, 0.3 + i * 0.2, 0.4)
        if p > 0:
            e = ease_out(p)
            rrect(b, (cx - 225, 580, cx + 225, 1170), 44, PANEL, e, outline=col, width=5)
            robot(b, img, cx, 750, t, 0.3 + i * 0.2, 0.55)
            txt(b, name, 70, col, cx, 945, alpha=e)
            txt(b, amt, 52, WHITE, cx, 1030, BOLD, alpha=e)
            txt(b, pct, 52, pcol, cx, 1100, BOLD, alpha=e)
    pop(b, "Kurt führt.", 92, WHITE, 1320, t, 1.8)
    pop(b, "Ohne einen einzigen Tipp.", 64, GREY, 1430, t, 2.5, BOLD)
    return b


def s10(t):  # Beweis + CTA
    b = background(t); header(b)
    pop(b, "Jeder Trade wird", 84, WHITE, 430, t, 0.0, BOLD)
    pop(b, "gespeichert:", 84, WHITE, 520, t, 0.15, BOLD)
    p = ease_out(prog(t, 0.6, 0.35))
    if p > 0:
        rrect(b, (70, 610, 1010, 900), 32, (8, 11, 20), p, outline=(45, 58, 92), width=3)
        d = ImageDraw.Draw(b)
        f = font(MONO, 36)
        lines = [("18:28  TSLA  KAUF  6 Stk.", BLUE), ("Preis: 384,71 $", WHITE),
                 ("Grund: Trend dreht nach oben", WHITE), ("        (EMA9 > EMA21, RSI 60)", GREY)]
        for i, (l, c) in enumerate(lines):
            a = ease_out(prog(t, 0.8 + i * 0.25, 0.3))
            if a > 0:
                d.text((110, 650 + i * 58), l, font=f, fill=c + (int(255 * a),))
    pop(b, "Uhrzeit. Preis. Grund.", 64, YELLOW, 980, t, 1.9)
    pop(b, "Morgen: Verkauft Bert", 76, WHITE, 1140, t, 2.8, BOLD)
    pop(b, "Tesla mit Gewinn?", 76, BLUE, 1235, t, 3.0)
    q = prog(t, 3.8, 0.4)
    if q > 0:
        pulse = 1 + 0.04 * math.sin((t - 3.8) * 6)
        btn = text_img("FOLGEN  →", BLACK, 80, (10, 14, 26))
        w, h = btn.width + 120, btn.height + 70
        bx = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(bx).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=YELLOW + (255,))
        bx.alpha_composite(btn, ((w - btn.width) // 2, (h - btn.height) // 2))
        place(b, bx, W / 2, 1420, alpha=ease_out(q), scale=pulse * (0.6 + 0.4 * ease_back(q)))
    return b


SCENES = [("s1", s1, 4.5), ("s2", s2, 9.0), ("s3", s3, 6.5), ("s4", s4, 7.0), ("s5", s5, 7.0),
          ("s6", s6, 8.0), ("s7", s7, 8.0), ("s8", s8, 6.0), ("s9", s9, 5.5), ("s10", s10, 6.5)]

if __name__ == "__main__":
    if sys.argv[1:] == ["stills"]:
        for name, fn, t in [("s1", s1, 4.0), ("s2", s2, 8.5), ("s3", s3, 6.0), ("s4", s4, 6.5),
                            ("s5", s5, 6.5), ("s6", s6, 7.5), ("s7", s7, 7.5), ("s8", s8, 5.5),
                            ("s9", s9, 5.0), ("s10", s10, 6.0)]:
            fn(t).convert("RGB").save(os.path.join(f1.OUT, f"still_{name}.jpg"), quality=90)
    else:
        for name, fn, dur in SCENES:
            f1.render_scene(name, fn, dur)
            print("fertig:", name, flush=True)
