#!/usr/bin/env python3
"""
Video-Baukasten v2 – „KI gegen das System"
=========================================
Baut eine Folge aus einer Folgen-Datei (video/folgen/folgeN.json) und den ECHTEN Daten in data/.
Look: ruhiges Börsen-Terminal, echte Charts, Untertitel synchron zur Stimme, Transparenz-Zeile.

Ablauf (siehe video/ANLEITUNG.md):
  1. python3 video/baukasten.py text   video/folgen/folgeN.json   -> schreibt stimme/folgeN.txt
  2. stimme/folgeN.txt pushen -> GitHub-Workflow „Stimme" erzeugt stimme/folgeN/clips.json + WAVs -> pullen
  3. python3 video/baukasten.py stills video/folgen/folgeN.json   -> Standbilder zum Prüfen
  4. python3 video/baukasten.py render video/folgen/folgeN.json   -> fertiges MP4 in $RENDER_DIR

Szenen-Typen (Feld "typ"):
  hook    – großer Einstieg:            "gross", "zeilen": [..], optional "farbe"
  chart   – echter Kerzen-Chart:        "symbol", optional "datum", "markierungen": [{"zeit": "16:35", "text": ".."}]
  trades  – Berts Entscheidungen (Log): optional "datum" (liest data/bert_entscheidungen.csv)
  konto   – Berts Kontoverlauf am Tag:  optional "datum"
  kurt    – Kurts Rechnung (Tabelle):   optional "datum", "max" (Standard 5)
  tipps   – Kurts Tipps mit Ergebnis:   optional "von", "bis" (Anstoß-Datum JJJJ-MM-TT), "titel"
  value   – Erklärung „Was heißt Value?" (Münzwurf)
  update  – Update-Hinweis:             "nummer", "titel", "punkte": [..]
  stand   – Zwischenstand Bert vs. Kurt in Prozent
  frage   – Cliffhanger-Frage:          "zeilen": [..]
  text    – freie Textfolie:            "titel", "zeilen": [..], optional "titel_farbe";
            eine Zeile darf auch {"text": "..", "farbe": "rot|gruen|blau|gelb|orange|grau"} sein
  woche   – Chart über mehrere Tage:    "symbol", "von", "bis" (JJJJ-MM-TT), z. B. Wochenrückblick
  nachrechnung – „Was wäre, wenn …?":   "von", "bis", optional "titel"
            (liest data/nachrechnung/bert_<von>_bis_<bis>.csv aus nachrechnung.py – KEINE echten Trades)
Jede Szene hat "sprecher": [Satz, ...]. Ein Satz ist entweder Text (Zahlen als Wörter!) oder
{"sag": "gesprochen, Zahlen als Wörter", "zeig": "Untertitel, Zahlen als Ziffern"}.
"""
import csv
import json
import math
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from folge1 import font, text_img, ease_out, ease_back, make_robot, BLACK, BOLD, SEMI, MONO, W, H, FPS  # noqa: E402

DATA = os.path.join(REPO, "data")
RENDER = os.environ.get("RENDER_DIR", "/tmp/render")
REGULAR = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
MONO_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

BG = (7, 10, 18)
PANEL = (13, 18, 31)
LINE = (34, 44, 70)
WHITE = (240, 244, 250)
GREY = (150, 160, 184)
DIM = (92, 104, 132)
BLUE = (61, 165, 255)
GREEN = (46, 229, 157)
RED = (255, 77, 94)
YELLOW = (255, 210, 63)
ORANGE = (255, 159, 67)

TOP = 390          # Inhalt beginnt hier
BOTTOM = 1215      # ... und endet hier (darunter Untertitel, ganz unten TikTok-Beschreibung)
SUB_Y = 1330       # Mitte der Untertitel
SUB_X = 520        # leicht links, damit die TikTok-Knöpfe rechts nichts verdecken
HEAD, GAP, TAIL = 0.30, 0.22, 0.45   # Pausen um die Sätze (Sekunden)

TEAMS = {
    "Bayern Munich": "FC Bayern", "Borussia Monchengladbach": "Mönchengladbach",
    "Borussia Dortmund": "Dortmund", "Bayer Leverkusen": "Leverkusen", "FSV Mainz 05": "Mainz 05",
    "Eintracht Frankfurt": "Frankfurt", "TSG Hoffenheim": "Hoffenheim", "VfB Stuttgart": "Stuttgart",
    "FC Schalke 04": "Schalke 04", "SC Freiburg": "Freiburg", "Werder Bremen": "Werder Bremen",
    "Manchester United": "Man United", "Manchester City": "Man City", "Tottenham Hotspur": "Tottenham",
    "Brighton and Hove Albion": "Brighton", "Nottingham Forest": "Nottingham", "Newcastle United": "Newcastle",
    "Inter Milan": "Inter Mailand", "AC Milan": "AC Mailand", "Atalanta BC": "Atalanta", "AS Roma": "AS Rom",
    "Paris Saint Germain": "Paris SG", "Real Racing Club de Santander": "Racing Santander",
    "Atlético Madrid": "Atlético", "Deportivo La Coruña": "La Coruña", "CA Osasuna": "Osasuna",
    "Athletic Bilbao": "Bilbao", "AS Monaco": "Monaco", "Olympique Lyonnais": "Lyon",
}
NAMES = {"TSLA": "Tesla", "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AMZN": "Amazon",
         "META": "Meta", "SPY": "S&P 500 (ETF)", "QQQ": "Nasdaq 100 (ETF)"}


# ------------------------------------------------------------------ Hilfen
def team(n):
    return TEAMS.get(n, n.replace("Monchengladbach", "Mönchengladbach"))


def num(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, d=2):
    return ("+" if v > 0 else "−" if v < 0 else "±") + num(abs(v), d) + " %"


def signed(v, d=2, unit=""):
    return ("+" if v > 0 else "−" if v < 0 else "±") + num(abs(v), d) + unit


COLORS = {"rot": RED, "gruen": GREEN, "blau": BLUE, "gelb": YELLOW, "orange": ORANGE, "grau": GREY,
          "weiss": WHITE}
WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def color(name, default):
    return COLORS.get(name, default) if name else default


