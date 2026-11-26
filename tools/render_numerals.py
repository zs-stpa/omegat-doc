#!/usr/bin/env python3
"""Renders the numeral samples of slide 6 (NUMERALS, NUMBER_SIGNS) to
transparent lossless WebP in assets/numerals/, so the deck shows them even
where the viewer lacks fonts for Aegean, Siyaq, Mayan or Kaktovik numerals.
Fonts are free: Noto (SIL OFL) and InupiaqNumbers (MIT) for Kaktovik, fetched
once into .fonts-cache/. Needs Google Chrome, curl and cwebp.

    python3 tools/render_numerals.py

Each image is cropped to the ink of a wide, tall headless Chrome screenshot,
so glyphs that overflow their advance (Siyaq) or reach far below the line
(Javanese) are kept whole. All are rendered at one font size; the deck places
them at one common scale (make_deck.py, fit_image).

@author stephan.pakebusch at zollsoft.de
"""
import html
import struct
import os
import re
import subprocess
import sys
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from deck_content import NUMBER_SIGNS, NUMERALS  # noqa: E402

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
OUT = os.path.join(ROOT, "assets", "numerals")
CACHE = os.path.join(ROOT, ".fonts-cache")
NOTO = "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts/{0}/unhinted/ttf/{0}-Regular.ttf"
# Kaktovik is not in Noto; InupiaqNumbers puts digits 1..19 at U+E5A0.., zero at U+E5B3.
INUPIAQ = "https://raw.githubusercontent.com/0xcf843ecf802c722f434d56/InupiaqNumbers/HEAD/InupiaqNumbers.ttf"
H, SIZE, SCALE, CANVAS, PAD = 180, 64, 2, 1100, 4
FALLBACK = "'Helvetica Neue', Helvetica, 'PingFang SC', 'Apple Symbols', sans-serif"


def font_file(family):
    path = os.path.join(CACHE, family + ".ttf")
    if not os.path.isfile(path):
        os.makedirs(CACHE, exist_ok=True)
        url = INUPIAQ if family == "InupiaqNumbers" else NOTO.format(family)
        subprocess.run(["curl", "-fsSL", "-o", path, url], check=True)
    return path


def shown(text, family):
    if family != "InupiaqNumbers":
        return text
    return "".join(chr(0xE5B3) if c == "\U0001d2c0" else chr(0xE5A0 + ord(c) - 0x1D2C1)
                   if 0x1D2C1 <= ord(c) <= 0x1D2D3 else c for c in text)


def page(text, family):
    face = (f"@font-face{{font-family:'{family}';src:url('file://{font_file(family)}')}}" if family else "")
    stack = f"'{family}', {FALLBACK}" if family else FALLBACK
    return (f'<!doctype html><meta charset="utf-8"><style>{face}</style>'
            '<body style="margin:0;background:transparent">'
            f'<div style="width:{CANVAS}px;height:{H}px;display:flex;align-items:center;justify-content:center">'
            f'<span dir="auto" style="font:{SIZE}px {stack};color:#1e282c;white-space:nowrap">'
            f'{html.escape(shown(text, family))}</span></div>')


def ink_box(png):
    """Bounding box (x0, x1, y0, y1) of the pixels with any alpha in an 8-bit RGBA PNG."""
    data = open(png, "rb").read()
    pos, idat, w, h = 8, b"", 0, 0
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and ctype == 6, "expects RGBA"
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    raw, stride, prev, cols, rows = zlib.decompress(idat), w * 4, bytearray(w * 4), set(), set()
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - 4] if i >= 4 else 0
            b, c = prev[i], prev[i - 4] if i >= 4 else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        ink = [x for x in range(w) if line[x * 4 + 3]]
        cols.update(ink)
        if ink:
            rows.add(y)
        prev = line
    return min(cols), max(cols), min(rows), max(rows)


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                           "--allow-file-access-from-files", "--virtual-time-budget=3000", *args],
                          check=True, capture_output=True, text=True).stdout


os.makedirs(OUT, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    for key, text, *rest in NUMERALS + NUMBER_SIGNS:
        family = rest[-1]
        src = os.path.join(tmp, key + ".html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(page(text, family))
        png = os.path.join(tmp, key + ".png")
        chrome("--default-background-color=00000000", f"--force-device-scale-factor={SCALE}",
               f"--window-size={CANVAS},{H}", f"--screenshot={png}", "file://" + src)
        x0, x1, y0, y1 = ink_box(png)
        if y0 == 0 or y1 == H * SCALE - 1:
            sys.exit(f"{key}: glyphs touch the canvas edge, raise H")
        x0, x1 = max(0, x0 - PAD * SCALE), min(CANVAS * SCALE - 1, x1 + PAD * SCALE)
        y0, y1 = y0 - PAD * SCALE, y1 + PAD * SCALE
        subprocess.run(["cwebp", "-quiet", "-lossless", "-z", "9", "-crop", str(x0), str(y0), str(x1 - x0 + 1),
                        str(y1 - y0 + 1), png, "-o", os.path.join(OUT, key + ".webp")], check=True)
        print(key, (x1 - x0 + 1) // SCALE, (y1 - y0 + 1) // SCALE, text)
