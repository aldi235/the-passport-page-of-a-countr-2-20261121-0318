#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws an open passport spread for the invented free-port Republic of
Talmar (Adriatic) in PURE PYTHON STDLIB: no PIL, no third-party code, no
external files at all. The program builds an RGB pixel buffer, draws
every element (desk, cover, pages, portrait, coat of arms, visa sticker,
stamps) with a small hand-rolled drawing engine, renders text with an
embedded 5x7 bitmap font, and encodes the result as a PNG with zlib and
struct.

Writes /output/entry.png (1024x1024, under 1 MiB). Deterministic: no
randomness, no network, no clock. Runs on a plain python:3.13 image.
"""

import math
import os
import struct
import zlib
from binascii import crc32

W, H = 1024, 1024
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT_PATH = os.path.join(OUT_DIR, "entry.png")

# ---------------------------------------------------------------- colours
DESK = (46, 49, 57)
DESK_GLOW = (96, 100, 116)
COVER = (106, 28, 40)
COVER_DARK = (74, 18, 27)
GOLD = (198, 164, 92)
PAGE_L = (246, 241, 227)    # data page cream
PAGE_R = (233, 239, 232)    # visa page pale green-grey
INK = (28, 32, 46)
INK_SOFT = (74, 78, 92)
LABEL = (110, 105, 88)
RULE = (150, 142, 118)
MRZ_BG = (252, 250, 244)
STAMP_BLUE = (32, 74, 138)
STAMP_GREEN = (18, 96, 66)
STAMP_RED = (148, 52, 40)
STAMP_PURPLE = (104, 58, 130)

# ------------------------------------------------------------- bitmap font
# 5x7 pixel glyphs, '#' = ink. Lowercase maps to uppercase at draw time.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "\u00b7": (".....", ".....", ".##..", ".##..", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", "#####", ".....", "....."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}


def glyph_of(ch):
    g = FONT.get(ch)
    if g is None:
        g = FONT.get(ch.upper(), FONT[" "])
    return g


# ------------------------------------------------------------------ canvas
class Canvas:
    """An RGB (or RGBA) pixel buffer with a small drawing engine."""

    def __init__(self, w, h, color=(0, 0, 0), alpha=False):
        self.w = w
        self.h = h
        self.alpha = alpha
        self.bpp = 4 if alpha else 3
        self.buf = bytearray(w * h * self.bpp)
        if alpha:
            # transparent by default; color is only used as an opaque fill
            if color != (0, 0, 0):
                self.fill(color, 255)
        elif color != (0, 0, 0):
            self.fill(color, 255)

    # ------------------------------------------------------------ pixels
    def _idx(self, x, y):
        return (y * self.w + x) * self.bpp

    def blend_px(self, x, y, rgb, a=255):
        if x < 0 or y < 0 or x >= self.w or y >= self.h or a <= 0:
            return
        i = self._idx(x, y)
        if a >= 255:
            self.buf[i] = rgb[0]
            self.buf[i + 1] = rgb[1]
            self.buf[i + 2] = rgb[2]
            if self.alpha:
                self.buf[i + 3] = 255
            return
        if self.alpha:
            # source-over onto an RGBA buffer
            da = self.buf[i + 3]
            sa = a
            oa = sa + da * (255 - sa) // 255
            if oa == 0:
                return
            for k in range(3):
                self.buf[i + k] = (rgb[k] * sa + self.buf[i + k] * da * (255 - sa) // 255) // oa
            self.buf[i + 3] = oa
        else:
            inv = 255 - a
            self.buf[i] = (rgb[0] * a + self.buf[i] * inv) // 255
            self.buf[i + 1] = (rgb[1] * a + self.buf[i + 1] * inv) // 255
            self.buf[i + 2] = (rgb[2] * a + self.buf[i + 2] * inv) // 255

    def get_px(self, x, y):
        i = self._idx(x, y)
        if self.alpha:
            return (self.buf[i], self.buf[i + 1], self.buf[i + 2], self.buf[i + 3])
        return (self.buf[i], self.buf[i + 1], self.buf[i + 2])

    # ------------------------------------------------------------ spans
    def hspan(self, x0, x1, y, rgb, a=255):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w - 1, x1)
        if x1 < x0:
            return
        if a >= 255 and not self.alpha:
            row = y * self.w * 3
            self.buf[row + x0 * 3: row + (x1 + 1) * 3] = bytes(rgb) * (x1 - x0 + 1)
            return
        for x in range(x0, x1 + 1):
            self.blend_px(x, y, rgb, a)

    def fill(self, rgb, a=255):
        for y in range(self.h):
            self.hspan(0, self.w - 1, y, rgb, a)

    # ------------------------------------------------------------ shapes
    def rect(self, x0, y0, x1, y1, rgb, a=255):
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            self.hspan(x0, x1, y, rgb, a)

    def line(self, x0, y0, x1, y1, rgb, width=1, a=255):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = width // 2
        for i in range(steps + 1):
            x = int(round(x0 + dx * i / steps))
            y = int(round(y0 + dy * i / steps))
            if width <= 1:
                self.blend_px(x, y, rgb, a)
            else:
                self.rect(x - r, y - r, x + r, y + r, rgb, a)

    def polyline(self, pts, rgb, width=1, a=255):
        for i in range(len(pts) - 1):
            self.line(int(pts[i][0]), int(pts[i][1]),
                      int(pts[i + 1][0]), int(pts[i + 1][1]), rgb, width, a)

    def ellipse(self, cx, cy, rx, ry, rgb, a=255, fill=True, width=1):
        if rx <= 0 or ry <= 0:
            return
        y0 = max(0, int(cy - ry))
        y1 = min(self.h - 1, int(cy + ry))
        for y in range(y0, y1 + 1):
            dy = (y + 0.5 - cy) / ry
            if abs(dy) >= 1:
                continue
            dx = rx * math.sqrt(1 - dy * dy)
            x0, x1 = int(cx - dx), int(cx + dx)
            if fill:
                self.hspan(x0, x1, y, rgb, a)
                continue
            rxi, ryi = rx - width, ry - width
            if rxi <= 0 or ryi <= 0:
                self.hspan(x0, x1, y, rgb, a)
                continue
            dyi = (y + 0.5 - cy) / ryi
            if abs(dyi) >= 1:
                self.hspan(x0, x1, y, rgb, a)
            else:
                dxi = rxi * math.sqrt(1 - dyi * dyi)
                ix0, ix1 = int(cx - dxi), int(cx + dxi)
                self.hspan(x0, ix0, y, rgb, a)
                self.hspan(ix1, x1, y, rgb, a)

    def circle(self, cx, cy, r, rgb, a=255, fill=True, width=1):
        self.ellipse(cx, cy, r, r, rgb, a, fill, width)

    def polygon(self, pts, rgb, a=255):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, int(min(ys)))
        y1 = min(self.h - 1, int(max(ys)))
        n = len(pts)
        for y in range(y0, y1 + 1):
            ym = y + 0.5
            xs = []
            for i in range(n):
                x0, yy0 = pts[i]
                x1, yy1 = pts[(i + 1) % n]
                if (yy0 <= ym < yy1) or (yy1 <= ym < yy0):
                    t = (ym - yy0) / (yy1 - yy0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hspan(int(xs[i]), int(xs[i + 1]), y, rgb, a)

    def arc(self, cx, cy, rx, ry, a0_deg, a1_deg, rgb, width=1, a=255):
        span = abs(a1_deg - a0_deg)
        n = max(8, int(span * max(rx, ry) / 24))
        pts = []
        for i in range(n + 1):
            t = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
            pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
        self.polyline(pts, rgb, width, a)

    def pie(self, cx, cy, rx, ry, a0_deg, a1_deg, rgb, a=255):
        """A filled pie wedge: centre plus the arc from a0 to a1."""
        span = abs(a1_deg - a0_deg)
        n = max(8, int(span * max(rx, ry) / 24))
        pts = [(cx, cy)]
        for i in range(n + 1):
            t = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
            pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
        self.polygon(pts, rgb, a)

    def rrect(self, x0, y0, x1, y1, radius, rgb, a=255):
        """Filled rounded rectangle (scanline, corner radius)."""
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            inset = 0
            if y - y0 < radius:
                dy = radius - (y - y0)
                inset = radius - int(math.sqrt(max(0, radius * radius - dy * dy)))
            elif y1 - y < radius:
                dy = radius - (y1 - y)
                inset = radius - int(math.sqrt(max(0, radius * radius - dy * dy)))
            self.hspan(x0 + inset, x1 - inset, y, rgb, a)

    def rrect_outline(self, x0, y0, x1, y1, radius, rgb, width=1, a=255):
        r = radius
        self.line(x0 + r, y0, x1 - r, y0, rgb, width, a)
        self.line(x0 + r, y1, x1 - r, y1, rgb, width, a)
        self.line(x0, y0 + r, x0, y1 - r, rgb, width, a)
        self.line(x1, y0 + r, x1, y1 - r, rgb, width, a)
        self.arc(x0 + r, y0 + r, r, r, 180, 270, rgb, width, a)
        self.arc(x1 - r, y0 + r, r, r, 270, 360, rgb, width, a)
        self.arc(x1 - r, y1 - r, r, r, 0, 90, rgb, width, a)
        self.arc(x0 + r, y1 - r, r, r, 90, 180, rgb, width, a)

    # -------------------------------------------------------------- text
    def _glyph(self, x, y, s, ch, rgb, a=255):
        g = glyph_of(ch)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "#":
                    if s == 1:
                        self.blend_px(x + col, y + row, rgb, a)
                    else:
                        self.rect(x + col * s, y + row * s,
                                  x + col * s + s - 1, y + row * s + s - 1,
                                  rgb, a)

    def text(self, x, y, s, string, rgb, tracking=0, anchor="la",
             bold=False, a=255):
        """Draw text; y is the top. anchor: la (left), ma (centre), ra."""
        n = len(string)
        w = n * 5 * s + max(0, n - 1) * tracking
        if anchor == "ma":
            x -= w // 2
        elif anchor == "ra":
            x -= w
        cx = x
        for ch in string:
            self._glyph(cx, y, s, ch, rgb, a)
            if bold and s >= 2:
                self._glyph(cx + 1, y, s, ch, rgb, a)
            cx += 5 * s + tracking
        return w

    def text_width(self, s, string, tracking=0):
        n = len(string)
        return n * 5 * s + max(0, n - 1) * tracking

    def glyph_rotated(self, cx, cy, angle_deg, s, ch, rgb, a=255):
        """Draw one glyph rotated clockwise by angle_deg around (cx, cy)."""
        g = glyph_of(ch)
        t = math.radians(angle_deg)
        ct, st = math.cos(t), math.sin(t)
        half = int(3.5 * s) + s
        for dy in range(-half, half + 1):
            for dx in range(-half, half + 1):
                lx = dx * ct + dy * st
                ly = -dx * st + dy * ct
                col = int((lx + 2.5 * s) // s)
                row = int((ly + 3.5 * s) // s)
                if 0 <= col < 5 and 0 <= row < 7 and g[row][col] == "#":
                    self.blend_px(cx + dx, cy + dy, rgb, a)

    def arc_text(self, cx, cy, radius, text, s, rgb, top=True, tracking=1,
                 a=255):
        """Text along a circular arc. Top arc reads upright across the top;
        bottom arc reads left-to-right along the bottom."""
        n = len(text)
        if n == 0 or radius <= 0:
            return
        step = (5 * s + tracking) / radius  # radians per character
        span = step * (n - 1)
        if top:
            a0 = -math.pi / 2 - span / 2
        else:
            a0 = math.pi / 2 + span / 2
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            ang = a0 + (step * i if top else -step * i)
            x = cx + radius * math.cos(ang)
            y = cy + radius * math.sin(ang)
            rot = math.degrees(ang) + (90 if top else -90)
            self.glyph_rotated(int(round(x)), int(round(y)), rot, s, ch,
                               rgb, a)

    # ------------------------------------------------------------ compose
    def downsample2x(self):
        """Half-size canvas: each pixel is the mean of a 2x2 block."""
        w2, h2 = self.w // 2, self.h // 2
        out = Canvas(w2, h2, alpha=self.alpha)
        sb, db = self.buf, out.buf
        bpp = self.bpp
        for y in range(h2):
            for x in range(w2):
                i00 = ((2 * y) * self.w + 2 * x) * bpp
                i01 = i00 + bpp
                i10 = ((2 * y + 1) * self.w + 2 * x) * bpp
                i11 = i10 + bpp
                o = (y * w2 + x) * bpp
                for k in range(bpp):
                    db[o + k] = (sb[i00 + k] + sb[i01 + k] +
                                 sb[i10 + k] + sb[i11 + k]) // 4
        return out

    def paste(self, src, x, y):
        """Paste src onto this canvas at (x, y); honours src alpha."""
        for sy in range(src.h):
            dy = y + sy
            if dy < 0 or dy >= self.h:
                continue
            for sx in range(src.w):
                dx = x + sx
                if dx < 0 or dx >= self.w:
                    continue
                if src.alpha:
                    r, g, b, al = src.get_px(sx, sy)
                    if al:
                        self.blend_px(dx, dy, (r, g, b), al)
                else:
                    self.blend_px(dx, dy, src.get_px(sx, sy), 255)

    def paste_rotated(self, src2x, cx, cy, angle_deg, global_alpha=255):
        """Paste a 2x RGBA layer rotated by angle_deg (clockwise) around
        (cx, cy), downsampled 2x in the same step. The pasted image is
        src2x.w//2 by src2x.h//2."""
        ow, oh = src2x.w // 2, src2x.h // 2
        t = math.radians(angle_deg)
        ct, st = math.cos(t), math.sin(t)
        # bounding box of the rotated output
        hw, hh = ow / 2.0, oh / 2.0
        corners = [(hw, hh), (-hw, hh), (hw, -hh), (-hw, -hh)]
        bx = max(abs(x * ct - y * st) for x, y in corners)
        by = max(abs(x * st + y * ct) for x, y in corners)
        x0 = int(cx - bx - 1)
        x1 = int(cx + bx + 1)
        y0 = int(cy - by - 1)
        y1 = int(cy + by + 1)
        sb = src2x.buf
        sw = src2x.w
        for oy in range(y0, y1 + 1):
            if oy < 0 or oy >= self.h:
                continue
            for ox in range(x0, x1 + 1):
                if ox < 0 or ox >= self.w:
                    continue
                # offset from centre, inverse-rotated into output space
                dx, dy = ox - cx, oy - cy
                lx = dx * ct + dy * st
                ly = -dx * st + dy * ct
                if abs(lx) > hw or abs(ly) > hh:
                    continue
                # into 2x source coordinates (2x2 block average)
                sx = (lx + hw) * 2
                sy = (ly + hh) * 2
                ix, iy = int(sx), int(sy)
                if ix < 0 or iy < 0 or ix + 1 >= sw or iy + 1 >= src2x.h:
                    continue
                i00 = (iy * sw + ix) * 4
                i01 = i00 + 4
                i10 = ((iy + 1) * sw + ix) * 4
                i11 = i10 + 4
                al = (sb[i00 + 3] + sb[i01 + 3] + sb[i10 + 3] + sb[i11 + 3]) // 4
                if al == 0:
                    continue
                r = (sb[i00] + sb[i01] + sb[i10] + sb[i11]) // 4
                g = (sb[i00 + 1] + sb[i01 + 1] + sb[i10 + 1] + sb[i11 + 1]) // 4
                b = (sb[i00 + 2] + sb[i01 + 2] + sb[i10 + 2] + sb[i11 + 2]) // 4
                self.blend_px(ox, oy, (r, g, b), al * global_alpha // 255)


# ------------------------------------------------------------ PNG encoder
def _png_chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path, cv):
    """Encode an RGB canvas as a PNG (colour type 2, 8-bit)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: None
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += _png_chunk(b"IDAT", comp)
    png += _png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------- MRZ check digits
def _mrz_value(ch):
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 55  # A=10 .. Z=35


def _mrz_check(s):
    weights = (7, 3, 1)
    return str(sum(_mrz_value(c) * weights[i % 3]
                   for i, c in enumerate(s)) % 10)


def mrz_lines():
    line1 = "P<TMRKOVAC<<ELENA<MARIS"
    line1 = line1 + "<" * (44 - len(line1))
    num, dob, exp = "TM4821937", "880314", "330611"
    pers = "<" * 14
    body = (num + _mrz_check(num) + "TMR" + dob + _mrz_check(dob) + "F" +
            exp + _mrz_check(exp) + pers + _mrz_check(pers))
    line2 = body + _mrz_check(body)
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return line1, line2


def star_points(cx, cy, r_out, r_in, rot_deg=-90):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot_deg + i * 36)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ------------------------------------------------------------ coat of arms
def coat_of_arms():
    """Talmar arms: gold star, shield with anchor. Drawn at 2x, returned
    downsampled (64x76)."""
    SC = 2
    cv = Canvas(64 * SC, 76 * SC, alpha=True)
    navy = (26, 48, 84)
    gold = (176, 138, 62)
    cream = (244, 238, 220)

    def poly(pts, rgb, a=255):
        cv.polygon([(x * SC, y * SC) for x, y in pts], rgb, a)

    def line(x0, y0, x1, y1, rgb, width=1, a=255):
        cv.line(x0 * SC, y0 * SC, x1 * SC, y1 * SC, rgb, width * SC, a)

    def arc(x0, y0, x1, y1, a0, a1, rgb, width=1, a=255):
        cv.arc((x0 + x1) / 2 * SC, (y0 + y1) / 2 * SC,
               (x1 - x0) / 2 * SC, (y1 - y0) / 2 * SC, a0, a1,
               rgb, width * SC, a)

    # star above the shield
    poly(star_points(32, 15, 12, 5.4), gold)
    # shield
    shield = [(3, 32), (61, 32), (61, 58), (32, 74), (3, 58)]
    poly(shield, cream)
    # shield outline (drawn as a polyline over the fill)
    cv.polyline([(x * SC, y * SC) for x, y in shield + [shield[0]]],
                navy, 2 * SC)
    # anchor
    ax, ay = 32, 50
    line(ax, ay - 12, ax, ay + 14, navy, 3)
    arc(ax - 5, ay - 17, ax + 5, ay - 7, 0, 360, navy, 2)
    line(ax - 11, ay - 8, ax + 11, ay - 8, navy, 3)
    arc(ax - 13, ay - 2, ax + 13, ay + 24, 20, 160, navy, 3)
    poly([(ax - 13, ay + 8), (ax - 6, ay + 6), (ax - 11, ay + 14)], navy)
    poly([(ax + 13, ay + 8), (ax + 6, ay + 6), (ax + 11, ay + 14)], navy)
    return cv.downsample2x()


# ---------------------------------------------------------------- portrait
def portrait():
    """Stylised flat passport portrait of Elena Kovac, drawn in code.
    Drawn at 2x on a layer, returned downsampled (150x190)."""
    SC = 2
    cv = Canvas(150 * SC, 190 * SC)
    cx = 75

    def ell(x0, y0, x1, y1, rgb, a=255, fill=True, width=1):
        cv.ellipse((x0 + x1) / 2 * SC, (y0 + y1) / 2 * SC,
                   (x1 - x0) / 2 * SC, (y1 - y0) / 2 * SC,
                   rgb, a, fill, width * SC)

    def poly(pts, rgb, a=255):
        cv.polygon([(x * SC, y * SC) for x, y in pts], rgb, a)

    def pie(x0, y0, x1, y1, a0, a1, rgb, a=255):
        cv.pie((x0 + x1) / 2 * SC, (y0 + y1) / 2 * SC,
               (x1 - x0) / 2 * SC, (y1 - y0) / 2 * SC, a0, a1, rgb, a)

    def line(x0, y0, x1, y1, rgb, width=1, a=255):
        cv.line(x0 * SC, y0 * SC, x1 * SC, y1 * SC, rgb, width * SC, a)

    def arc(x0, y0, x1, y1, a0, a1, rgb, width=1, a=255):
        cv.arc((x0 + x1) / 2 * SC, (y0 + y1) / 2 * SC,
               (x1 - x0) / 2 * SC, (y1 - y0) / 2 * SC, a0, a1,
               rgb, width * SC, a)

    def rrect(x0, y0, x1, y1, r, rgb, a=255):
        cv.rrect(x0 * SC, y0 * SC, x1 * SC, y1 * SC, r * SC, rgb, a)

    # backdrop: soft blue-grey vertical gradient
    for y in range(190 * SC):
        t = y / (190 * SC)
        c = tuple(int(a + (b - a) * t)
                  for a, b in zip((168, 182, 194), (205, 212, 218)))
        cv.hspan(0, 150 * SC - 1, y, c)
    # soft light behind the head
    ell(27, 4, 123, 118, (232, 236, 240), a=55)
    skin = (226, 178, 140)
    skin_dark = (206, 152, 116)
    hair_c = (58, 40, 30)
    hair_hi = (88, 62, 44)
    # hair back mass (shoulder length)
    ell(cx - 62, 8, cx + 62, 128, hair_c)
    # shoulders / blazer
    ell(cx - 118, 118, cx + 118, 320, (38, 52, 74))
    ell(cx - 118, 118, cx + 118, 320, (28, 40, 58), fill=False, width=2)
    # blouse V
    poly([(cx - 26, 132), (cx + 26, 132), (cx, 178)], (240, 238, 232))
    # blazer lapels
    poly([(cx - 26, 132), (cx - 8, 150), (cx, 178), (cx - 34, 152)], (30, 42, 60))
    poly([(cx + 26, 132), (cx + 8, 150), (cx, 178), (cx + 34, 152)], (30, 42, 60))
    # neck
    rrect(cx - 16, 108, cx + 16, 142, 8, skin_dark)
    rrect(cx - 15, 106, cx + 15, 138, 7, skin)
    # ears
    ell(cx - 52, 62, cx - 38, 88, skin_dark)
    ell(cx + 38, 62, cx + 52, 88, skin_dark)
    # face
    ell(cx - 44, 26, cx + 44, 122, skin)
    # cheek shading + highlight (soft, unblurred)
    ell(cx + 6, 40, cx + 44, 118, (198, 140, 105), a=55)
    ell(cx - 42, 30, cx - 8, 70, (244, 208, 176), a=65)
    ell(cx - 30, 92, cx - 12, 106, (214, 138, 118), a=50)
    ell(cx + 12, 92, cx + 30, 106, (214, 138, 118), a=50)
    # hair front: centre part, framing the face
    pie(cx - 48, 10, cx + 48, 84, 180, 360, hair_c)
    ell(cx - 50, 18, cx - 30, 108, hair_c)
    ell(cx + 30, 18, cx + 50, 108, hair_c)
    poly([(cx - 46, 34), (cx - 20, 22), (cx, 30), (cx + 20, 22),
          (cx + 46, 34), (cx + 40, 52), (cx, 40), (cx - 40, 52)], hair_c)
    for sx, sy, ex, ey in ((-40, 30, -32, 88), (40, 30, 32, 88),
                           (-14, 26, -22, 60), (14, 26, 22, 60)):
        line(cx + sx, sy, cx + ex, ey, hair_hi, 2)
    # eyebrows
    arc(cx - 32, 58, cx - 8, 72, 200, 340, (52, 36, 26), 3)
    arc(cx + 8, 58, cx + 32, 72, 200, 340, (52, 36, 26), 3)
    # eyes
    for ex in (-20, 20):
        ell(cx + ex - 9, 72, cx + ex + 9, 82, (250, 248, 244))
        ell(cx + ex - 5, 72, cx + ex + 5, 82, (46, 34, 26))
        ell(cx + ex - 2, 73, cx + ex + 1, 76, (255, 255, 255))
        arc(cx + ex - 10, 70, cx + ex + 10, 82, 180, 360, (40, 30, 24), 2)
    # nose
    line(cx + 1, 80, cx - 1, 94, skin_dark, 2)
    arc(cx - 5, 92, cx + 5, 99, 0, 180, skin_dark, 2)
    # lips
    poly([(cx - 12, 104), (cx, 101), (cx + 12, 104), (cx + 8, 109),
          (cx, 112), (cx - 8, 109)], (178, 96, 88))
    line(cx - 11, 104, cx + 11, 104, (140, 70, 66), 1)
    # chin shadow
    arc(cx - 10, 112, cx + 10, 120, 0, 180, skin_dark, 1)
    return cv.downsample2x()


# ------------------------------------------------------------------ stamps
def circular_stamp_layer(diameter, color, top_text, bottom_text, mid_text,
                         date_text, sub_text="", alpha=215, mid_star=False,
                         arc_scale=2):
    """A round border-control stamp on a transparent 2x layer."""
    SC = 2
    D = diameter * SC
    layer = Canvas(D, D, alpha=True)
    cx = cy = D // 2
    r_out = D // 2 - 2 * SC
    r_in = D // 2 - 9 * SC
    layer.ellipse(cx, cy, r_out, r_out, color, a=alpha, fill=False,
                  width=3 * SC)
    layer.ellipse(cx, cy, r_in, r_in, color, a=alpha, fill=False, width=SC)
    mid_r = (r_out + r_in) // 2 + SC
    layer.arc_text(cx, cy, mid_r, top_text, arc_scale, color, top=True,
                   tracking=1, a=alpha)
    layer.arc_text(cx, cy, mid_r, bottom_text, arc_scale, color, top=False,
                   tracking=1, a=alpha)
    # side stars
    for sx in (-1, 1):
        layer.polygon(star_points(cx + sx * mid_r, cy, 6 * SC, 2.7 * SC),
                      color, a=alpha)
    if mid_star:
        layer.polygon(star_points(cx, cy - 13 * SC, 8 * SC, 3.6 * SC),
                      color, a=alpha)
    else:
        layer.text(cx, cy - 13 * SC - 10, 3, mid_text, color, anchor="ma",
                   bold=True, a=alpha)
    layer.line(cx - 26 * SC, cy - 4 * SC, cx + 26 * SC, cy - 4 * SC,
               color, width=SC, a=alpha)
    layer.text(cx, cy + 5 * SC - 7, 2, date_text, color, anchor="ma",
               bold=True, a=alpha)
    if sub_text:
        layer.text(cx, cy + 15 * SC - 7, 2, sub_text, color, anchor="ma",
                   a=alpha)
    return layer


def rect_stamp_layer(w, h, color, lines, alpha=220):
    """A rectangular ink stamp on a transparent 2x layer.
    lines: list of (text, bold, scale)."""
    SC = 2
    layer = Canvas(w * SC, h * SC, alpha=True)
    layer.rrect_outline(2 * SC, 2 * SC, w * SC - 3 * SC, h * SC - 3 * SC,
                        2 * SC, color, width=2 * SC, a=alpha)
    layer.rrect_outline(5 * SC, 5 * SC, w * SC - 6 * SC, h * SC - 6 * SC,
                        2 * SC, color, width=SC, a=alpha)
    total = sum(7 * sz for _, _, sz in lines) + 4 * (len(lines) - 1)
    y = (h * SC - total) // 2
    for text, bold, sz in lines:
        layer.text(w * SC // 2, y, sz, text, color, anchor="ma",
                   bold=bold, a=alpha)
        y += 7 * sz + 4
    return layer


# ------------------------------------------------------------ visa sticker
def draw_visa(cv, x, y, w=240, h=160):
    """The Dravian visa sticker, drawn directly on the main canvas."""
    bg = (243, 226, 221)
    ink = (96, 40, 44)
    ink2 = (60, 30, 34)
    cv.rrect(x, y, x + w - 1, y + h - 1, 4, bg)
    cv.rrect_outline(x, y, x + w - 1, y + h - 1, 4, (150, 90, 90), 2)
    cv.rrect_outline(x + 5, y + 5, x + w - 6, y + h - 6, 3, (190, 140, 140), 1)
    # faint guilloche
    for yy in range(y + 10, y + h - 8, 6):
        pts = [(xx, yy + 1.5 * math.sin(xx / 9.0))
               for xx in range(x + 8, x + w - 8, 4)]
        cv.polyline(pts, (214, 178, 172), 1)
    cv.text(x + 12, y + 8, 1, "KINGDOM OF DRAVIA", ink2, bold=True)
    cv.text(x + w - 12, y + 8, 1, "No. DV-2024-11873", ink, anchor="ra")
    cv.text(x + 12, y + 22, 2, "VISA", ink2, tracking=4, bold=True)
    cv.text(x + w - 12, y + 24, 1, "TYPE C  \u00b7  MULTIPLE", ink,
            anchor="ra", bold=True)
    cv.line(x + 12, y + 42, x + w - 12, y + 42, (170, 120, 118), 1)
    rows = [
        ("VALID FROM", "01 SEP 2024", "UNTIL", "30 NOV 2024"),
        ("DURATION OF STAY", "30 DAYS", "ISSUED IN", "PORT TALMAR"),
        ("ISSUED ON", "28 AUG 2024", "PASSPORT No.", "TM4821937"),
    ]
    ry = y + 48
    for l1, v1, l2, v2 in rows:
        cv.text(x + 12, ry, 1, l1, (140, 90, 88))
        cv.text(x + 12, ry + 7, 1, v1, ink2, bold=True)
        cv.text(x + 128, ry, 1, l2, (140, 90, 88))
        cv.text(x + 128, ry + 7, 1, v2, ink2, bold=True)
        ry += 17
    cv.line(x + 12, ry + 1, x + w - 12, ry + 1, (170, 120, 118), 1)
    ry += 5
    cv.text(x + 12, ry, 1, "CONDITION", ink, bold=True)
    cond = ("EMPLOYMENT PROHIBITED. HOLDER MUST",
            "REGISTER AT THE HARBOUR OFFICE WITHIN",
            "48 HOURS OF ARRIVAL.")
    ry += 7
    for ln in cond:
        cv.text(x + 12, ry, 1, ln, ink2)
        ry += 9
    ry += 2
    cv.text(x + 12, ry, 1, "VCDRVKOVAC<<ELENA<MARIS<<<<<<<DV202411873", ink)


# --------------------------------------------------------------- signature
def draw_signature(cv, x, y, w=200, h=34):
    """Flowing pseudo-handwriting: two sine strokes and an underline."""
    ink = (38, 52, 110)
    pts = []
    for xx in range(4, 78, 2):
        t = (xx - 4) / 74
        yy = 16 - 9 * math.sin(t * math.pi * 3.2) * (1 - t * 0.4) - 4 * t
        pts.append((x + xx, y + yy))
    cv.polyline(pts, ink, 2, a=235)
    pts = []
    for xx in range(84, w - 6, 2):
        t = (xx - 84) / (w - 90)
        yy = 17 - 6 * math.sin(t * math.pi * 4.5) * (1 - t * 0.5)
        pts.append((x + xx, y + yy))
    cv.polyline(pts, ink, 2, a=235)
    cv.arc(x + w // 2, y + 22, w // 2 - 10, 8, 10, 170, ink, 1, a=235)


def guilloche(cv, box, color, step=11, amp=3.0):
    """Fine wavy security lines across a page area."""
    x0, y0, x1, y1 = box
    y = y0
    while y < y1:
        pts = []
        x = x0
        while x <= x1:
            pts.append((x, y + amp * math.sin((x - x0) / 26.0)))
            x += 6
        cv.polyline(pts, color, 1)
        y += step


# =================================================================== build
def build():
    cv = Canvas(W, H, DESK)

    # drop shadow: the cover hides all but the bottom strip
    cv.rect(38, 856, 994, 862, (0, 0, 0), a=90)

    # cover peeking out around the pages
    cv.rrect(30, 166, 994, 856, 14, COVER)
    cv.rrect_outline(34, 170, 990, 852, 12, GOLD, 2)
    cv.rrect_outline(30, 166, 994, 856, 14, COVER_DARK, 2)

    # pages
    LX, RX, PY0, PY1 = 42, 982, 178, 844
    MID = (LX + RX) // 2
    cv.rect(LX, PY0, MID, PY1, PAGE_L)
    cv.rect(MID, PY0, RX, PY1, PAGE_R)

    # security guilloche on both pages
    guilloche(cv, (LX + 8, PY0 + 8, MID - 8, PY1 - 8), (224, 217, 196))
    guilloche(cv, (MID + 8, PY0 + 8, RX - 8, PY1 - 8), (216, 224, 214))

    # faint paper noise (deterministic LCG, no random module needed)
    seed = 20261121

    def rnd():
        nonlocal seed
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        return seed

    for _ in range(3000):
        x = LX + rnd() % (RX - LX)
        y = PY0 + rnd() % (PY1 - PY0)
        cv.blend_px(x, y, (90, 85, 70), 4 + rnd() % 8)

    # gutter shadow + centre crease
    for i in range(26):
        a = int(70 * (1 - i / 26))
        cv.line(MID - i, PY0, MID - i, PY1, (120, 110, 88), 1, a)
        cv.line(MID + i, PY0, MID + i, PY1, (110, 116, 104), 1, a)
    cv.line(MID, PY0, MID, PY1, (96, 88, 70), 1)
    # outer page edge shading
    for i in range(10):
        a = int(46 * (1 - i / 10))
        cv.line(LX + i, PY0, LX + i, PY1, (140, 132, 108), 1, a)
        cv.line(RX - i, PY0, RX - i, PY1, (130, 138, 128), 1, a)
        cv.line(LX, PY1 - i, RX, PY1 - i, (140, 132, 108), 1, a)

    # ======================================================= LEFT: data page
    cxL = (LX + MID) // 2  # 277
    arms = coat_of_arms()
    cv.paste(arms, cxL - 32, 190)
    cv.text(cxL, 268, 3, "REPUBLIC OF TALMAR", INK, tracking=2,
            anchor="ma", bold=True)
    cv.text(cxL, 294, 2, "PASSPORT", INK_SOFT, tracking=7, anchor="ma",
            bold=True)
    cv.line(LX + 30, 316, MID - 30, 316, RULE, 1)
    cv.line(LX + 30, 320, MID - 30, 320, RULE, 1)

    # type / code / number row
    for x, lab, val in ((LX + 24, "TYPE", "P"),
                        (LX + 110, "CODE", "TMR"),
                        (LX + 210, "PASSPORT No.", "TM4821937")):
        cv.text(x, 330, 1, lab, LABEL)
        cv.text(x, 340, 2, val, INK, bold=True)

    # portrait
    photo = portrait()
    cv.paste(photo, LX + 20, 378)
    cv.line(LX + 20, 378, LX + 170, 378, (120, 112, 92), 2)
    cv.line(LX + 20, 568, LX + 170, 568, (120, 112, 92), 2)
    cv.line(LX + 20, 378, LX + 20, 568, (120, 112, 92), 2)
    cv.line(LX + 170, 378, LX + 170, 568, (120, 112, 92), 2)
    # embossed seal overlapping the photo corner
    seal = circular_stamp_layer(54, (120, 110, 80), "REPUBLIC OF TALMAR",
                                "PORT TALMAR", "", "12 JUN 2023",
                                alpha=120, mid_star=True, arc_scale=1)
    cv.paste_rotated(seal, LX + 118 + 27, 516 + 27, -14)

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
        cv.text(fx, fy, 1, lab, LABEL)
        cv.text(fx, fy + 10, 2, val, INK, bold=True)
        cv.line(fx, fy + 28, MID - 24, fy + 28, (205, 196, 172), 1)
        fy += 32

    # issue / expiry / authority / signature
    cv.line(LX + 20, 584, MID - 24, 584, RULE, 1)
    cv.text(LX + 20, 594, 1, "DATE OF ISSUE", LABEL)
    cv.text(LX + 20, 604, 2, "12 JUN 2023", INK, bold=True)
    cv.text(LX + 210, 594, 1, "DATE OF EXPIRY", LABEL)
    cv.text(LX + 210, 604, 2, "11 JUN 2033", INK, bold=True)
    cv.text(LX + 20, 640, 1, "AUTHORITY", LABEL)
    cv.text(LX + 20, 650, 2, "PORT TALMAR", INK, bold=True)
    cv.text(LX + 20, 676, 1, "PERSONAL No.", LABEL)
    cv.text(LX + 20, 686, 2, "140388-4821", INK)
    cv.text(LX + 210, 640, 1, "HOLDER'S SIGNATURE", LABEL)
    draw_signature(cv, LX + 210, 652)
    cv.line(LX + 210, 690, MID - 24, 690, RULE, 1)
    cv.text(LX + 210, 700, 1, "HEIGHT 172 CM  \u00b7  EYES BROWN", INK_SOFT)

    # MRZ
    cv.rect(LX + 8, 752, MID - 8, 828, MRZ_BG)
    cv.line(LX + 8, 752, MID - 8, 752, (200, 192, 168), 1)
    cv.line(LX + 8, 828, MID - 8, 828, (200, 192, 168), 1)
    cv.line(LX + 8, 752, LX + 8, 828, (200, 192, 168), 1)
    cv.line(MID - 8, 752, MID - 8, 828, (200, 192, 168), 1)
    l1, l2 = mrz_lines()
    cv.text(LX + 10, 762, 2, l1, INK)
    cv.text(LX + 10, 788, 2, l2, INK)

    # ====================================================== RIGHT: visa page
    cxR = (MID + RX) // 2  # 747
    cv.text(cxR, 192, 2, "VISAS", INK_SOFT, tracking=8, anchor="ma",
            bold=True)
    cv.text(RX - 24, 192, 2, "12", INK_SOFT, anchor="ra", bold=True)
    cv.text(MID + 24, 192, 1, "VISA", LABEL)
    cv.line(MID + 24, 216, RX - 24, 216, (170, 178, 168), 1)

    # Dravian visa sticker
    draw_visa(cv, MID + 24, 236)
    fee = rect_stamp_layer(96, 26, STAMP_PURPLE,
                           [("FEE 12 ZLV", True, 3), ("PAID", True, 3)],
                           alpha=210)
    cv.paste_rotated(fee, MID + 268 + 48, 238 + 13, -10)

    # border stamps: a coherent travel history, all after issue (12 JUN 2023)
    stamps = [
        (880, 310, 96, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
         "EXIT", "01 SEP 2024", "A-14", -9),
        (800, 402, 100, STAMP_BLUE, "KINGDOM OF DRAVIA", "KORVAC",
         "ENTRY", "02 SEP 2024", "B-07", 7),
        (620, 470, 96, STAMP_BLUE, "KINGDOM OF DRAVIA", "KORVAC",
         "EXIT", "18 SEP 2024", "B-07", -6),
        (880, 482, 96, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
         "ENTRY", "19 SEP 2024", "A-14", 11),
        (610, 586, 92, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
         "EXIT", "04 MAR 2025", "A-02", 8),
        (880, 600, 100, STAMP_RED, "CORVINIA", "VELIKA",
         "ENTRY", "05 MAR 2025", "C-21", -8),
        (630, 700, 96, STAMP_RED, "CORVINIA", "VELIKA",
         "EXIT", "21 MAR 2025", "C-21", 6),
        (880, 712, 96, STAMP_GREEN, "REPUBLIC OF TALMAR", "PORT TALMAR",
         "ENTRY", "22 MAR 2025", "A-14", -12),
    ]
    for cx, cy, dia, color, top, bottom, mid, date, sub, rot in stamps:
        st = circular_stamp_layer(dia, color, top, bottom, mid, date, sub)
        cv.paste_rotated(st, cx, cy, rot)

    # endorsement: the telling paperwork detail — a harbour pilot of a
    # free port, stamped by the harbour master rather than the police.
    ex0, ey0, ex1, ey1 = MID + 24, 766, MID + 446, 822
    for (x0, y0, x1, y1) in ((ex0, ey0, ex1, ey0), (ex0, ey1, ex1, ey1),
                             (ex0, ey0, ex0, ey1), (ex1, ey0, ex1, ey1)):
        cv.line(x0, y0, x1, y1, STAMP_BLUE, 2, a=225)
    for (x0, y0, x1, y1) in ((ex0 + 3, ey0 + 3, ex1 - 3, ey0 + 3),
                             (ex0 + 3, ey1 - 3, ex1 - 3, ey1 - 3),
                             (ex0 + 3, ey0 + 3, ex0 + 3, ey1 - 3),
                             (ex1 - 3, ey0 + 3, ex1 - 3, ey1 - 3)):
        cv.line(x0, y0, x1, y1, STAMP_BLUE, 1, a=225)
    cv.text((ex0 + ex1) // 2, ey0 + 19, 1,
            "ENDORSEMENT 7 \u2014 HOLDER IS A LICENSED HARBOUR PILOT,",
            STAMP_BLUE, tracking=1, anchor="ma", a=225)
    cv.text((ex0 + ex1) // 2, ey0 + 30, 1,
            "PORT OF TALMAR. VALID FOR CREW-LIST PURPOSES ONLY.",
            STAMP_BLUE, tracking=1, anchor="ma", a=225)
    return cv


def main():
    img = build()
    os.makedirs(OUT_DIR, exist_ok=True)
    size = write_png(OUT_PATH, img)
    print(f"wrote {OUT_PATH} {W}x{H} {size} bytes")
    if size > 1048576:
        raise SystemExit("entry.png exceeds 1 MiB")


if __name__ == "__main__":
    main()