def weekday(iso):
    import datetime as _dt
    return WEEKDAYS[_dt.date.fromisoformat(iso).weekday()]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(f, start, length):
    return clamp((f - start) / length) if length > 0 else (1.0 if f >= start else 0.0)


def read_csv(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def de_date(iso):
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def put(base, img, cx, cy, alpha=1.0, scale=1.0, anchor="c"):
    if alpha <= 0.003:
        return
    if abs(scale - 1) > 0.005:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
    x = {"c": cx - img.width / 2, "l": cx, "r": cx - img.width}[anchor]
    base.alpha_composite(img, (int(x), int(cy - img.height / 2)))


def T(base, s, size, color, cx, cy, path=BLACK, alpha=1.0, anchor="c", scale=1.0):
    put(base, text_img(s, path, size, color), cx, cy, alpha, scale, anchor)


def appear(base, s, size, color, cy, f, start, path=BLACK, cx=W / 2, anchor="c", dur=0.06):
    p = prog(f, start, dur)
    if p > 0:
        T(base, s, size, color, cx, cy + (1 - ease_out(p)) * 28, path, ease_out(p), anchor)


def panel(base, box, outline=LINE, fill=PANEL, alpha=1.0, r=28, width=2):
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(box, r, fill=fill + (int(235 * alpha),),
                                          outline=outline + (int(255 * alpha),), width=width)
    base.alpha_composite(lay)


def fit(s, path, size, maxw):
    while size > 18 and font(path, size).getlength(s) > maxw:
        size -= 2
    return size


# ------------------------------------------------------------------ Grundbild
def _base():
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 90):
        d.line([(x, 0), (x, H)], fill=(13, 18, 30, 255), width=1)
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(13, 18, 30, 255), width=1)
    return img


BASE = _base()
ICON_B = make_robot(BLUE, "bert", 120).resize((60, 60), Image.LANCZOS)
ICON_K = make_robot(GREEN, "kurt", 120).resize((60, 60), Image.LANCZOS)


def chrome(img, ep):
    """Kopfzeile + Transparenz-Zeile (auf jeder Szene gleich)."""
    img.alpha_composite(ICON_B, (70, 225))
    img.alpha_composite(ICON_K, (118, 225))
    T(img, "KI GEGEN DAS SYSTEM", 32, WHITE, 196, 256, SEMI, anchor="l")
    T(img, f"FOLGE {ep['folge']} · {ep.get('titel', '')}".strip(" ·"), 28, GREY, 1010, 256, MONO, anchor="r")
    d = ImageDraw.Draw(img)
    d.line([(70, 302), (1010, 302)], fill=LINE + (255,), width=2)
    T(img, "Demokonto · kein echtes Geld · alle Trades öffentlich auf GitHub", 26, DIM, W / 2, 336, SEMI)


# ------------------------------------------------------------------ Daten
def chart_day(day):
    p = os.path.join(DATA, "charts", f"{day}.json")
    if not os.path.exists(p):
        raise SystemExit(f"Chartdaten fehlen: {p} – Workflow „Chartdaten“ starten.")
    return json.load(open(p, encoding="utf-8"))


def trades_on(day, symbol=None):
    out = []
    for r in read_csv("bert_trades.csv"):
        if r["zeit"].startswith(day) and (symbol is None or r["symbol"] == symbol):
            out.append(r)
    return out


def equity_rows(day=None):
    rows = read_csv("bert_kontostand.csv")
    return [r for r in rows if day is None or r["zeit"].startswith(day)]


def latest_before(rows, day):
    sel = [r for r in rows if r["zeit"][:10] <= day]
    return sel[-1] if sel else None


# ------------------------------------------------------------------ Szenen
class Scene:
    """Basis: f = Fortschritt 0..1 innerhalb der Szene, t = Sekunden in der Szene."""

    def __init__(self, spec, ep):
        self.s, self.ep = spec, ep
        self.day = spec.get("datum", ep["datum"])

    def prepare(self, dur):
        self.dur = dur

    def frame(self, t):
        img = BASE.copy()
        chrome(img, self.ep)
        self.draw(img, t / self.dur if self.dur else 1.0, t)
        return img

    def draw(self, img, f, t):
        pass


class Hook(Scene):
    def prepare(self, dur):
        super().prepare(dur)
        self.bg = None
        try:
            sym = self.s.get("symbol", "SPY")
            data = chart_day(self.day)["symbole"].get(sym)
            if data:
                closes = [k[4] for k in data["kerzen"]]
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                d = ImageDraw.Draw(lay)
                lo, hi = min(closes), max(closes)
                pts = [(60 + 960 * i / (len(closes) - 1), 1150 - 600 * (c - lo) / ((hi - lo) or 1))
                       for i, c in enumerate(closes)]
                col = GREEN if closes[-1] >= closes[0] else RED
                d.line(pts, fill=col + (60,), width=10, joint="curve")
                self.bg = lay.filter(ImageFilter.GaussianBlur(2))
        except SystemExit:
            pass

    def draw(self, img, f, t):
        if self.bg:
            img.alpha_composite(self.bg)
        col = {"rot": RED, "gruen": GREEN, "blau": BLUE, "gelb": YELLOW}.get(self.s.get("farbe", "gelb"), YELLOW)
        p = prog(t, 0, 0.35)
        T(img, self.s["gross"], fit(self.s["gross"], BLACK, 200, 940), col, W / 2, 620, alpha=ease_out(p),
          scale=0.85 + 0.15 * ease_back(p))
        for i, z in enumerate(self.s.get("zeilen", [])):
            appear(img, z, fit(z, BLACK, 76, 940), WHITE, 820 + i * 100, f, 0.12 + i * 0.18)


