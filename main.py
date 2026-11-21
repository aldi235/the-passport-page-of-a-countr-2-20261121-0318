#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws an open passport spread for the invented free-port Republic of
Talmar (Adriatic) entirely in code with PIL: a data page with a drawn
portrait and a machine-readable zone with real ICAO check digits, and a
visa page with a Dravian visa sticker and a coherent 2024-2025 travel
history stamped by Talmar and its neighbours Dravia and Corvinia.

Writes /output/entry.png (1024x1024, under 1 MiB). No network, no
external images: every pixel is drawn here, fonts are bundled in fonts/.
Deterministic output (fixed random seed) so repeated runs agree.
"""

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1024, 1024
BASE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("ENTRY_PNG", "/output/entry.png"))

random.seed(20261121)

# ---------------------------------------------------------------- fonts
FONTS = {
    "sans": "LiberationSans-Regular.ttf",
    "sans_b": "LiberationSans-Bold.ttf",
    "serif": "LiberationSerif-Regular.ttf",
    "serif_b": "LiberationSerif-Bold.ttf",
    "mono": "LiberationMono-Regular.ttf",
    "mono_b": "LiberationMono-Bold.ttf",
}


def font(name, size):
    p = BASE / "fonts" / FONTS[name]
    if not p.exists():  # fall back to system fonts
        p = Path("/usr/share/fonts/truetype/liberation") / FONTS[name]
    return ImageFont.truetype(str(p), size)


# ---------------------------------------------------------------- colours
DESK = (46, 49, 57)
DESK_LIGHT = (62, 66, 76)
COVER = (106, 28, 40)
COVER_DARK = (74, 18, 27)
GOLD = (198, 164, 92)
PAGE_L = (246, 241, 227)   # data page cream
PAGE_R = (233, 239, 232)   # visa page pale green-grey
INK = (28, 32, 46)
INK_SOFT = (74, 78, 92)
LABEL = (110, 105, 88)
RULE = (150, 142, 118)
MRZ_BG = (252, 250, 244)
STAMP_BLUE = (32, 74, 138)
STAMP_GREEN = (18, 96, 66)
STAMP_RED = (148, 52, 40)
STAMP_PURPLE = (104, 58, 130)

# ---------------------------------------------------------------- helpers


def spaced(draw, xy, text, fnt, fill, tracking=0, anchor="la"):
    """Draw text with letter tracking; anchor like PIL ('la','ma','ra')."""
    x, y = xy
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    if anchor.startswith("m"):
        x -= total / 2
    elif anchor.startswith("r"):
        x -= total
    cx = x
    for ch, w in zip(text, widths):
        draw.text((cx, y), ch, font=fnt, fill=fill)
        cx += w + tracking
    return total


def text_w(draw, text, fnt, tracking=0):
    return sum(draw.textlength(ch, font=fnt) for ch in text) + tracking * max(0, len(text) - 1)


def hline(draw, x0, x1, y, fill, width=1):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def rounded_frame(draw, box, radius, outline, width=1):
    draw.rounded_rectangle(box, radius=radius, outline=outline, width=width)


# ------------------------------------------------------- MRZ check digits
def mrz_value(ch):
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 55  # A=10 .. Z=35


def mrz_check(s):
    weights = (7, 3, 1)
    return str(sum(mrz_value(c) * weights[i % 3] for i, c in enumerate(s)) % 10)


def mrz_lines():
    line1 = "P<TMRKOVAC<<ELENA<MARIS"
    line1 = line1 + "<" * (44 - len(line1))
    num = "TM4821937"
    dob, exp = "880314", "330611"
    pers = "<" * 14
    l2 = num + mrz_check(num) + "TMR" + dob + mrz_check(dob) + "F" + exp
    l2 += mrz_check(exp) + pers + mrz_check(pers)
    final = mrz_check(l2)
    line2 = l2 + final
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return line1, line2


# ------------------------------------------------------------- guilloche
def guilloche(draw, box, color, step=7, amp=2.2):
    """Fine wavy security lines across a page area."""
    x0, y0, x1, y1 = box
    y = y0
    while y < y1:
        pts = []
        x = x0
        while x <= x1:
            pts.append((x, y + amp * math.sin((x - x0) / 26.0)))
            x += 6
        draw.line(pts, fill=color, width=1)
        y += step


def paper_noise(img, box, amount=6, alpha=10):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    noise = Image.new("L", (w, h), 0)
    px = noise.load()
    for _ in range(w * h // 90):
        px[random.randrange(w), random.randrange(h)] = random.randrange(140, 255)
    noise = noise.filter(ImageFilter.GaussianBlur(0.6))
    overlay = Image.new("RGBA", (w, h), (90, 85, 70, 0))
    overlay.putalpha(noise.point(lambda v: v * alpha // 255))
    img.paste(overlay, (x0, y0), overlay)


# ------------------------------------------------------------ coat of arms
def coat_of_arms(size=84):
    """Talmar arms: shield, anchor, star, waves. Drawn supersampled."""
    s = 4
    w, h = size * s, int(size * 1.18 * s)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    navy = (26, 48, 84, 255)
    gold = (176, 138, 62, 255)
    cx = w // 2
    # star above shield
    star_r = 13 * s
    sy = 16 * s
    pts = []
    for i in range(10):
        r = star_r if i % 2 == 0 else star_r * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + r * math.cos(a), sy + r * math.sin(a)))
    d.polygon(pts, fill=gold)
    # shield
    top = 34 * s
    sw, sh = 30 * s, 40 * s
    shield = [(cx - sw, top), (cx + sw, top), (cx + sw, top + sh - 12 * s),
              (cx, top + sh + 6 * s), (cx - sw, top + sh - 12 * s)]
    d.polygon(shield, fill=(244, 238, 220, 255), outline=navy, width=2 * s)
    # anchor
    ax, ay = cx, top + 20 * s
    d.line([(ax, ay - 12 * s), (ax, ay + 14 * s)], fill=navy, width=3 * s)
    d.arc([ax - 5 * s, ay - 17 * s, ax + 5 * s, ay - 7 * s], 0, 360, fill=navy, width=2 * s)
    d.line([(ax - 11 * s, ay - 8 * s), (ax + 11 * s, ay - 8 * s)], fill=navy, width=3 * s)
    d.arc([ax - 13 * s, ay - 2 * s, ax + 13 * s, ay + 24 * s], 20, 160, fill=navy, width=3 * s)
    d.polygon([(ax - 13 * s, ay + 8 * s), (ax - 6 * s, ay + 6 * s), (ax - 11 * s, ay + 14 * s)], fill=navy)
    d.polygon([(ax + 13 * s, ay + 8 * s), (ax + 6 * s, ay + 6 * s), (ax + 11 * s, ay + 14 * s)], fill=navy)
    # waves under shield
    for i, wy in enumerate((top + sh + 12 * s, top + sh + 18 * s)):
        pts = []
        for x in range(cx - 34 * s, cx + 35 * s, 3 * s):
            pts.append((x, wy + 2 * s * math.sin((x - cx) / (7.0 * s))))
        d.line(pts, fill=navy, width=2 * s)
    layer = layer.resize((size, int(size * 1.18)), Image.LANCZOS)
    return layer


# ---------------------------------------------------------------- portrait
def portrait(w=150, h=190):
    """Stylised flat passport portrait of Elena Kovac, drawn in code."""
    s = 4
    W4, H4 = w * s, h * s
    img = Image.new("RGB", (W4, H4), (0, 0, 0))
    d = ImageDraw.Draw(img)
    # backdrop: soft blue-grey gradient
    for y in range(H4):
        t = y / H4
        c = tuple(int(a + (b - a) * t) for a, b in zip((168, 182, 194), (205, 212, 218)))
        d.line([(0, y), (W4, y)], fill=c)
    # soft light behind head
    glow = Image.new("RGBA", (W4, H4), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W4 * 0.18, H4 * 0.02, W4 * 0.82, H4 * 0.62], fill=(232, 236, 240, 120))
    img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(18 * s)))
    d = ImageDraw.Draw(img)
    skin = (226, 178, 140)
    skin_dark = (206, 152, 116)
    skin_light = (238, 196, 162)
    hair_c = (58, 40, 30)
    hair_hi = (88, 62, 44)
    cx = W4 // 2
    # hair back mass (shoulder length)
    d.ellipse([cx - 62 * s, 8 * s, cx + 62 * s, 128 * s], fill=hair_c)
    # shoulders / blazer
    d.pieslice([cx - 118 * s, 118 * s, cx + 118 * s, 320 * s], 180, 360, fill=(38, 52, 74))
    d.pieslice([cx - 118 * s, 118 * s, cx + 118 * s, 320 * s], 180, 360, outline=(28, 40, 58), width=2 * s)
    # blouse V
    d.polygon([(cx - 26 * s, 132 * s), (cx + 26 * s, 132 * s), (cx, 178 * s)], fill=(240, 238, 232))
    # blazer lapels
    d.polygon([(cx - 26 * s, 132 * s), (cx - 8 * s, 150 * s), (cx, 178 * s), (cx - 34 * s, 152 * s)], fill=(30, 42, 60))
    d.polygon([(cx + 26 * s, 132 * s), (cx + 8 * s, 150 * s), (cx, 178 * s), (cx + 34 * s, 152 * s)], fill=(30, 42, 60))
    # neck
    d.rounded_rectangle([cx - 16 * s, 108 * s, cx + 16 * s, 142 * s], radius=8 * s, fill=skin_dark)
    d.rounded_rectangle([cx - 15 * s, 106 * s, cx + 15 * s, 138 * s], radius=7 * s, fill=skin)
    # ears
    d.ellipse([cx - 52 * s, 62 * s, cx - 38 * s, 88 * s], fill=skin_dark)
    d.ellipse([cx + 38 * s, 62 * s, cx + 52 * s, 88 * s], fill=skin_dark)
    # face
    d.ellipse([cx - 44 * s, 26 * s, cx + 44 * s, 122 * s], fill=skin)
    # cheek shading + highlight
    shade = Image.new("RGBA", (W4, H4), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.ellipse([cx + 6 * s, 40 * s, cx + 44 * s, 118 * s], fill=(198, 140, 105, 60))
    sd.ellipse([cx - 42 * s, 30 * s, cx - 8 * s, 70 * s], fill=(244, 208, 176, 70))
    sd.ellipse([cx - 30 * s, 92 * s, cx - 12 * s, 106 * s], fill=(214, 138, 118, 55))
    sd.ellipse([cx + 12 * s, 92 * s, cx + 30 * s, 106 * s], fill=(214, 138, 118, 55))
    img = Image.alpha_composite(img, shade.filter(ImageFilter.GaussianBlur(4 * s)))
    d = ImageDraw.Draw(img)
    # hair front: centre part, framing the face
    d.pieslice([cx - 48 * s, 10 * s, cx + 48 * s, 84 * s], 180, 360, fill=hair_c)
    d.ellipse([cx - 50 * s, 18 * s, cx - 30 * s, 108 * s], fill=hair_c)
    d.ellipse([cx + 30 * s, 18 * s, cx + 50 * s, 108 * s], fill=hair_c)
    d.polygon([(cx - 46 * s, 34 * s), (cx - 20 * s, 22 * s), (cx, 30 * s),
               (cx + 20 * s, 22 * s), (cx + 46 * s, 34 * s), (cx + 40 * s, 52 * s),
               (cx, 40 * s), (cx - 40 * s, 52 * s)], fill=hair_c)
    for sx, sy, ex, ey in ((-40, 30, -32, 88), (40, 30, 32, 88), (-14, 26, -22, 60), (14, 26, 22, 60)):
        d.line([(cx + sx * s, sy * s), (cx + ex * s, ey * s)], fill=hair_hi, width=2 * s)
    # eyebrows
    d.arc([cx - 32 * s, 58 * s, cx - 8 * s, 72 * s], 200, 340, fill=(52, 36, 26), width=3 * s)
    d.arc([cx + 8 * s, 58 * s, cx + 32 * s, 72 * s], 200, 340, fill=(52, 36, 26), width=3 * s)
    # eyes
    for ex in (-20, 20):
        d.ellipse([cx + (ex - 9) * s, 72 * s, cx + (ex + 9) * s, 82 * s], fill=(250, 248, 244))
        d.ellipse([cx + (ex - 5) * s, 72 * s, cx + (ex + 5) * s, 82 * s], fill=(46, 34, 26))
        d.ellipse([cx + (ex - 2) * s, 73 * s, cx + (ex + 1) * s, 76 * s], fill=(255, 255, 255))
        d.arc([cx + (ex - 10) * s, 70 * s, cx + (ex + 10) * s, 82 * s], 180, 360, fill=(40, 30, 24), width=2 * s)
    # nose
    d.line([(cx + 1 * s, 80 * s), (cx - 1 * s, 94 * s)], fill=skin_dark, width=2 * s)
    d.arc([cx - 5 * s, 92 * s, cx + 5 * s, 99 * s], 0, 180, fill=skin_dark, width=2 * s)
    # lips
    d.polygon([(cx - 12 * s, 104 * s), (cx, 101 * s), (cx + 12 * s, 104 * s),
               (cx + 8 * s, 109 * s), (cx, 112 * s), (cx - 8 * s, 109 * s)], fill=(178, 96, 88))
    d.line([(cx - 11 * s, 104 * s), (cx + 11 * s, 104 * s)], fill=(140, 70, 66), width=1 * s)
    # chin shadow
    d.arc([cx - 10 * s, 112 * s, cx + 10 * s, 120 * s], 0, 180, fill=skin_dark, width=1 * s)
    img = img.convert("RGB").resize((w, h), Image.LANCZOS)
    # faint photo grain
    grain = Image.effect_noise((w, h), 12).convert("L")
    img = Image.blend(img, Image.merge("RGB", (grain, grain, grain)), 0.03)
    return img


# ------------------------------------------------------------- arc text
def _char_tile(ch, fnt, fill):
    tile = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.text((20, 20), ch, font=fnt, fill=fill, anchor="mm")
    return tile


def arc_text(layer, center, radius, text, fnt, fill, top=True):
    """Draw text along a circular arc (top arc reads upright, bottom arc too)."""
    cx, cy = center
    n = len(text)
    if n == 0:
        return
    # angular width per character
    step = 2 * math.asin(min(0.5, (fnt.size * 0.62) / (2 * radius)))
    span = step * (n - 1)
    if top:
        a0 = -math.pi / 2 - span / 2
    else:
        a0 = math.pi / 2 + span / 2
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        a = a0 + (step * i if top else -step * i)
        x = cx + radius * math.cos(a)
        y = cy + radius * math.sin(a)
        tile = _char_tile(ch, fnt, fill)
        rot = math.degrees(a) + (90 if top else -90)
        tile = tile.rotate(-rot, resample=Image.BICUBIC, center=(20, 20))
        layer.paste(tile, (int(x - 20), int(y - 20)), tile)


# ---------------------------------------------------------------- stamps
def circular_stamp(diameter, color, top_text, bottom_text, mid_text, date_text,
                   sub_text="", rotate=0, alpha=215):
    """A round border-control stamp on its own transparent layer."""
    s = 3
    D = diameter * s
    layer = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = color + (alpha,)
    cx = cy = D // 2
    r_out, r_in = D // 2 - 2 * s, D // 2 - 9 * s
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=c, width=3 * s)
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=c, width=1 * s)
    f_arc = font("sans_b", 11 * s)
    arc_text(layer, (cx, cy), (r_out + r_in) // 2 + 1 * s, top_text, f_arc, c, top=True)
    arc_text(layer, (cx, cy), (r_out + r_in) // 2 + 1 * s, bottom_text, f_arc, c, top=False)
    # side stars
    for sx in (-1, 1):
        x = cx + sx * (r_out + r_in) // 2
        d.text((x, cy), "*", font=font("sans_b", 12 * s), fill=c, anchor="mm")
    f_mid = font("sans_b", 12 * s)
    f_date = font("sans_b", 11 * s)
    d.text((cx, cy - 13 * s), mid_text, font=f_mid, fill=c, anchor="mm")
    d.line([(cx - 26 * s, cy - 4 * s), (cx + 26 * s, cy - 4 * s)], fill=c, width=1 * s)
    d.text((cx, cy + 5 * s), date_text, font=f_date, fill=c, anchor="mm")
    if sub_text:
        d.text((cx, cy + 15 * s), sub_text, font=font("sans", 8 * s), fill=c, anchor="mm")
    layer = layer.resize((diameter, diameter), Image.LANCZOS)
    if rotate:
        layer = layer.rotate(rotate, resample=Image.BICUBIC, expand=False)
    return layer


def rect_stamp(w, h, color, lines, rotate=0, alpha=220, font_size=11):
    """A rectangular ink stamp; lines is a list of (text, bold, size)."""
    s = 3
    layer = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = color + (alpha,)
    d.rectangle([2 * s, 2 * s, w * s - 3 * s, h * s - 3 * s], outline=c, width=2 * s)
    d.rectangle([5 * s, 5 * s, w * s - 6 * s, h * s - 6 * s], outline=c, width=1 * s)
    total = sum(sz for _, _, sz in lines) + 4 * (len(lines) - 1)
    y = (h * s - total * s) // 2
    for text, bold, sz in lines:
        f = font("sans_b" if bold else "sans", sz * s)
        d.text((w * s // 2, y), text, font=f, fill=c, anchor="ma")
        y += (sz + 4) * s
    layer = layer.resize((w, h), Image.LANCZOS)
    if rotate:
        layer = layer.rotate(rotate, resample=Image.BICUBIC, expand=True)
    return layer


# ------------------------------------------------------------ visa sticker
def visa_sticker(w=240, h=160):
    s = 3
    layer = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bg = (243, 226, 221, 255)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=4 * s, fill=bg,
                        outline=(150, 90, 90, 255), width=2 * s)
    d.rounded_rectangle([5 * s, 5 * s, w * s - 6 * s, h * s - 6 * s], radius=3 * s,
                        outline=(190, 140, 140, 255), width=1 * s)
    # faint guilloche
    for yy in range(10 * s, h * s - 8 * s, 6 * s):
        pts = [(x, yy + 1.5 * s * math.sin(x / (9.0 * s))) for x in range(8 * s, w * s - 8 * s, 4 * s)]
        d.line(pts, fill=(214, 178, 172, 255), width=1)
    ink = (96, 40, 44)
    ink2 = (60, 30, 34)
    d.text((12 * s, 8 * s), "KINGDOM OF DRAVIA", font=font("serif_b", 10 * s), fill=ink2)
    d.text((w * s - 12 * s, 8 * s), "No. DV-2024-11873", font=font("sans", 8 * s), fill=ink, anchor="ra")
    spaced(d, (12 * s, 22 * s), "VISA", font("sans_b", 15 * s), ink2, tracking=4 * s)
    d.text((w * s - 12 * s, 24 * s), "TYPE C  ·  MULTIPLE", font=font("sans_b", 8 * s), fill=ink, anchor="ra")
    hline(d, 12 * s, w * s - 12 * s, 42 * s, (170, 120, 118), width=1 * s)
    rows = [
        ("VALID FROM", "01 SEP 2024", "UNTIL", "30 NOV 2024"),
        ("DURATION OF STAY", "30 DAYS", "ISSUED IN", "PORT TALMAR"),
        ("ISSUED ON", "28 AUG 2024", "PASSPORT No.", "TM4821937"),
    ]
    y = 48 * s
    for l1, v1, l2, v2 in rows:
        d.text((12 * s, y), l1, font=font("sans", 6 * s), fill=(140, 90, 88))
        d.text((12 * s, y + 7 * s), v1, font=font("sans_b", 8 * s), fill=ink2)
        d.text((128 * s, y), l2, font=font("sans", 6 * s), fill=(140, 90, 88))
        d.text((128 * s, y + 7 * s), v2, font=font("sans_b", 8 * s), fill=ink2)
        y += 17 * s
    hline(d, 12 * s, w * s - 12 * s, y + 1 * s, (170, 120, 118), width=1 * s)
    y += 5 * s
    d.text((12 * s, y), "CONDITION", font=font("sans_b", 6 * s), fill=ink)
    cond = ("EMPLOYMENT PROHIBITED. HOLDER MUST",
            "REGISTER AT THE HARBOUR OFFICE WITHIN",
            "48 HOURS OF ARRIVAL.")
    y += 7 * s
    for line in cond:
        d.text((12 * s, y), line, font=font("sans", 7 * s), fill=ink2)
        y += 9 * s
    y += 2 * s
    d.text((12 * s, y), "VCDRVKOVAC<<ELENA<MARIS<<<<<<<DV202411873", font=font("mono", 6 * s), fill=ink)
    layer = layer.resize((w, h), Image.LANCZOS)
    return layer


# ---------------------------------------------------------------- signature
def signature(w=170, h=30):
    s = 3
    layer = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = (38, 52, 110, 235)
    # flowing pseudo-handwriting: two strokes
    pts = []
    for x in range(4 * s, 78 * s, 2 * s):
        t = (x - 4 * s) / (74 * s)
        y = 16 * s - 9 * s * math.sin(t * math.pi * 3.2) * (1 - t * 0.4) - 4 * s * t
        pts.append((x, y))
    d.line(pts, fill=ink, width=2 * s, joint="curve")
    pts = []
    for x in range(84 * s, w * s - 6 * s, 2 * s):
        t = (x - 84 * s) / (w * s - 90 * s)
        y = 17 * s - 6 * s * math.sin(t * math.pi * 4.5) * (1 - t * 0.5)
        pts.append((x, y))
    d.line(pts, fill=ink, width=2 * s, joint="curve")
    # underline flourish
    d.arc([10 * s, 14 * s, w * s - 10 * s, 30 * s], 10, 170, fill=ink, width=1 * s)
    layer = layer.resize((w, h), Image.LANCZOS)
    return layer


# =================================================================== main
def build():
    img = Image.new("RGB", (W, H), DESK)
    d = ImageDraw.Draw(img)
    # desk: soft radial light, top-left
    light = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    ld.ellipse([-320, -360, 760, 560], fill=(96, 100, 116, 70))
    img = Image.alpha_composite(img.convert("RGBA"), light.filter(ImageFilter.GaussianBlur(120)))
    d = ImageDraw.Draw(img)

    # drop shadow of the open passport
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([38, 178, 994, 862], radius=16, fill=(0, 0, 0, 140))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)

    # cover peeking out around the pages
    d.rounded_rectangle([30, 166, 994, 856], radius=14, fill=COVER)
    d.rounded_rectangle([34, 170, 990, 852], radius=12, outline=GOLD, width=2)
    d.rounded_rectangle([30, 166, 994, 856], radius=14, outline=COVER_DARK, width=2)

    # pages
    LX, RX, PY0, PY1 = 42, 982, 178, 844
    MID = (LX + RX) // 2
    d.rectangle([LX, PY0, MID, PY1], fill=PAGE_L)
    d.rectangle([MID, PY0, RX, PY1], fill=PAGE_R)

    # page texture + guilloche
    guilloche(d, (LX + 8, PY0 + 8, MID - 8, PY1 - 8), (224, 217, 196), step=11, amp=3.0)
    guilloche(d, (MID + 8, PY0 + 8, RX - 8, PY1 - 8), (216, 224, 214), step=11, amp=3.0)
    paper_noise(img, (LX, PY0, MID, PY1))
    paper_noise(img, (MID, PY0, RX, PY1))
    d = ImageDraw.Draw(img)

    # gutter shadow + centre crease
    for i in range(26):
        a = int(70 * (1 - i / 26))
        d.line([(MID - i, PY0), (MID - i, PY1)], fill=(120, 110, 88, a))
        d.line([(MID + i, PY0), (MID + i, PY1)], fill=(110, 116, 104, a))
    d.line([(MID, PY0), (MID, PY1)], fill=(96, 88, 70), width=1)
    # outer page edge shading
    for i in range(10):
        a = int(46 * (1 - i / 10))
        d.line([(LX + i, PY0), (LX + i, PY1)], fill=(140, 132, 108, a))
        d.line([(RX - i, PY0), (RX - i, PY1)], fill=(130, 138, 128, a))
        d.line([(LX, PY1 - i), (RX, PY1 - i)], fill=(140, 132, 108, a))

    # ======================================================= LEFT: data page
    cxL = (LX + MID) // 2  # 277
    arms = coat_of_arms(64)
    img.paste(arms, (cxL - arms.width // 2, 190), arms)
    d = ImageDraw.Draw(img)
    spaced(d, (cxL, 268), "REPUBLIC OF TALMAR", font("serif_b", 20), INK, tracking=2, anchor="ma")
    spaced(d, (cxL, 294), "PASSPORT", font("sans_b", 12), INK_SOFT, tracking=7, anchor="ma")
    hline(d, LX + 30, MID - 30, 316, RULE, 1)
    hline(d, LX + 30, MID - 30, 320, RULE, 1)

    # type / code / number row
    f_lab, f_val, f_valb = font("sans", 8), font("sans", 13), font("sans_b", 14)
    for x, lab, val in ((LX + 24, "TYPE", "P"),
                        (LX + 110, "CODE", "TMR"),
                        (LX + 210, "PASSPORT No.", "TM4821937")):
        d.text((x, 330), lab, font=f_lab, fill=LABEL)
        d.text((x, 340), val, font=f_valb, fill=INK)

    # portrait
    photo = portrait(150, 190)
    img.paste(photo, (LX + 20, 378))
    d = ImageDraw.Draw(img)
    d.rectangle([LX + 20, 378, LX + 170, 568], outline=(120, 112, 92), width=2)
    # embossed seal overlapping photo corner
    seal = circular_stamp(54, (120, 110, 80), "REPUBLIC OF TALMAR", "PORT TALMAR",
                          "★", "12 JUN 2023", rotate=-14, alpha=120)
    img.paste(seal, (LX + 118, 516), seal)
    d = ImageDraw.Draw(img)

    # data fields right of the photo
    fields = [
        ("SURNAME", "KOVAC"),
        ("GIVEN NAMES", "ELENA MARIS"),
        ("NATIONALITY", "TALMARIAN"),
        ("DATE OF BIRTH", "14 MAR 1988"),
        ("PLACE OF BIRTH", "PORT TALMAR"),
        ("SEX", "F"),
    ]
    fx, fy = LX + 186, 378
    for lab, val in fields:
        d.text((fx, fy), lab, font=f_lab, fill=LABEL)
        d.text((fx, fy + 10), val, font=f_valb, fill=INK)
        hline(d, fx, MID - 24, fy + 28, (205, 196, 172), 1)
        fy += 32

    # issue / expiry / authority / signature
    hline(d, LX + 20, MID - 24, 584, RULE, 1)
    d.text((LX + 20, 594), "DATE OF ISSUE", font=f_lab, fill=LABEL)
    d.text((LX + 20, 604), "12 JUN 2023", font=f_valb, fill=INK)
    d.text((LX + 210, 594), "DATE OF EXPIRY", font=f_lab, fill=LABEL)
    d.text((LX + 210, 604), "11 JUN 2033", font=f_valb, fill=INK)
    d.text((LX + 20, 640), "AUTHORITY", font=f_lab, fill=LABEL)
    d.text((LX + 20, 650), "PORT TALMAR", font=f_valb, fill=INK)
    d.text((LX + 20, 676), "PERSONAL No.", font=f_lab, fill=LABEL)
    d.text((LX + 20, 686), "140388-4821", font=f_val, fill=INK)
    d.text((LX + 210, 640), "HOLDER'S SIGNATURE", font=f_lab, fill=LABEL)
    sig = signature(200, 34)
    img.paste(sig, (LX + 210, 652), sig)
    d = ImageDraw.Draw(img)
    hline(d, LX + 210, MID - 24, 690, RULE, 1)
    d.text((LX + 210, 700), "HEIGHT 172 CM  ·  EYES BROWN", font=font("sans", 9), fill=INK_SOFT)

    # MRZ
    d.rectangle([LX + 14, 752, MID - 14, 828], fill=MRZ_BG, outline=(200, 192, 168))
    l1, l2 = mrz_lines()
    f_mrz = font("mono_b", 16)
    d.text((LX + 24, 762), l1, font=f_mrz, fill=INK)
    d.text((LX + 24, 788), l2, font=f_mrz, fill=INK)

    # ====================================================== RIGHT: visa page
    cxR = (MID + RX) // 2  # 747
    spaced(d, (cxR, 192), "VISAS", font("sans_b", 13), INK_SOFT, tracking=8, anchor="ma")
    d.text((RX - 24, 192), "12", font=font("sans_b", 12), fill=INK_SOFT, anchor="ra")
    d.text((MID + 24, 192), "VISA", font=font("sans", 9), fill=LABEL)
    hline(d, MID + 24, RX - 24, 216, (170, 178, 168), 1)

    # Dravian visa sticker
    visa = visa_sticker(240, 160)
    img.paste(visa, (MID + 24, 236), visa)
    d = ImageDraw.Draw(img)
    fee = rect_stamp(96, 26, STAMP_PURPLE,
                     [("FEE 12 ZLV", True, 10), ("PAID", True, 10)],
                     rotate=-10, alpha=210)
    img.paste(fee, (MID + 268, 238), fee)
    d = ImageDraw.Draw(img)

    # border stamps: a coherent travel history, all after issue (12 JUN 2023)
    def stamp(cx, cy, dia, color, top, bottom, mid, date, sub, rot):
        st = circular_stamp(dia, color, top, bottom, mid, date, sub, rotate=rot)
        img.paste(st, (cx - st.width // 2, cy - st.height // 2), st)

    stamp(880, 310, 96, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
          "EXIT", "01 SEP 2024", "A-14", -9)
    stamp(800, 402, 100, STAMP_BLUE, "KINGDOM OF DRAVIA", "KORVAC",
          "ENTRY", "02 SEP 2024", "B-07", 7)
    stamp(620, 470, 96, STAMP_BLUE, "KINGDOM OF DRAVIA", "KORVAC",
          "EXIT", "18 SEP 2024", "B-07", -6)
    stamp(880, 482, 96, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
          "ENTRY", "19 SEP 2024", "A-14", 11)
    stamp(610, 586, 92, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
          "EXIT", "04 MAR 2025", "A-02", 8)
    stamp(880, 600, 100, STAMP_RED, "CORVINIA", "VELIKA",
          "ENTRY", "05 MAR 2025", "C-21", -8)
    stamp(630, 700, 96, STAMP_RED, "CORVINIA", "VELIKA",
          "EXIT", "21 MAR 2025", "C-21", 6)
    stamp(880, 712, 96, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
          "ENTRY", "22 MAR 2025", "A-14", -12)
    d = ImageDraw.Draw(img)

    # endorsement: the telling paperwork detail — a harbour pilot of a
    # free port, stamped by the harbour master rather than the police.
    end = rect_stamp(422, 56, STAMP_BLUE, [
        ("ENDORSEMENT 7 — HOLDER IS A LICENSED HARBOUR PILOT,", True, 11),
        ("PORT OF TALMAR. VALID FOR CREW-LIST PURPOSES ONLY.", True, 11),
    ], rotate=-1, alpha=225)
    img.paste(end, (MID + 24, 766), end)
    d = ImageDraw.Draw(img)

    # final soft vignette over the desk only (keep pages crisp)
    img.save("/tmp/_passport_preview.png", optimize=True)
    return img


def main():
    img = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    size = OUT.stat().st_size
    print(f"wrote {OUT} {img.size} {size} bytes")
    if size > 1048576:
        raise SystemExit("entry.png exceeds 1 MiB")


if __name__ == "__main__":
    main()
