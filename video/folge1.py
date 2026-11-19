#!/usr/bin/env python3
"""Folge 1 – KI gegen das System. Rendert Szenen als einzelne MP4s (1080x1920, 30 fps)."""
import math, os, random, subprocess, sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
OUT = os.environ.get("RENDER_DIR", "/tmp/render")
os.makedirs(OUT, exist_ok=True)
FD = "/usr/share/fonts/opentype/inter/"
BLACK = FD + "InterDisplay-Black.otf"
BOLD = FD + "InterDisplay-Bold.otf"
SEMI = FD + "InterDisplay-SemiBold.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

WHITE = (255, 255, 255)
GREY = (150, 163, 190)
BLUE = (61, 165, 255)      # Bert
GREEN = (46, 229, 157)     # Kurt
YELLOW = (255, 210, 63)
RED = (255, 77, 94)
PANEL = (22, 30, 52)


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_back(x):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ------------------------------------------------------------------ background
def make_bg():
    bg = Image.new("RGB", (W, H + 120))
    d = ImageDraw.Draw(bg)
    for y in range(H + 120):
        k = y / (H + 120)
        d.line([(0, y), (W, y)], fill=(int(9 + 10 * k), int(13 + 12 * k), int(26 + 22 * k)))
    for x in range(0, W + 1, 120):
        d.line([(x, 0), (x, H + 120)], fill=(28, 38, 64), width=2)
    for y in range(0, H + 121, 120):
        d.line([(0, y), (W, y)], fill=(28, 38, 64), width=2)
    return bg


BG = make_bg()


def background(t):
    off = int((t * 30) % 120)
    return BG.crop((0, off, W, off + H)).convert("RGBA")


# ------------------------------------------------------------------ text layers
@lru_cache(512)
def text_img(text, path, size, color, stroke=0):
    f = font(path, size)
    l, tp, r, b = f.getbbox(text, stroke_width=stroke)
    img = Image.new("RGBA", (r - l + 8, b - tp + 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4 - l, 4 - tp), text, font=f, fill=color + (255,),
                             stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return img


def with_alpha(img, a):
    if a >= 0.999:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return img


def place(base, img, cx, cy, alpha=1.0, scale=1.0, anchor="c"):
    if alpha <= 0.003 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.005:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    img = with_alpha(img, alpha)
    x = int(cx - img.width / 2) if anchor == "c" else int(cx)
    y = int(cy - img.height / 2)
    base.alpha_composite(img, (x, y))


def txt(base, text, size, color, cx, cy, path=BLACK, alpha=1.0, scale=1.0, anchor="c"):
    place(base, text_img(text, path, size, color), cx, cy, alpha, scale, anchor)


def pop(base, text, size, color, cy, t, start, path=BLACK, cx=W / 2, dur=0.35):
    p = prog(t, start, dur)
    if p <= 0:
        return
    txt(base, text, size, color, cx, cy + (1 - ease_out(p)) * 40, path, alpha=ease_out(p),
        scale=0.85 + 0.15 * ease_back(p))


def rrect(base, box, r, fill, alpha=1.0, outline=None, width=0):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, r, fill=fill + (int(255 * alpha),),
                        outline=(outline + (int(255 * alpha),)) if outline else None, width=width)
    base.alpha_composite(layer)


def header(base, t):
    pill = text_img("KI GEGEN DAS SYSTEM  ·  FOLGE 1", SEMI, 34, GREY)
    w = pill.width + 60
    rrect(base, (W / 2 - w / 2, 230, W / 2 + w / 2, 300), 35, (18, 25, 45), 0.9, outline=(45, 58, 92), width=2)
    place(base, pill, W / 2, 265)


# ------------------------------------------------------------------ robots
def make_robot(color, kind, size=420):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = (12, 17, 30, 255)
    c = color + (255,)
    # Glow
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((s * .12, s * .18, s * .88, s * .94), fill=color + (90,))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(s * .08)))
    # Antenne
    d.line([(s * .5, s * .2), (s * .5, s * .08)], fill=c, width=int(s * .03))
    d.ellipse((s * .45, s * .03, s * .55, s * .13), fill=YELLOW + (255,))
    # Ohren
    d.rounded_rectangle((s * .1, s * .42, s * .2, s * .62), int(s * .03), fill=c)
    d.rounded_rectangle((s * .8, s * .42, s * .9, s * .62), int(s * .03), fill=c)
    # Kopf
    d.rounded_rectangle((s * .17, s * .2, s * .83, s * .84), int(s * .12), fill=c)
    # Visier
    d.rounded_rectangle((s * .25, s * .32, s * .75, s * .62), int(s * .08), fill=dark)
    # Augen
    for ex in (.39, .61):
        d.ellipse((s * (ex - .055), s * .41, s * (ex + .055), s * .52), fill=color + (255,))
        d.ellipse((s * (ex - .02), s * .44, s * (ex + .03), s * .49), fill=(255, 255, 255, 255))
    # Mund
    d.rounded_rectangle((s * .4, s * .7, s * .6, s * .74), int(s * .02), fill=dark)
    if kind == "bert":
        # Krawatte
        d.polygon([(s * .5, s * .84), (s * .45, s * .92), (s * .5, s * .99), (s * .55, s * .92)], fill=RED + (255,))
        f = font(BLACK, int(s * .12))
        d.text((s * .5, s * .265), "$", font=f, fill=dark, anchor="mm")
    else:
        # Fußball
        bx, by, br = s * .82, s * .82, s * .13
        d.ellipse((bx - br, by - br, bx + br, by + br), fill=(255, 255, 255, 255), outline=dark, width=int(s * .012))
        pts = [(bx + br * .45 * math.cos(math.radians(a - 90)), by + br * .45 * math.sin(math.radians(a - 90)))
               for a in range(0, 360, 72)]
        d.polygon(pts, fill=dark)
    return img