class Chart(Scene):
    def prepare(self, dur):
        super().prepare(dur)
        self.sym = self.s["symbol"]
        day = chart_day(self.day)
        d = day["symbole"][self.sym]
        self.k, self.e9, self.e21 = d["kerzen"], d["ema9"], d["ema21"]
        self.trades = trades_on(self.day, self.sym)
        lows = [x[3] for x in self.k] + [float(t["preis_usd"]) for t in self.trades]
        highs = [x[2] for x in self.k] + [float(t["preis_usd"]) for t in self.trades]
        lo, hi = min(lows + self.e21 + self.e9), max(highs + self.e21 + self.e9)
        pad = (hi - lo) * 0.08
        self.lo, self.hi = lo - pad, hi + pad
        self.box = (90, 565, 900, 1095)  # Plotbereich (rechts Preisachse)
        self.lines = [(float(l["preis"]), l.get("text", "")) for l in self.s.get("linien", [])]
        for v, _ in self.lines:
            lo, hi = min(lo, v - pad), max(hi, v + pad)
            self.lo, self.hi = min(self.lo, v - pad), max(self.hi, v + pad)
        # statischer Teil
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        panel(st, (60, 410, 1020, 1200))
        x0, y0, x1, y1 = self.box
        dr = ImageDraw.Draw(st)
        for i in range(5):
            v = self.lo + (self.hi - self.lo) * i / 4
            y = self.y(v)
            dr.line([(x0, y), (x1, y)], fill=LINE + (255,), width=1)
            T(st, num(v), 26, DIM, x1 + 14, y, MONO_REG, anchor="l")
        for lab in ("15:30", "17:00", "18:30", "20:00", "21:30"):
            idx = next((i for i, c in enumerate(self.k) if c[0] == lab), None)
            if idx is not None:
                T(st, lab, 26, DIM, self.x(idx), y1 + 30, MONO_REG)
        first, last = self.k[0][1], self.k[-1][4]
        ch = (last / first - 1) * 100
        T(st, self.sym, 56, WHITE, 90, 465, BLACK, anchor="l")
        T(st, NAMES.get(self.sym, ""), 34, GREY, 90 + font(BLACK, 56).getlength(self.sym) + 20, 470, SEMI, anchor="l")
        T(st, pct(ch), 40, GREEN if ch >= 0 else RED, 990, 465, BLACK, anchor="r")
        T(st, f"{de_date(self.day)} · Schluss {num(last)} $", 28, GREY, 90, 515, SEMI, anchor="l")
        T(st, "Quelle: Alpaca (IEX)", 24, DIM, 990, 515, SEMI, anchor="r")
        T(st, "—— schnelle Linie (Ø ~2 Std.)", 26, BLUE, 90, 1170, SEMI, anchor="l")
        T(st, "—— langsame Linie (Ø ~5 Std.)", 26, YELLOW, 990, 1170, SEMI, anchor="r")
        for v, label in self.lines:
            y = self.y(v)
            for xx in range(x0, x1, 22):
                dr.line([(xx, y), (xx + 12, y)], fill=GREY + (230,), width=3)
            if label:
                T(st, label, 26, WHITE, x1 - 6, y - 22, SEMI, anchor="r")
        self.static = st

    def x(self, i):
        x0, _, x1, _ = self.box
        return x0 + (x1 - x0) * (i + 0.5) / len(self.k)

    def y(self, v):
        _, y0, _, y1 = self.box
        return y1 - (y1 - y0) * (v - self.lo) / (self.hi - self.lo)

    def idx_of(self, hhmm):
        h, m = map(int, hhmm.split(":"))
        tm = h * 60 + m
        best = 0
        for i, c in enumerate(self.k):
            ch, cm = map(int, c[0].split(":"))
            if ch * 60 + cm <= tm:
                best = i
        frac = (tm - (int(self.k[best][0][:2]) * 60 + int(self.k[best][0][3:]))) / 15
        return best + clamp(frac, 0, 0.99) - 0.5

    def draw(self, img, f, t):
        img.alpha_composite(self.static)
        n = len(self.k)
        reveal = ease_out(prog(f, 0.05, 0.6)) * n
        shown = int(reveal)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cw = (self.box[2] - self.box[0]) / n * 0.62
        for i in range(min(n, shown + 1)):
            a = 1.0 if i < shown else reveal - shown
            if a <= 0:
                continue
            _, o, h, l, c, _ = self.k[i]
            col = GREEN if c >= o else RED
            x = self.x(i)
            d.line([(x, self.y(h)), (x, self.y(l))], fill=col + (int(255 * a),), width=3)
            top, bot = sorted((self.y(o), self.y(c)))
            d.rectangle((x - cw / 2, top, x + cw / 2, max(bot, top + 2)), fill=col + (int(255 * a),))
        m = max(2, min(n, int(reveal + 0.999)))
        for vals, col in ((self.e21, YELLOW), (self.e9, BLUE)):
            pts = [(self.x(i), self.y(v)) for i, v in enumerate(vals[:m])]
            d.line(pts, fill=col + (255,), width=5, joint="curve")
        img.alpha_composite(lay)
        # Markierungen (z. B. „Bert wacht auf")
        for mk in self.s.get("markierungen", []):
            xi = self.idx_of(mk["zeit"])
            if reveal >= xi + 0.5:
                a = ease_out(clamp((reveal - xi - 0.5) / 1.5))
                x = self.box[0] + (self.box[2] - self.box[0]) * (xi + 0.5) / n
                dl = ImageDraw.Draw(img)
                for yy in range(self.box[1], self.box[3], 18):
                    dl.line([(x, yy), (x, yy + 9)], fill=GREY + (int(200 * a),), width=2)
                T(img, f"{mk['zeit']} {mk['text']}", 26, WHITE, x + 8, self.box[1] + 18, SEMI, a, anchor="l")
        # Echte Trades als Pfeile
        for tr in self.trades:
            hhmm = tr["zeit"][11:16]
            xi = self.idx_of(hhmm)
            if reveal < xi + 0.5:
                continue
            a = ease_out(clamp((reveal - xi - 0.5) / 1.2))
            x = self.box[0] + (self.box[2] - self.box[0]) * (xi + 0.5) / n
            y = self.y(float(tr["preis_usd"]))
            buy = tr["aktion"] == "Kauf"
            col = GREEN if buy else RED
            dl = ImageDraw.Draw(img)
            s = 22
            if buy:
                tri = [(x, y + 8), (x - s, y + 8 + s * 1.5), (x + s, y + 8 + s * 1.5)]
                ly = y + 8 + s * 1.5 + 30
            else:
                tri = [(x, y - 8), (x - s, y - 8 - s * 1.5), (x + s, y - 8 - s * 1.5)]
                ly = y - 8 - s * 1.5 - 30
            dl.polygon(tri, fill=col + (int(255 * a),))
            dl.ellipse((x - 7, y - 7, x + 7, y + 7), fill=WHITE + (int(255 * a),))
            label = f"{'KAUF' if buy else 'VERKAUF'} {num(float(tr['preis_usd']))} $"
            size = 30
            wlab = font(BLACK, size).getlength(label) + 28
            lx = clamp(x - wlab / 2, self.box[0], self.box[2] - wlab)
            panel(img, (lx, ly - 24, lx + wlab, ly + 24), outline=col, fill=(8, 11, 20), alpha=a, r=12)
            T(img, label, size, col, lx + wlab / 2, ly, BLACK, a)


