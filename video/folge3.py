#!/usr/bin/env python3
"""Folge 3 – Tag 2 (Daten vom 19.11.). Nutzt die Bausteine aus Folge 1."""
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
    pill = text_img("KI GEGEN DAS SYSTEM  ·  FOLGE 3  ·  TAG 2", SEMI, 34, GREY)
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


def stamp(b, text, col, cx, cy, q, rot=-7):
    if q <= 0:
        return
    st = text_img(text, BLACK, 100, col)
    pad = 30
    bx = Image.new("RGBA", (st.width + pad * 2, st.height + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(bx).rounded_rectangle((4, 4, bx.width - 4, bx.height - 4), 24, outline=col + (255,), width=12)
    bx.alpha_composite(st, (pad, pad))
    bx = bx.rotate(rot, expand=True, resample=Image.BICUBIC)
    place(b, bx, W / 2, cy, alpha=min(1, q * 2), scale=2.2 - 1.2 * ease_out(q))


# ------------------------------------------------------------------ Echte Daten (data/, 19.11.)
BUY_PRICE, SELL_PRICE, QTY = 384.71, 379.52, 6
TRADE_PL, TRADE_PCT = -31.14, -1.35
EQ = [("15:24", 10041.81), ("16:35", 9970.50), ("17:42", 9968.85), ("18:43", 9968.85),
      ("19:43", 9968.85), ("20:50", 9968.85), ("21:43", 9968.85)]
BERT_END, BERT_PL, BERT_PCT = 9968.85, -31.15, -0.31
KURT_GAMES = [  # Samstag, 21.11. – geprüft um 10:58
    ("Leverkusen – Paderborn", "Quote 10,50", RED),
    ("Union Berlin – Leipzig", "+1,5 %", GREY),
    ("Elversberg – Freiburg", "+0,4 %", GREY),
    ("Gladbach – Dortmund", "−0,5 %", GREY),
    ("Schalke – Stuttgart", "−0,5 %", GREY),
    ("Frankfurt – Hoffenheim", "−1,2 %", GREY),
]


# ------------------------------------------------------------------ Szenen
def s1(t):  # Hook
    b = background(t); header(b)
    pop(b, "TAG 2", 220, YELLOW, 620, t, 0.0)
    pop(b, "Bert verkauft Tesla.", 96, WHITE, 830, t, 0.6)
    pop(b, "Mit Verlust.", 110, RED, 980, t, 1.8)
    return b


def s2(t):  # Der Morgen
    b = background(t); header(b)
    pop(b, "15:24 Uhr", 110, WHITE, 450, t, 0.0)
    pop(b, "kurz vor Börsenstart", 56, GREY, 560, t, 0.3, BOLD)
    p = ease_out(prog(t, 0.9, 0.4))
    if p > 0:
        dy = (1 - p) * 50
        rrect(b, (130, 650 + dy, 950, 900 + dy), 40, PANEL, p, outline=GREEN, width=4)
        txt(b, "Berts Konto:", 46, GREY, W / 2, 715 + dy, BOLD, alpha=p)
        txt(b, "+41,81 $", 110, GREEN, W / 2, 815 + dy, alpha=p)
    pop(b, "Tesla vom Vortag", 66, WHITE, 1030, t, 2.0, BOLD)
    pop(b, "noch im Depot.", 66, WHITE, 1115, t, 2.2, BOLD)
    pop(b, "Aber Bert schläft.", 92, YELLOW, 1290, t, 3.4)
    pop(b, "Er wacht erst um", 66, WHITE, 1440, t, 4.8, BOLD)
    pop(b, "16:35 Uhr auf.", 66, WHITE, 1525, t, 5.0, BOLD)
    return b


def s3(t):  # Der Verkauf
    b = background(t); header(b)
    pop(b, "Der Verkauf:", 92, WHITE, 410, t, 0.0)
    p = ease_out(prog(t, 0.4, 0.4))
    if p > 0:
        dy = (1 - p) * 60
        rrect(b, (90, 510 + dy, 990, 1240 + dy), 44, PANEL, p, outline=BLUE, width=4)
        txt(b, "16:35 Uhr  (10:35 in New York)", 44, GREY, W / 2, 590 + dy, BOLD, alpha=p)
        txt(b, "VERKAUF: TESLA", 88, BLUE, W / 2, 710 + dy, alpha=p)
    pop(b, f"{QTY} Aktien × {money(SELL_PRICE)} $", 70, WHITE, 850, t, 1.3, BOLD)
    pop(b, f"gekauft für {money(BUY_PRICE)} $", 56, GREY, 940, t, 2.3, BOLD)
    pop(b, f"{money(TRADE_PL)} $  ({money(TRADE_PCT)} %)".replace("-", "−"), 84, RED, 1060, t, 3.4)
    pop(b, "Grund: Position vom Vortag", 50, WHITE, 1170, t, 4.4, BOLD)
    pop(b, "Daytrading = nichts behalten.", 50, GREY, 1340, t, 5.4, BOLD)
    return b


def s4(t):  # Konto heute
    b = background(t); header(b)
    pop(b, "Berts Konto heute:", 92, WHITE, 410, t, 0.0)
    p = ease_out(prog(t, 0.4, 0.3))
    if p > 0:
        rrect(b, (80, 520, 1000, 1130), 36, PANEL, p)
    box = (150, 620, 930, 1010)
    lo, hi = 9955, 10055
    q = ease_out(prog(t, 0.7, 2.4))
    if q > 0:
        vals = [v for _, v in EQ]
        pts = lines_layer(b, [(vals, BLUE)], box, q, lo, hi, widths=[10])
        layer = Image.new("RGBA", b.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ys = box[3] - (box[3] - box[1]) * (10000 - lo) / (hi - lo)
        for x in range(box[0], box[2], 30):
            d.line([(x, ys), (x + 15, ys)], fill=GREY + (160,), width=3)
        n = max(1, int(len(pts[0]) * q))
        ex, ey = pts[0][n - 1]
        d.ellipse((ex - 14, ey - 14, ex + 14, ey + 14), fill=WHITE + (255,))
        b.alpha_composite(layer)
        txt(b, "Start 10.000 $", 34, GREY, box[2] - 230, ys - 30, SEMI, alpha=q, anchor="l")
        txt(b, "15:24", 32, GREY, box[0] - 20, 1075, SEMI, alpha=q, anchor="l")
        txt(b, "21:43", 32, GREY, box[2] - 70, 1075, SEMI, alpha=q, anchor="l")
        if q > 0.3:
            sx, sy = pts[0][1]
            txt(b, "Verkauf", 36, RED, sx + 30, sy - 40, BOLD, alpha=ease_out(prog(t, 1.6, 0.3)), anchor="l")
    pop(b, "Danach: kein Kaufsignal.", 70, WHITE, 1260, t, 3.3)
    pop(b, "Bert kauft nichts mehr.", 62, GREY, 1360, t, 4.0, BOLD)
    pop(b, money(BERT_END) + " $", 100, WHITE, 1500, t, 5.0)
    pop(b, f"{money(BERT_PL)} $  ({money(BERT_PCT)} %)".replace("-", "−"), 60, RED, 1610, t, 5.4, BOLD)
    return b


def s5(t):  # Das Problem
    b = background(t); header(b)
    pop(b, "Das Problem:", 110, RED, 470, t, 0.0)
    pop(b, "Bert wacht nur", 80, WHITE, 650, t, 0.8, BOLD)
    pop(b, "ca. 1× pro Stunde auf.", 80, WHITE, 745, t, 1.0, BOLD)
    stamp(b, "ZU LANGSAM", RED, W / 2, 980, prog(t, 2.2, 0.35))
    pop(b, "Beim Daytrading zählt", 66, WHITE, 1230, t, 3.6, BOLD)
    pop(b, "jede Minute.", 66, YELLOW, 1315, t, 3.8)
    return b


def s6(t):  # Update #2
    b = background(t); header(b)
    p = prog(t, 0.0, 0.4)
    if p > 0:
        tag = text_img("UPDATE #2", BLACK, 120, (10, 14, 26))
        w, h = tag.width + 100, tag.height + 50
        bx = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(bx).rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=YELLOW + (255,))
        bx.alpha_composite(tag, ((w - tag.width) // 2, (h - tag.height) // 2))
        place(b, bx, W / 2, 470, alpha=ease_out(p), scale=0.6 + 0.4 * ease_back(p))
    pop(b, "Das Projekt ist jetzt", 66, WHITE, 670, t, 0.9, BOLD)
    pop(b, "öffentlich.", 90, GREEN, 770, t, 1.1)
    pop(b, "Jeder Trade live nachprüfbar:", 50, WHITE, 900, t, 2.2, BOLD)
    q = ease_out(prog(t, 2.6, 0.35))
    if q > 0:
        rrect(b, (110, 950, 970, 1040), 26, (8, 11, 20), q, outline=(45, 58, 92), width=3)
        txt(b, "GitHub: ki-gegen-das-system", 42, BLUE, W / 2, 995, MONO, alpha=q)
    pop(b, "Dadurch darf Bert länger laufen:", 54, WHITE, 1180, t, 4.2, BOLD)
    pop(b, "Ab morgen prüft er", 76, WHITE, 1300, t, 5.4)
    pop(b, "alle 5 Minuten.", 90, YELLOW, 1410, t, 5.7)
    return b


def s7(t):  # Kurt
    b = background(t); header(b)
    robot(b, KURT, 165, 400, t, 0.0, 0.36)
    pop(b, "Und Kurt?", 100, GREEN, 400, t, 0.2, cx=W / 2 + 80)
    pop(b, "6 Samstagsspiele geprüft:", 54, WHITE, 580, t, 0.8, BOLD)
    for i, (game, val, col) in enumerate(KURT_GAMES):
        a = ease_out(prog(t, 1.4 + i * 0.3, 0.3))
        if a <= 0:
            continue
        y = 690 + i * 105
        rrect(b, (70, y - 45, 1010, y + 45), 22, PANEL, a)
        txt(b, game, 42, WHITE, 105, y, BOLD, alpha=a, anchor="l")
        vi = text_img(val, BOLD, 42, col)
        place(b, vi, 980 - vi.width, y, alpha=a, anchor="l")
    pop(b, "Kurt tippt erst ab +3 % Value.", 56, YELLOW, 1330, t, 3.6)
    pop(b, "Paderborn: zu riskant.", 52, GREY, 1420, t, 4.4, BOLD)
    pop(b, "0 Tipps.", 100, WHITE, 1560, t, 5.4)
    return b


def s8(t):  # Zwischenstand
    b = background(t); header(b)
    pop(b, "ZWISCHENSTAND", 110, YELLOW, 450, t, 0.0)
    data = [("BERT", BERT, money(BERT_END) + " $", money(BERT_PCT).replace("-", "−") + " %", BLUE, RED),
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
    pop(b, "Immer noch ohne Tipp.", 64, GREY, 1430, t, 2.5, BOLD)
    return b


def s9(t):  # Cliffhanger + CTA
    b = background(t); header(b)
    robot(b, BERT, W / 2, 560, t, 0.0, 0.75)
    pop(b, "Morgen:", 92, WHITE, 830, t, 0.3)
    pop(b, "Bert zum ersten Mal", 76, WHITE, 960, t, 0.8, BOLD)
    pop(b, "den ganzen Tag wach.", 76, BLUE, 1055, t, 1.0)
    pop(b, "Holt er die 31 $ zurück?", 66, YELLOW, 1200, t, 2.4)
    return b


SCENES = [("s1", s1, 4.0), ("s2", s2, 8.0), ("s3", s3, 8.5), ("s4", s4, 7.5), ("s5", s5, 6.0),
          ("s6", s6, 9.5), ("s7", s7, 8.5), ("s8", s8, 5.5), ("s9", s9, 6.5)]

if __name__ == "__main__":
    if sys.argv[1:] == ["stills"]:
        for name, fn, dur in SCENES:
            fn(dur - 0.4).convert("RGB").save(os.path.join(f1.OUT, f"still_{name}.jpg"), quality=90)
    else:
        for name, fn, dur in SCENES:
            f1.render_scene(name, fn, dur)
            print("fertig:", name, flush=True)