BERT = make_robot(BLUE, "bert")
KURT = make_robot(GREEN, "kurt")


def robot(base, which, cx, cy, t, start, size=1.0, bob=True):
    p = prog(t, start, 0.45)
    if p <= 0:
        return
    sc = size * (0.3 + 0.7 * ease_back(p))
    dy = math.sin((t - start) * 3.2) * 10 if bob else 0
    place(base, which, cx, cy + dy, alpha=ease_out(p), scale=sc)


def de_num(v):
    return f"{int(round(v)):,}".replace(",", ".")


# ------------------------------------------------------------------ Szenen
def s1(t):  # Hook
    b = background(t); header(b, t)
    if t < 2.4:
        pop(b, "Ich kann", 110, WHITE, 700, t, 0.0)
        shake = math.sin(t * 60) * 8 * (1 - prog(t, 0.7, 0.5)) if t > 0.35 else 0
        pop(b, "NICHT", 210, RED, 870, t, 0.35, cx=W / 2 + shake)
        pop(b, "programmieren.", 110, WHITE, 1040, t, 0.7)
    else:
        u = t - 2.4
        pop(b, "Trotzdem hab ich", 96, WHITE, 690, u, 0.0)
        pop(b, "2 Bots", 220, YELLOW, 870, u, 0.25)
        pop(b, "gebaut.", 110, WHITE, 1050, u, 0.5)
    return b


def s2(t):  # Mit KI, am iPad
    b = background(t); header(b, t)
    robot(b, BERT, 330, 640, t, 0.0, 0.95)
    robot(b, KURT, 750, 640, t, 0.2, 0.95)
    pop(b, "Mit KI.", 120, WHITE, 1000, t, 0.6)
    pop(b, "Am iPad.", 120, WHITE, 1140, t, 1.3)
    pop(b, "An einem Abend.", 120, YELLOW, 1280, t, 2.0)
    return b


def s3(t):  # 10.000 Spielgeld
    b = background(t); header(b, t)
    pop(b, "Jeder bekommt", 100, WHITE, 560, t, 0.0)
    v = 10000 * ease_out(prog(t, 0.3, 1.6))
    if t > 0.3:
        txt(b, de_num(v), 230, YELLOW, W / 2, 760, alpha=ease_out(prog(t, 0.3, 0.3)))
    pop(b, "Spielgeld.", 110, WHITE, 950, t, 0.5)
    for i, (who, img, cur, col) in enumerate((("BERT", BERT, "$", BLUE), ("KURT", KURT, "€", GREEN))):
        cx = 300 + i * 480
        p = prog(t, 1.9 + i * 0.25, 0.4)
        if p > 0:
            rrect(b, (cx - 200, 1100, cx + 200, 1480), 40, PANEL, ease_out(p), outline=col, width=4)
            place(b, img, cx, 1230, alpha=ease_out(p), scale=0.5 * ease_back(p))
            txt(b, f"{who}", 54, col, cx, 1390, alpha=ease_out(p))
            txt(b, f"10.000 {cur}", 50, WHITE, cx, 1445, BOLD, alpha=ease_out(p))
    pop(b, "Wer macht mehr draus?", 80, YELLOW, 1610, t, 3.0)
    return b


def _mkwalk():
    for seed in range(200):
        random.seed(seed)
        w = [0.0]
        for _ in range(80):
            w.append(w[-1] + random.gauss(0.15, 1.0))
        if w[-1] >= max(w) - 0.5 and w[-1] - min(w) > 8:
            return w
    return w


_walk = _mkwalk()