class Trades(Scene):
    def prepare(self, dur):
        super().prepare(dur)
        rows = [r for r in read_csv("bert_entscheidungen.csv") if r["zeit"].startswith(self.day)]
        self.rows = rows[-6:]

    def draw(self, img, f, t):
        appear(img, self.s.get("titel", "Berts Entscheidungen"), 64, WHITE, 450, f, 0.0)
        panel(img, (60, 520, 1020, 1190), fill=(6, 8, 15))
        d = ImageDraw.Draw(img)
        for i, c in enumerate((RED, YELLOW, GREEN)):
            d.ellipse((92 + i * 40, 548, 116 + i * 40, 572), fill=c + (255,))
        T(img, "data/bert_entscheidungen.csv", 24, DIM, 990, 560, MONO_REG, anchor="r")
        if not self.rows:
            appear(img, "Heute keine Aktion – kein Signal.", 40, GREY, 800, f, 0.1, MONO)
            return
        big = len(self.rows) <= 3
        y = 650 if big else 630
        for i, r in enumerate(self.rows):
            a = ease_out(prog(f, 0.08 + i * 0.12, 0.08))
            if a <= 0:
                continue
            akt = r["aktion"]
            col = GREEN if akt == "KAUF" else RED if akt == "VERKAUF" else YELLOW if akt == "SICHERUNG" else GREY
            line = f"{r['zeit'][11:16]}  {r['symbol']:<5} {akt}"
            if r.get("preis_usd"):
                line += f"  {num(float(r['preis_usd']))} $"
            T(img, line, 40 if big else 34, col, 100, y, MONO, a, anchor="l")
            grund = r["grund"]
            cut = 50 if big else 52
            T(img, "  " + grund[:cut] + ("…" if len(grund) > cut else ""), 30 if big else 28, GREY, 100,
              y + (50 if big else 42), MONO_REG, a, anchor="l")
            y += 130 if big else 98
        # Ergebnis abgeschlossener Trades
        ys = 1010
        for tr in [x for x in trades_on(self.day) if x["aktion"] == "Verkauf" and x.get("gewinn_usd")][-2:]:
            a = ease_out(prog(f, 0.45, 0.1))
            g = float(tr["gewinn_usd"])
            gp = float(tr.get("gewinn_prozent") or 0)
            T(img, f"Ergebnis {tr['symbol']}: {signed(g, 2, ' $')} ({pct(gp)})", 48, GREEN if g >= 0 else RED,
              W / 2, ys, BLACK, a)
            ys += 70


class Konto(Scene):
    def prepare(self, dur):
        super().prepare(dur)
        self.rows = equity_rows(self.day)
        allrows = equity_rows()
        self.last = latest_before(allrows, self.day)
        prev = [r for r in allrows if r["zeit"][:10] < self.day]
        self.start_day = float(prev[-1]["kontostand_usd"]) if prev else 10000.0

    def draw(self, img, f, t):
        appear(img, "Berts Konto heute", 64, WHITE, 450, f, 0.0)
        panel(img, (60, 520, 1020, 1000))
        vals = [self.start_day] + [float(r["kontostand_usd"]) for r in self.rows]
        times = ["Start"] + [r["zeit"][11:16] for r in self.rows]
        lo, hi = min(vals + [10000]) - 5, max(vals + [10000]) + 5
        x0, y0, x1, y1 = 110, 580, 960, 930

        def Y(v):
            return y1 - (y1 - y0) * (v - lo) / (hi - lo)
        d = ImageDraw.Draw(img)
        ys = Y(10000)
        for x in range(x0, x1, 28):
            d.line([(x, ys), (x + 14, ys)], fill=DIM + (255,), width=2)
        T(img, "Start 10.000 $", 24, DIM, x1, ys - 22, SEMI, anchor="r")
        q = ease_out(prog(f, 0.05, 0.5))
        n = max(2, int(len(vals) * q + 0.999))
        pts = [(x0 + (x1 - x0) * i / max(1, len(vals) - 1), Y(v)) for i, v in enumerate(vals)][:n]
        col = GREEN if vals[-1] >= self.start_day else RED
        if len(pts) >= 2:
            d.line(pts, fill=col + (255,), width=7, joint="curve")
        ex, ey = pts[-1]
        d.ellipse((ex - 11, ey - 11, ex + 11, ey + 11), fill=WHITE + (255,))
        T(img, times[0], 24, DIM, x0, 965, MONO_REG, anchor="l")
        T(img, times[-1], 24, DIM, x1, 965, MONO_REG, anchor="r")
        if self.last:
            end = float(self.last["kontostand_usd"])
            day_ch = end - self.start_day
            total = float(self.last["gewinn_prozent"])
            appear(img, f"{num(end)} $", 110, WHITE, 1075, f, 0.45)
            appear(img, f"heute {signed(day_ch, 2, ' $')}  ·  gesamt {pct(total)}", 40,
                   GREEN if day_ch >= 0 else RED, 1165, f, 0.55, BOLD)