def chart(base, t, start, box, color):
    x0, y0, x1, y1 = box
    p = ease_out(prog(t, start, 2.6))
    if p <= 0:
        return
    rrect(base, box, 36, PANEL, 0.9)
    lo, hi = min(_walk), max(_walk)
    pts = [(x0 + 40 + (x1 - x0 - 80) * i / (len(_walk) - 1),
            y1 - 40 - (y1 - y0 - 80) * (v - lo) / (hi - lo)) for i, v in enumerate(_walk)]
    n = max(2, int(len(pts) * p))
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.line(pts[:n], fill=color + (90,), width=22, joint="curve")
    d.line(pts[:n], fill=color + (255,), width=8, joint="curve")
    ex, ey = pts[n - 1]
    d.ellipse((ex - 16, ey - 16, ex + 16, ey + 16), fill=WHITE + (255,))
    base.alpha_composite(layer)


def s4(t):  # Bert
    b = background(t); header(b, t)
    robot(b, BERT, W / 2, 560, t, 0.0, 0.9)
    pop(b, "BÖRSEN-BERT", 130, BLUE, 840, t, 0.3)
    chart(b, t, 0.8, (90, 950, 990, 1330), BLUE)
    pop(b, "handelt US-Aktien", 80, WHITE, 1440, t, 1.4, BOLD)
    pop(b, "alle 15 Minuten.", 80, WHITE, 1540, t, 2.4, BOLD)
    pop(b, "Komplett allein.", 80, YELLOW, 1640, t, 3.4)
    return b


def s5(t):  # Kurt
    b = background(t); header(b, t)
    robot(b, KURT, W / 2, 600, t, 0.0, 0.9)
    pop(b, "KICKER-KURT", 130, GREEN, 880, t, 0.3)
    pop(b, "tippt die Bundesliga", 84, WHITE, 1060, t, 1.0, BOLD)
    pop(b, "aber nur,", 84, WHITE, 1190, t, 2.4, BOLD)
    pop(b, "wenn es sich lohnt.", 96, YELLOW, 1310, t, 3.0)
    return b