class Kurt(Scene):
    def prepare(self, dur):
        super().prepare(dur)
        rows = [r for r in read_csv("kurt_analyse.csv") if r["zeit"].startswith(self.day)]
        def key(r):
            return (0 if r["entscheidung"].startswith(("TIPP", "NOTFALL")) else 1, -float(r["value_prozent"]))
        rows.sort(key=key)
        self.rows = rows[: int(self.s.get("max", 5))]
        alle = [r for r in read_csv("kurt_analyse.csv") if r["zeit"].startswith(self.day)]
        self.total = len(alle)
        self.ligen = len({r["liga"] for r in alle})

    def draw(self, img, f, t):
        appear(img, self.s.get("titel", "Kurts Rechnung"), 64, GREEN, 440, f, 0.0)
        ligen = f"{self.ligen} Liga" if self.ligen == 1 else f"{self.ligen} Ligen"
        appear(img, f"{self.total} Spiele geprüft · {ligen} · {de_date(self.day)}", 30, GREY, 500, f, 0.03, SEMI)
        y = 580
        for i, r in enumerate(self.rows):
            a = ease_out(prog(f, 0.08 + i * 0.1, 0.08))
            if a <= 0:
                y += 120
                continue
            ent = r["entscheidung"]
            tipp = ent.startswith(("TIPP", "NOTFALL"))
            risk = "riskant" in r["grund"]
            col = GREEN if tipp else ORANGE if risk else DIM
            panel(img, (60, y - 50, 1020, y + 58), outline=col if tipp else LINE, alpha=a, r=20)
            match = f"{team(r['heim'])} – {team(r['gast'])}"
            T(img, match, fit(match, BLACK, 38, 640), WHITE, 90, y - 16, BLACK, a, anchor="l")
            tip = "Unentschieden" if r["bester_tipp"] == "Unentschieden" else team(r["bester_tipp"])
            info = f"{tip} · Chance {num(float(r['faire_chance_prozent']), 0)} % · Quote {num(float(r['quote']))}"
            T(img, info, fit(info, MONO_REG, 26, 660), GREY, 90, y + 26, MONO_REG, a, anchor="l")
            val = float(r["value_prozent"])
            T(img, pct(val, 1), 38, GREEN if val >= 2 else (ORANGE if val > 0 else RED), 990, y - 14, BLACK, a,
              anchor="r")
            badge = "GETIPPT" if ent.startswith("TIPP") else "NOTFALL" if ent.startswith("NOTFALL") else \
                ("zu riskant" if risk else "kein Tipp")
            T(img, badge, 26, col, 990, y + 26, BOLD, a, anchor="r")
            y += 120


class Tipps(Scene):
    """Kurts Tipps mit Ergebnis (z. B. montags fürs Wochenende). Optional "von"/"bis" (Anstoß-Datum)."""

    def prepare(self, dur):
        super().prepare(dur)
        rows = read_csv("kurt_tipps.csv")
        von, bis = self.s.get("von"), self.s.get("bis", self.day)
        def kick(r):
            from datetime import datetime, timezone
            from zoneinfo import ZoneInfo
            return datetime.fromisoformat(r["anstoss"].replace("Z", "+00:00")).astimezone(
                ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d")
        if von:
            rows = [r for r in rows if von <= kick(r) <= bis]
        self.rows = rows[-5:]
        self.kick = {id(r): kick(r) for r in self.rows}

    def draw(self, img, f, t):
        appear(img, self.s.get("titel", "Kurts Tipps"), 64, GREEN, 440, f, 0.0)
        if not self.rows:
            appear(img, "Noch keine Tipps.", 44, GREY, 700, f, 0.1, BOLD)
            return
        y = 560
        total = 0.0
        for i, r in enumerate(self.rows):
            a = ease_out(prog(f, 0.08 + i * 0.12, 0.08))
            st = r["status"]
            col = GREEN if st == "gewonnen" else RED if st == "verloren" else YELLOW
            if a > 0:
                panel(img, (60, y - 52, 1020, y + 60), outline=col, alpha=a, r=20)
                match = f"{team(r['heim'])} – {team(r['gast'])}"
                T(img, match, fit(match, BLACK, 38, 600), WHITE, 90, y - 18, BLACK, a, anchor="l")
                tip = r["tipp"] if r["tipp"] == "Unentschieden" else team(r["tipp"])
                art = " · Notfall" if r.get("art") == "Notfall" else ""
                info = f"Tipp {tip} · Quote {num(float(r['quote']))} · {num(float(r['einsatz_eur']), 0)} €{art}"
                T(img, info, fit(info, MONO_REG, 26, 640), GREY, 90, y + 26, MONO_REG, a, anchor="l")
                if st == "offen":
                    T(img, "offen", 38, YELLOW, 990, y - 14, BLACK, a, anchor="r")
                    T(img, de_date(self.kick[id(r)])[:6], 26, GREY, 990, y + 26, MONO_REG, a, anchor="r")
                else:
                    g = float(r["gewinn_eur"] or 0)
                    T(img, signed(g, 2, " €"), 38, col, 990, y - 14, BLACK, a, anchor="r")
                    T(img, f"{st} {r['ergebnis']}", 26, col, 990, y + 26, BOLD, a, anchor="r")
            if st != "offen":
                total += float(r["gewinn_eur"] or 0)
            y += 128
        if any(r["status"] != "offen" for r in self.rows):
            appear(img, f"Summe: {signed(total, 2, ' €')}", 56, GREEN if total >= 0 else RED, 1170, f, 0.6)


class Value(Scene):
    def draw(self, img, f, t):
        appear(img, "Was heißt „Value“?", 70, YELLOW, 450, f, 0.0)
        # Münze
        cx, cy, r = W / 2, 660, 110
        spin = abs(math.cos(t * 5.0)) if f < 0.25 else 1.0
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        rx = max(6, r * spin)
        d.ellipse((cx - rx, cy - r, cx + rx, cy + r), fill=(214, 170, 60, 255), outline=(255, 222, 120, 255), width=6)
        lay.alpha_composite(text_img("K", BLACK, 120, (120, 86, 20)).resize(
            (max(1, int(80 * spin)), 120)), (int(cx - 40 * spin), int(cy - 64)))
        img.alpha_composite(lay)
        rows = [
            (0.12, "Münzwurf: Chance", "50 %", WHITE),
            (0.28, "Faire Quote", "2,00", WHITE),
            (0.44, "Angebot", "2,04", YELLOW),
            (0.60, "Im Schnitt pro 100 €", "102 €", GREEN),
        ]
        y = 815
        for st, lab, val, col in rows:
            a = ease_out(prog(f, st, 0.06))
            if a > 0:
                T(img, lab, 44, GREY, 110, y, BOLD, a, anchor="l")
                T(img, val, 60, col, 970, y, BLACK, a, anchor="r")
            y += 72
        p = prog(f, 0.74, 0.08)
        if p > 0:
            panel(img, (110, 1135 - 50, 970, 1135 + 50), outline=GREEN, alpha=ease_out(p), r=26)
            T(img, "= +2 % Value → Kurt tippt", 50, GREEN, W / 2, 1135, BLACK, ease_out(p))


class Update(Scene):
    def draw(self, img, f, t):
        p = prog(t, 0, 0.35)
        lab = f"UPDATE #{self.s['nummer']}"
        tag = text_img(lab, BLACK, 92, (10, 14, 26))
        w, h = tag.width + 80, tag.height + 40
        bx = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(bx).rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=YELLOW + (255,))
        bx.alpha_composite(tag, ((w - tag.width) // 2, (h - tag.height) // 2))
        put(img, bx, W / 2, 480, ease_out(p), 0.7 + 0.3 * ease_back(p))
        appear(img, self.s.get("titel", ""), fit(self.s.get("titel", ""), BLACK, 64, 940), WHITE, 610, f, 0.05)
        y = 730
        for i, pkt in enumerate(self.s.get("punkte", [])):
            a = ease_out(prog(f, 0.12 + i * 0.15, 0.07))
            if a > 0:
                panel(img, (80, y - 46, 1000, y + 46), alpha=a, r=22)
                T(img, "›", 56, YELLOW, 115, y - 4, BLACK, a)
                T(img, pkt, fit(pkt, BOLD, 42, 820), WHITE, 150, y, BOLD, a, anchor="l")
            y += 112


class Stand(Scene):
    def prepare(self, dur):
        super().prepare(dur)
        b = latest_before(equity_rows(), self.day)
        k = latest_before(read_csv("kurt_kontostand.csv"), self.day)
        self.bert = (float(b["kontostand_usd"]), float(b["gewinn_prozent"])) if b else (10000.0, 0.0)
        self.kurt = (float(k["kontostand_eur"]), float(k["gewinn_prozent"])) if k else (10000.0, 0.0)

    def draw(self, img, f, t):
        appear(img, "ZWISCHENSTAND", 92, YELLOW, 450, f, 0.0)
        big_b = make_robot(BLUE, "bert", 160)
        big_k = make_robot(GREEN, "kurt", 160)
        for i, (name, icon, (amt, p), cur, col) in enumerate(
                (("BERT", big_b, self.bert, "$", BLUE), ("KURT", big_k, self.kurt, "€", GREEN))):
            cx = 290 + i * 500
            a = ease_out(prog(f, 0.08 + i * 0.1, 0.1))
            if a <= 0:
                continue
            panel(img, (cx - 225, 540, cx + 225, 1060), outline=col, alpha=a, r=36, width=4)
            put(img, icon, cx, 640, a)
            T(img, name, 60, col, cx, 770, BLACK, a)
            T(img, pct(p), 80, GREEN if p > 0 else RED if p < 0 else GREY, cx, 880, BLACK, a)
            T(img, f"{num(amt)} {cur}", 40, WHITE, cx, 980, BOLD, a)
        lead = "Bert führt" if self.bert[1] > self.kurt[1] else "Kurt führt" if self.kurt[1] > self.bert[1] else "Gleichstand"
        appear(img, lead, 72, WHITE, 1150, f, 0.4)


class Frage(Scene):
    def draw(self, img, f, t):
        for i, z in enumerate(self.s.get("zeilen", [])):
            col = YELLOW if i == len(self.s["zeilen"]) - 1 else WHITE
            appear(img, z, fit(z, BLACK, 86, 940), col, 640 + i * 120, f, 0.05 + i * 0.15)


class Text(Scene):
    def draw(self, img, f, t):
        appear(img, self.s.get("titel", ""), fit(self.s.get("titel", ""), BLACK, 80, 940),
               color(self.s.get("titel_farbe"), YELLOW), 500, f, 0.0)
        for i, z in enumerate(self.s.get("zeilen", [])):
            txt, col = (z["text"], color(z.get("farbe"), WHITE)) if isinstance(z, dict) else (z, WHITE)
            appear(img, txt, fit(txt, BOLD, 56, 920), col, 660 + i * 95, f, 0.1 + i * 0.12, BOLD)


class Woche(Chart):
    """Echter Chart über mehrere Handelstage (z. B. Montag bis Freitag), mit Berts Linien."""

    def prepare(self, dur):
        Scene.prepare(self, dur)
        self.sym = self.s.get("symbol", "SPY")
        von, bis = self.s["von"], self.s["bis"]
        days = sorted(fn[:-5] for fn in os.listdir(os.path.join(DATA, "charts"))
                      if fn.endswith(".json") and von <= fn[:-5] <= bis)
        if not days:
            raise SystemExit(f"Keine Chartdaten zwischen {von} und {bis}.")
        self.k, self.e9, self.e21, self.starts = [], [], [], []
        for day in days:
            d = chart_day(day)["symbole"].get(self.sym)
            if not d:
                continue
            self.starts.append((len(self.k), day))
            self.k += d["kerzen"]
            self.e9 += d["ema9"]
            self.e21 += d["ema21"]
        self.trades = []
        lo = min([x[3] for x in self.k] + self.e9 + self.e21)
        hi = max([x[2] for x in self.k] + self.e9 + self.e21)
        pad = (hi - lo) * 0.08
        self.lo, self.hi = lo - pad, hi + pad
        self.box = (90, 565, 900, 1095)
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        panel(st, (60, 410, 1020, 1200))
        x0, y0, x1, y1 = self.box
        dr = ImageDraw.Draw(st)
        for i in range(5):
            v = self.lo + (self.hi - self.lo) * i / 4
            y = self.y(v)
            dr.line([(x0, y), (x1, y)], fill=LINE + (255,), width=1)
            T(st, num(v), 26, DIM, x1 + 14, y, MONO_REG, anchor="l")
        n = len(self.k)
        slot = (x1 - x0) / n
        for j, (idx, day) in enumerate(self.starts):
            end = self.starts[j + 1][0] if j + 1 < len(self.starts) else n
            if j:
                xs = x0 + slot * idx
                for yy in range(y0, y1, 18):
                    dr.line([(xs, yy), (xs, yy + 9)], fill=DIM + (255,), width=2)
            T(st, f"{weekday(day)} {day[8:10]}.", 26, DIM, x0 + slot * (idx + end) / 2, y1 + 30, MONO_REG)
        first, last = self.k[0][1], self.k[-1][4]
        ch = (last / first - 1) * 100
        T(st, self.sym, 56, WHITE, 90, 465, BLACK, anchor="l")
        T(st, NAMES.get(self.sym, ""), 34, GREY, 90 + font(BLACK, 56).getlength(self.sym) + 20, 470, SEMI, anchor="l")
        T(st, pct(ch), 40, GREEN if ch >= 0 else RED, 990, 465, BLACK, anchor="r")
        T(st, f"{de_date(days[0])[:6]}–{de_date(days[-1])} · Schluss {num(last)} $", 28, GREY, 90, 515, SEMI,
          anchor="l")
        T(st, "Quelle: Alpaca (IEX)", 24, DIM, 990, 515, SEMI, anchor="r")
        T(st, "—— schnelle Linie (Ø ~2 Std.)", 26, BLUE, 90, 1170, SEMI, anchor="l")
        T(st, "—— langsame Linie (Ø ~5 Std.)", 26, YELLOW, 990, 1170, SEMI, anchor="r")
        self.static = st


class Nachrechnung(Scene):
    """„Was wäre, wenn …?" – nachgerechnete Trades aus nachrechnung.py (keine echten Trades!)."""
    GRUND = {"blau unter gelb": "Blau unter Gelb", "Börsenschluss naht": "Börsenschluss",
             "Stop-Loss": "Stop-Loss", "Gewinnmitnahme": "Gewinnmitnahme"}

    def prepare(self, dur):
        super().prepare(dur)
        self.von, self.bis = self.s["von"], self.s["bis"]
        name = f"bert_{self.von}_bis_{self.bis}.csv"
        if not os.path.exists(os.path.join(DATA, "nachrechnung", name)):
            raise SystemExit(f"Nachrechnung fehlt: python3 nachrechnung.py {self.von} {self.bis}")
        self.rows = sorted(read_csv(os.path.join("nachrechnung", name)), key=lambda r: (r["tag"], r["kauf_zeit"]))

    def draw(self, img, f, t):
        titel = self.s.get("titel", "Was wäre, wenn …?")
        appear(img, titel, fit(titel, BLACK, 64, 940), WHITE, 440, f, 0.0)
        sub = f"Nachrechnung mit echten Kursen · {de_date(self.von)[:6]}–{de_date(self.bis)}"
        appear(img, sub, fit(sub, SEMI, 30, 940), GREY, 500, f, 0.03, SEMI)
        y, shown = 600, self.rows[:5]
        for i, r in enumerate(shown):
            a = ease_out(prog(f, 0.10 + i * 0.10, 0.08))
            g = float(r["gewinn_usd"])
            col = GREEN if g > 0 else RED
            if a > 0:
                panel(img, (60, y - 50, 1020, y + 52), outline=col, alpha=a, r=20)
                T(img, f"{weekday(r['tag'])} {r['kauf_zeit']}  {r['symbol']}", 38, WHITE, 90, y - 14, BLACK, a,
                  anchor="l")
                info = (f"{num(float(r['kauf_preis_usd']))} → {num(float(r['verkauf_preis_usd']))} $ · "
                        f"{self.GRUND.get(r['verkaufsgrund'], r['verkaufsgrund'])}")
                T(img, info, fit(info, MONO_REG, 26, 640), GREY, 90, y + 26, MONO_REG, a, anchor="l")
                T(img, signed(g, 2, " $"), 38, col, 990, y - 14, BLACK, a, anchor="r")
                T(img, pct(float(r["gewinn_prozent"])), 26, col, 990, y + 26, BOLD, a, anchor="r")
            y += 118
        total = sum(float(r["gewinn_usd"]) for r in self.rows)
        plus = sum(float(r["gewinn_usd"]) > 0 for r in self.rows)
        summe = f"{len(self.rows)} Trades · {plus} im Plus · {signed(total, 2, ' $')}"
        appear(img, summe, fit(summe, BLACK, 52, 940), GREEN if total >= 0 else RED, max(y + 20, 1100), f, 0.6)
        appear(img, "keine echten Trades · grob nachgerechnet · nachrechnung.py", 26, DIM, 1180, f, 0.65, SEMI)


TYPES = {"hook": Hook, "chart": Chart, "trades": Trades, "konto": Konto, "kurt": Kurt, "tipps": Tipps,
         "value": Value,
         "update": Update, "stand": Stand, "frage": Frage, "text": Text, "woche": Woche,
         "nachrechnung": Nachrechnung}


# ------------------------------------------------------------------ Untertitel
UNITS = {"%", "%.", "%,", "$", "$.", "€", "€.", "Uhr", "Uhr.", "Prozent", "Prozent.", "Dollar", "Dollar.",
         "Euro", "Euro."}


def chunks(text, maxw=4):
    words = []
    for w_ in text.split():   # Einheiten bleiben bei ihrer Zahl („6 %", „379 $", „16:35 Uhr")
        if words and (w_ in UNITS or w_.rstrip(".,!?") in UNITS) and re.search(r"\d", words[-1]):
            words[-1] += " " + w_
        else:
            words.append(w_)
    out, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= maxw or re.search(r"[.!?,:;]$", w_):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    merged = []  # einzelne Wörter an den vorigen Schnipsel hängen (wenn der Satz dort nicht endet)
    for c in out:
        if (merged and len(c.split()) == 1 and len(merged[-1].split()) < 6
                and len(merged[-1]) + len(c) <= 30 and not re.search(r"[.!?]$", merged[-1])):
            merged[-1] += " " + c
        else:
            merged.append(c)
    return merged


def subtitle_track(timeline):
    """Liste (start, ende, text) für jeden Untertitel-Schnipsel."""
    track = []
    for start, dur, text in timeline:
        parts = chunks(text)
        weights = [len(p) + 3 for p in parts]
        total = sum(weights)
        t = start
        for p, wgt in zip(parts, weights):
            d = dur * wgt / total
            track.append((t, t + d, p))
            t += d
    return track


def draw_subtitle(img, track, gt):
    cur = next((s for s in track if s[0] <= gt < s[1]), None)
    if not cur:
        return
    txt = cur[2]
    p = clamp((gt - cur[0]) / 0.08)
    size = fit(txt, BLACK, 66, 840)
    has_num = re.search(r"\d|Prozent|Dollar|Euro", txt)
    col = YELLOW if has_num else WHITE
    lay = text_img(txt, BLACK, size, col, 7)
    put(img, lay, SUB_X, SUB_Y, 1.0, 0.92 + 0.08 * ease_out(p))


# ------------------------------------------------------------------ Ablauf
def load_episode(path):
    ep = json.load(open(path, encoding="utf-8"))
    ep["_name"] = os.path.splitext(os.path.basename(path))[0]
    for i, s in enumerate(ep["szenen"], 1):
        s.setdefault("id", f"s{i}")
    return ep


def sag(x):
    """Gesprochener Text (Zahlen als Wörter)."""
    return (x["sag"] if isinstance(x, dict) else x).strip()


def zeig(x):
    """Untertitel (darf Ziffern enthalten). Ohne "zeig" = gesprochener Text."""
    return (x.get("zeig") or x["sag"] if isinstance(x, dict) else x).strip()


def write_text(ep):
    lines = [f"# {ep['_name']} – automatisch aus video/folgen/{ep['_name']}.json erzeugt"]
    for s in ep["szenen"]:
        for satz in s.get("sprecher", []):
            lines.append(f"{s['id']}|{sag(satz)}")
    out = os.path.join(REPO, "stimme", f"{ep['_name']}.txt")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("Sprechertext geschrieben:", out)


def load_clips(ep):
    p = os.path.join(REPO, "stimme", ep["_name"], "clips.json")
    if not os.path.exists(p):
        return None
    clips = json.load(open(p, encoding="utf-8"))["clips"]
    want = [(s["id"], sag(satz)) for s in ep["szenen"] for satz in s.get("sprecher", [])]
    have = [(c["szene"], c["text"]) for c in clips]
    if want != have:
        print("Achtung: Stimme passt nicht zum aktuellen Text – erst neu vertonen lassen!")
        return None
    return clips


def plan(ep, clips):
    """Berechnet Szenenlängen und die Zeitpunkte der Sätze."""
    scenes, timeline, audio = [], [], []
    t = 0.0
    ci = 0
    for s in ep["szenen"]:
        sp = s.get("sprecher", [])
        n = len(sp)
        cl = clips[ci:ci + n] if clips else [{"dauer": max(1.2, len(sag(x)) / 15), "datei": None}
                                             for x in sp]
        ci += n
        dur = HEAD + sum(c["dauer"] for c in cl) + GAP * max(0, n - 1) + TAIL
        dur = max(dur, float(s.get("min_dauer", 2.5)))
        pos = t + HEAD
        for c, x in zip(cl, sp):
            timeline.append((pos, c["dauer"], zeig(x)))
            if c.get("datei"):
                audio.append((pos, os.path.join(REPO, "stimme", ep["_name"], c["datei"])))
            pos += c["dauer"] + GAP
        scenes.append((s, t, dur))
        t += dur
    return scenes, timeline, audio, t


def render(ep, stills_only=False):
    os.makedirs(RENDER, exist_ok=True)
    clips = load_clips(ep)
    if clips is None and not stills_only:
        raise SystemExit("Keine passende Stimme gefunden (stimme/<folge>/clips.json).")
    scenes, timeline, audio, total = plan(ep, clips)
    track = subtitle_track(timeline)
    files = []
    for s, start, dur in scenes:
        sc = TYPES[s["typ"]](s, ep)
        sc.prepare(dur)
        if stills_only:
            for frac in (0.5, 0.95):
                t = dur * frac
                fr = sc.frame(t)
                draw_subtitle(fr, track, start + t)
                fr.convert("RGB").save(os.path.join(RENDER, f"still_{s['id']}_{int(frac * 100)}.jpg"), quality=88)
            continue
        tmp = os.path.join(RENDER, f"{ep['_name']}_{s['id']}.tmp.mp4")
        final = tmp.replace(".tmp.mp4", ".mp4")
        n = int(round(dur * FPS))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
               "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            t = i / FPS
            fr = sc.frame(t)
            draw_subtitle(fr, track, start + t)
            fr = fr.convert("RGB")
            if i < 3:
                fr = Image.blend(Image.new("RGB", (W, H), BG), fr, (i + 1) / 4)
            pr.stdin.write(fr.tobytes())
        pr.stdin.close()
        if pr.wait() != 0:
            raise SystemExit(f"ffmpeg-Fehler in Szene {s['id']}")
        os.replace(tmp, final)
        files.append(final)
        print(f"Szene {s['id']} ({s['typ']}, {dur:.1f}s) fertig", flush=True)
    if stills_only:
        print("Standbilder in", RENDER)
        return
    lst = os.path.join(RENDER, f"{ep['_name']}_list.txt")
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    joined = os.path.join(RENDER, f"{ep['_name']}_joined.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                           "-c", "copy", joined])
    out = os.path.join(RENDER, f"Folge{ep['folge']}_KI-gegen-das-System.mp4")
    mix(joined, audio, total, out)
    print("FERTIG:", out, f"({total:.1f}s)")


def mix(video, audio, total, out):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video]
    filt, labels = [], []
    for i, (start, path) in enumerate(audio):
        cmd += ["-i", path]
        ms = int(start * 1000)
        filt.append(f"[{i + 1}:a]aresample=44100,adelay={ms}|{ms},volume=1.0[a{i}]")
        labels.append(f"[a{i}]")
    filt.append("".join(labels) + f"amix=inputs={len(audio)}:normalize=0,pan=stereo|c0=c0|c1=c0,"
                f"alimiter=limit=0.89:level=false,apad,atrim=0:{total:.3f}[voice]")
    tmp = out.replace(".mp4", ".tmp.mp4")
    cmd += ["-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[voice]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp]
    subprocess.check_call(cmd)
    os.replace(tmp, out)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("text", "stills", "render"):
        sys.exit(__doc__)
    episode = load_episode(sys.argv[2])
    if sys.argv[1] == "text":
        write_text(episode)
    elif sys.argv[1] == "stills":
        render(episode, stills_only=True)
    else:
        render(episode)