def s6(t):  # Kurts erste Entscheidung
    b = background(t); header(b, t)
    pop(b, "Kurts erste", 100, WHITE, 470, t, 0.0)
    pop(b, "Entscheidung:", 100, GREEN, 590, t, 0.15)
    p = ease_out(prog(t, 0.6, 0.4))
    if p > 0:
        rrect(b, (90, 700 + (1 - p) * 60, 990, 1260 + (1 - p) * 60), 44, PANEL, p, outline=(45, 58, 92), width=3)
        txt(b, "FC BAYERN", 70, WHITE, W / 2, 800 + (1 - p) * 60, alpha=p)
        txt(b, "vs.", 50, GREY, W / 2, 875 + (1 - p) * 60, BOLD, alpha=p)
        txt(b, "1. FC KÖLN", 70, WHITE, W / 2, 950 + (1 - p) * 60, alpha=p)
    pop(b, "Tipp: Köln gewinnt?", 66, YELLOW, 1080, t, 1.6, BOLD)
    pop(b, "Chance: unter 5 %", 66, WHITE, 1175, t, 2.6, BOLD)
    # Stempel
    q = prog(t, 4.0, 0.35)
    if q > 0:
        st = text_img("ZU RISKANT", BLACK, 120, RED)
        pad = 34
        box = Image.new("RGBA", (st.width + pad * 2, st.height + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(box)
        d.rounded_rectangle((4, 4, box.width - 4, box.height - 4), 24, outline=RED + (255,), width=12)
        box.alpha_composite(st, (pad, pad))
        box = box.rotate(-9, expand=True, resample=Image.BICUBIC)
        place(b, box, W / 2, 1390, alpha=min(1, q * 2), scale=2.2 - 1.2 * ease_out(q))
    pop(b, "Kein Tipp. Kurt bleibt cool.", 70, WHITE, 1580, t, 5.0, BOLD)
    return b


TERM = [
    ("> Erster Start!", WHITE),
    ("> Bert startet mit 10.000 $", BLUE),
    ("> Noch 48 Min. bis Börsenschluss", WHITE),
    ("> Letzte Stunde:", WHITE),
    ("  keine neuen Käufe.", YELLOW),
]


def s7(t):  # Und Bert?
    b = background(t); header(b, t)
    pop(b, "Und Bert?", 140, BLUE, 520, t, 0.0)
    p = ease_out(prog(t, 0.6, 0.35))
    if p > 0:
        rrect(b, (70, 660, 1010, 1260), 36, (8, 11, 20), p, outline=(45, 58, 92), width=3)
        layer = Image.new("RGBA", b.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for i, col in enumerate((RED, YELLOW, GREEN)):
            d.ellipse((110 + i * 50, 700, 140 + i * 50, 730), fill=col + (int(255 * p),))
        b.alpha_composite(layer)
        f = font(MONO, 42)
        cps = 26
        tt = max(0.0, t - 1.0)
        chars = int(tt * cps)
        y = 790
        d = ImageDraw.Draw(b)
        for line, col in TERM:
            shown = line[:max(0, chars)]
            chars -= len(line) + 6
            if shown:
                d.text((110, y), shown, font=f, fill=col + (255,))
            y += 85
            if chars < 0:
                if int(t * 2) % 2 == 0:
                    cx = 110 + f.getlength(shown)
                    d.rectangle((cx + 4, y - 85 + 6, cx + 28, y - 85 + 52), fill=WHITE + (255,))
                break
    pop(b, "Zu spät. Bert wartet", 80, WHITE, 1400, t, 5.0, BOLD)
    pop(b, "auf seinen ersten Tag.", 80, WHITE, 1500, t, 5.2, BOLD)
    return b


def s8(t):  # Duell
    b = background(t); header(b, t)
    pop(b, "DAS DUELL", 130, YELLOW, 470, t, 0.0)
    for i, (name, img, cur, col) in enumerate((("BERT", BERT, "$", BLUE), ("KURT", KURT, "€", GREEN))):
        cx = 290 + i * 500
        p = prog(t, 0.3 + i * 0.2, 0.4)
        if p > 0:
            e = ease_out(p)
            rrect(b, (cx - 220, 600, cx + 220, 1180), 44, PANEL, e, outline=col, width=5)
            robot(b, img, cx, 770, t, 0.3 + i * 0.2, 0.55)
            txt(b, name, 70, col, cx, 960, alpha=e)
            txt(b, f"10.000 {cur}", 56, WHITE, cx, 1045, BOLD, alpha=e)
            txt(b, "±0,00 %", 50, GREY, cx, 1115, BOLD, alpha=e)
    q = prog(t, 0.8, 0.3)
    if q > 0:
        place(b, text_img("VS", BLACK, 90, WHITE, 6), W / 2, 890, alpha=q, scale=1.8 - 0.8 * ease_back(q))
    pop(b, "Kein echtes Geld.", 76, WHITE, 1320, t, 1.6, BOLD)
    pop(b, "Nur Spielgeld.", 76, WHITE, 1420, t, 2.2, BOLD)
    return b


def s9(t):  # CTA
    b = background(t); header(b, t)
    pop(b, "In Folge 2:", 100, WHITE, 560, t, 0.0)
    pop(b, "Berts erster", 130, BLUE, 730, t, 0.3)
    pop(b, "Trading-Tag.", 130, BLUE, 870, t, 0.5)
    pop(b, "Gewinnt er – oder", 84, WHITE, 1040, t, 1.4, BOLD)
    pop(b, "verbrennt er Geld?", 84, YELLOW, 1140, t, 1.9, BOLD)
    p = prog(t, 3.0, 0.4)
    if p > 0:
        pulse = 1 + 0.04 * math.sin((t - 3.0) * 6)
        btn = text_img("FOLGEN  →", BLACK, 80, (10, 14, 26))
        w, h = btn.width + 120, btn.height + 70
        bx = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(bx).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=YELLOW + (255,))
        bx.alpha_composite(btn, ((w - btn.width) // 2, (h - btn.height) // 2))
        place(b, bx, W / 2, 1330, alpha=ease_out(p), scale=pulse * (0.6 + 0.4 * ease_back(p)))
    return b


SCENES = [("s1", s1, 5.0), ("s2", s2, 4.0), ("s3", s3, 4.6), ("s4", s4, 6.0), ("s5", s5, 6.0),
          ("s6", s6, 8.0), ("s7", s7, 7.0), ("s8", s8, 5.0), ("s9", s9, 6.0)]


def render_scene(name, fn, dur):
    tmp = os.path.join(OUT, f"{name}.tmp.mp4")
    final = os.path.join(OUT, f"{name}.mp4")
    n = int(round(dur * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        fr = fn(t).convert("RGB")
        # weicher Einstieg: erste 4 Frames aus Schwarz
        if i < 4:
            fr = Image.blend(Image.new("RGB", (W, H)), fr, (i + 1) / 5)
        pr.stdin.write(fr.tobytes())
    pr.stdin.close()
    if pr.wait() == 0:
        os.replace(tmp, final)
    else:
        sys.exit(f"ffmpeg-Fehler in {name}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    if mode == "stills":
        for name, fn, t in [("s1", s1, 1.6), ("s1", s1, 4.2), ("s3", s3, 4.0), ("s4", s4, 5.0),
                            ("s6", s6, 7.0), ("s7", s7, 6.5), ("s8", s8, 4.0), ("s9", s9, 5.0)]:
            fn(t).convert("RGB").save(os.path.join(OUT, f"still_{name}_{t}.jpg"), quality=90)
    else:
        for name, fn, dur in SCENES:
            render_scene(name, fn, dur)
            print("fertig:", name, flush=True)
