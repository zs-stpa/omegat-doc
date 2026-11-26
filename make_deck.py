#!/usr/bin/env python3
# *************************************************************************
#  OmegaT - Computer Assisted Translation (CAT) tool
#           with fuzzy matching, translation memory, keyword search,
#           glossaries, and translation leveraging into updated projects.
#
#  Copyright (C) 2026 Stephan Pakebusch
#                Home page: https://www.omegat.org/
#                Support center: https://omegat.org/support
#
#  This file is part of OmegaT.
#
#  OmegaT is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  OmegaT is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# *************************************************************************
"""Contribution deck: German / Esperanto / English, accessible colours.

Writes dist/OmegaT-Beitraege-Sommer-2026-<version>.html: one self-contained
file without external references, small enough to send by mail. Every
slide exists in three languages; a switch on each slide (DE · EO · EN, also
keys 1/2/3) changes the language for the whole deck. Every image is embedded
once and reused by all language versions.

Colour choices hold for red-green and blue-yellow colour vision deficiency
(Okabe-Ito based, no red/green or green/blue pairs): status is always coded
by shape and text as well, before/after by symbol and word. Text contrast is
at least 4.5:1, the smallest text 13 px at 1200 px slide width.

    python3 make_deck.py [version]      (default version: dev)

Only the Python standard library is needed; all images and clips are taken
from assets/ as they are (prepared with tools/, see README).

@author stephan.pakebusch at zollsoft.de
"""
import base64
import json
import html
import os
import re
import struct
import sys

from deck_content import (AS_OF, BLOCKS, FIGURES, FOOTER, LANGS, STATUS_TEXT, UI,
                             BEFORE_AFTER, CREDITS, SLIDES)

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(HERE, "assets", "OmegaT.svg")

W, H = 1200, 700
INK = "#1e282c"
GREY = "#555f64"        # 6.4:1 on white, 5.9:1 on PANEL
PANEL = "#f4f6f7"
BORDER = "#b9c3c8"
ACCENT = "#ef3b39"       # logo red, decoration only
KICKER = "#b3261e"       # text red, 6.3:1
BLUE = "#0072B2"         # Okabe-Ito blue, 5.1:1
BLUE_BG = "#e6f1f8"
VERM = "#a84300"         # darkened Okabe-Ito vermillion, 5.6:1
VERM_BG = "#fbeee6"
SLATE = "#3d4a52"
SLATE_BG = "#eceff1"

# Status: colour + shape + word. Upstream filled circle, merge request ring,
# fork diamond.
STATUS = {"up": (BLUE, BLUE_BG, "circle"), "mr": (VERM, VERM_BG, "ring"), "fork": (SLATE, SLATE_BG, "diamond")}
KIND = {"before": (VERM, VERM_BG, "✗"), "after": (BLUE, BLUE_BG, "✓"), "now": (SLATE, SLATE_BG, "")}


# ---------------------------------------------------------------- images


def image_size(path):
    data = open(path, "rb").read()
    if path.endswith(".png"):
        return struct.unpack(">II", data[16:24])
    if path.endswith(".webp"):
        if data[12:16] == b"VP8L":
            b = int.from_bytes(data[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
        if data[12:16] == b"VP8X":
            return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1
        sys.exit(f"unsupported WebP variant: {path}")
    head = data[:4000].decode("utf-8", "replace")
    vb = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', head)
    if vb:
        return float(vb.group(1)), float(vb.group(2))
    w = re.search(r'\bwidth="([\d.]+)', head)
    h = re.search(r'\bheight="([\d.]+)', head)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    sys.exit(f"no size in {path}")


MIME = {".svg": "image/svg+xml", ".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png"}


def embeddable(path):
    """Bytes and MIME type of an asset, embedded as it is."""
    return open(path, "rb").read(), MIME[os.path.splitext(path)[1]]


class Images:
    """Each image becomes one symbol in a shared defs block, used by id."""

    def __init__(self):
        self.ids, self.defs = {}, []

    def ref(self, path):
        if path not in self.ids:
            if not os.path.isfile(path):
                sys.exit(f"image missing: {path}")
            iid = f"img{len(self.ids)}"
            w, h = image_size(path)
            data, mime = embeddable(path)
            uri = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")
            self.defs.append(f'<symbol id="{iid}" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid meet">'
                             f'<image width="{w}" height="{h}" href="{uri}"/></symbol>')
            self.ids[path] = iid
        return self.ids[path]


IMG = Images()


# ---------------------------------------------------------------- drawing


def esc(s):
    return html.escape(s, quote=True)


def text(x, y, s, size=17, fill=INK, weight="normal", anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')


def tip(svg, tooltip):
    """Native hover tooltip for a graphic element."""
    return f'<g><title>{esc(tooltip)}</title>{svg}</g>' if tooltip else svg


def fmt_int(n, lang):
    sep = {"de": ".", "eo": "\u202f", "en": ","}[lang]
    return f"{n:,}".replace(",", sep)


def fmt_bytes(n, lang):
    if n >= 1e6:
        v, unit = n / 1e6, "MB"
    else:
        v, unit = n / 1e3, "KB"
    txt = f"{v:.1f}" if v < 100 else f"{v:.0f}"
    if lang != "en":
        txt = txt.replace(".", ",")
    return f"{txt} {unit}"


def wrap(s, width):
    lines, line = [], ""
    for word in s.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return lines


def para(x, y, s, width, size=14, fill=INK, weight="normal"):
    lh = size * 1.35
    lines = wrap(s, width)
    return "".join(text(x, y + i * lh, ln, size, fill, weight) for i, ln in enumerate(lines)), len(lines) * lh


def box(x, y, w, h, fill=PANEL, stroke=BORDER, rx=8, sw=1):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def image(x, y, w, h, path, tooltip=None):
    return tip(box(x - 1, y - 1, w + 2, h + 2, "#ffffff", BORDER, 0)
               + f'<use href="#{IMG.ref(path)}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"/>', tooltip)


def shape(kind, cx, cy, color, r=6):
    if kind == "circle":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
    if kind == "ring":
        return f'<circle cx="{cx}" cy="{cy}" r="{r - 1}" fill="#ffffff" stroke="{color}" stroke-width="2.5"/>'
    if kind == "triangle":
        return f'<path d="M{cx},{cy - r - 1} L{cx + r + 1},{cy + r} L{cx - r - 1},{cy + r} z" fill="{color}"/>'
    if kind == "square":
        return f'<rect x="{cx - r + 0.5}" y="{cy - r + 0.5}" width="{2 * r - 1}" height="{2 * r - 1}" fill="{color}"/>'
    d = r + 1
    return f'<path d="M{cx},{cy - d} L{cx + d},{cy} L{cx},{cy + d} L{cx - d},{cy} z" fill="{color}"/>'


def chip(x, y, label, kind, size=13):
    fg, bg, sym = KIND[kind]
    s = f"{sym} {label}".strip()
    w = 16 + size * 0.66 * len(s)
    return (f'<rect x="{x:.1f}" y="{y - size - 3}" width="{w:.0f}" height="{size + 9}" rx="{(size + 9) / 2}" '
            f'fill="{bg}" stroke="{fg}" stroke-width="1.4"/>'
            + text(x + w / 2, y + 0.5, s, size, fg, "bold", "middle")), w


class Arrows:
    """Arrow marker with an id unique per slide and language."""

    def __init__(self, uid):
        self.uid = uid

    def defs(self):
        return (f'<defs><marker id="ar-{self.uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{GREY}"/></marker></defs>')

    def __call__(self, x1, y1, x2, y2):
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{GREY}" stroke-width="2" '
                f'marker-end="url(#ar-{self.uid})"/>')


def legend(x, y, lang):
    out, cx = [], x
    for key in ("up", "mr", "fork"):
        color, _, kind = STATUS[key]
        desc = STATUS_TEXT[key][lang]
        out.append(shape(kind, cx + 6, y - 5, color) + text(cx + 18, y, desc, 13.5, GREY))
        cx += 18 + 7.2 * len(desc) + 28
    return "".join(out)


def counts(items, lang):
    n = {k: sum(1 for it in items if it[-1] == k) for k in ("up", "mr", "fork")}
    return " · ".join(f"{n[k]} {UI['count_' + k][lang]}" for k in ("up", "mr", "fork") if n[k])


def frame(page, total, lang, title, body, block=None, arrows=None):
    kicker = text(86, 24, f"{UI['block'][lang]} {block}", 13, KICKER, "bold") if block else ""
    head = (f'<use href="#{IMG.ref(LOGO_PATH)}" x="24" y="12" width="50" height="50"/>'
            + kicker + text(86, 56, title, 28, INK, "bold")
            + f'<rect x="36" y="72" width="{W - 72}" height="2" fill="{ACCENT}"/>')
    footer = (text(36, H - 16, f"{FOOTER[lang]} · {AS_OF[lang]}", 13, GREY)
              + text(W - 36, H - 16, f"{page} / {total}", 13, GREY, anchor="end"))
    return (f'<svg class="l-{lang}" lang="{lang}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Helvetica, Arial, sans-serif" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title>{arrows.defs() if arrows else ""}'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>{head}{body}'
            f'<line x1="36" y1="{H - 38}" x2="{W - 36}" y2="{H - 38}" stroke="{BORDER}"/>{footer}</svg>')


def takeaway(s, right=""):
    return (box(36, H - 92, W - 72, 42, INK, INK)
            + text(56, H - 65, s, 17, "#ffffff", "bold")
            + (text(W - 56, H - 65, right, 14, "#e3e8ea", anchor="end") if right else ""))


# ---------------------------------------------------------------- slide types


def overview(page, total, lang, spec):
    body = []
    gap, top = 18, 96
    bw = (W - 72 - gap * (len(FIGURES) - 1)) / len(FIGURES)
    for i, (num, label, sub, key, ftip) in enumerate(FIGURES):
        x = 36 + i * (bw + gap)
        body.append(f'<g><title>{esc(ftip[lang])}</title>')
        color = {"up": BLUE, "mr": VERM, "fork": SLATE, "all": INK}[key]
        body.append(box(x, top, bw, 124, PANEL, BORDER, 10)
                    + f'<rect x="{x:.1f}" y="{top}" width="6" height="124" rx="3" fill="{color}"/>')
        if key in STATUS:
            body.append(shape(STATUS[key][2], x + bw - 22, top + 22, color, 7))
        body.append(text(x + 22, top + 56, num, 48, color, "bold"))
        body.append(text(x + 22, top + 86, label[lang], 16.5, INK, "bold"))
        body.append(text(x + 22, top + 108, sub[lang], 13, GREY))
        body.append("</g>")
    y0 = 262
    body.append(text(36, y0, UI["six_blocks"][lang], 20, INK, "bold"))
    body.append(text(560, y0, UI["share_up"][lang], 13.5, GREY))
    for i, (key, title, lead, items) in enumerate(BLOCKS):
        y = y0 + 40 + i * 50
        up = sum(1 for it in items if it[-1] == "up")
        body.append(f'<g><title>{esc(title[lang] + ": " + counts(items, lang) + " – " + lead[lang])}</title>')
        body.append(text(36, y, key, 22, KICKER, "bold"))
        body.append(text(66, y, title[lang], 18, INK, "bold"))
        body.append(text(66, y + 20, f"{UI['slides'][lang]} {spec[key]} · {len(items)} {UI['entries'][lang]}", 13, GREY))
        bx, bwid = 560, 400
        body.append(f'<rect x="{bx}" y="{y - 13}" width="{bwid}" height="16" rx="3" fill="#ffffff" stroke="{GREY}"/>')
        if up:
            body.append(f'<rect x="{bx}" y="{y - 13}" width="{bwid * up / len(items):.1f}" height="16" rx="3" fill="{BLUE}"/>')
        body.append(text(bx + bwid + 14, y, counts(items, lang), 13, GREY))
        body.append("</g>")
    body.append(legend(36, H - 54, lang))
    return frame(page, total, lang, UI["deck_title"][lang], "".join(body))


def dense(page, total, lang, block):
    key, title, lead, items = block
    body = []
    p, hh = para(36, 104, lead[lang], 118, 17, GREY)
    body.append(p)
    top = 104 + hh + 8
    cols = 3
    rows = -(-len(items) // cols)
    step = min(64, ((H - 102) - top) / rows)
    cw = (W - 72 - 40) / cols
    for i, (t, d, st) in enumerate(items):
        c, r = divmod(i, rows)
        x, y = 36 + c * (cw + 20), top + r * step
        color, _, kind = STATUS[st]
        bh = step - 6
        g = [box(x, y, cw, bh, PANEL, BORDER, 6),
             f'<rect x="{x}" y="{y}" width="4" height="{bh:.1f}" rx="2" fill="{color}"/>',
             shape(kind, x + cw - 16, y + 16, color, 5.5)]
        if d[lang] and bh >= 38:
            g += [text(x + 14, y + 19, t[lang], 14, INK, "bold"), text(x + 14, y + 36, d[lang], 13, GREY)]
        else:
            g.append(text(x + 14, y + bh / 2 + 5, t[lang], 14, INK, "bold"))
        body.append(tip("".join(g), " — ".join(v for v in (t[lang], d[lang]) if v) + " · " + STATUS_TEXT[st][lang]))
    body.append(box(36, H - 92, W - 72, 42, INK, INK) + legend_dark(56, H - 65, lang, {it[-1] for it in items})
                + text(W - 56, H - 65, counts(items, lang), 14, "#e3e8ea", anchor="end"))
    return frame(page, total, lang, title[lang], "".join(body), key)


def legend_dark(x, y, lang, keys=("up", "mr", "fork")):
    light = {"up": "#7cc4f0", "mr": "#f2a66b", "fork": "#d0d6d9"}
    out, cx = [], x
    for key in [k for k in ("up", "mr", "fork") if k in keys]:
        kind = STATUS[key][2]
        desc = STATUS_TEXT[key][lang]
        out.append(shape(kind, cx + 6, y - 5, light[key]) + text(cx + 18, y, desc, 14, "#ffffff", "bold"))
        cx += 18 + 7.8 * len(desc) + 26
    return "".join(out)


def notes_column(x, y, w, notes, lang, size=14, numbered=True):
    out, cy = [], y
    ind = 32 if numbered else 14
    for i, (head, body) in enumerate(notes):
        if numbered:
            out.append(f'<circle cx="{x + 12}" cy="{cy - 5}" r="12" fill="{INK}"/>'
                       + text(x + 12, cy, str(i + 1), 13, "#ffffff", "bold", "middle"))
        else:
            out.append(f'<rect x="{x}" y="{cy - 16}" width="4" height="{size * 1.45 + 6:.0f}" rx="2" fill="{INK}"/>')
        out.append(text(x + ind, cy, head[lang], size + 1, INK, "bold"))
        p, hh = para(x + ind, cy + size * 1.45, body[lang], int((w - ind) / (size * 0.5)), size, GREY)
        out.append(p)
        cy += size * 1.45 + hh + 16
    return "".join(out)


def image_slide(page, total, lang, s):
    top = 92
    body = []
    if s.get("lead"):
        p, hh = para(36, 110, s["lead"][lang], 124, 16, GREY)
        body.append(p)
        top = 110 + hh
    iw = s.get("img_w", 730)
    body.append(image(36, top, iw, H - 104 - top, s["img"], s["title"][lang]))
    body.append(notes_column(36 + iw + 26, top + 18, W - 72 - iw - 26, s["notes"], lang, numbered=s.get("numbered", True)))
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"])


def pair_slide(page, total, lang, s):
    top = 92
    body = []
    if s.get("lead"):
        p, hh = para(36, 110, s["lead"][lang], 124, 16, GREY)
        body.append(p)
        top = 110 + hh
        if any(img.endswith(".mp4") for _, _, img, _ in s["pair"]):
            # one video element serves all languages: same box in each
            top = 110 + max(len(wrap(s["lead"][l], 124)) for l in LANGS) * 16 * 1.35
    w = (W - 72 - 20) / 2
    for i, (label, kind, img, cap) in enumerate(s["pair"]):
        x = 36 + i * (w + 20)
        c, cw = chip(x, top + 20, label[lang], kind)
        body.append(c + text(x + cw + 10, top + 20, cap[lang], 14, GREY))
        ih = H - 104 - top - 34
        if img.endswith(".mp4"):
            body.append(box(x - 1, top + 31, w + 2, ih + 2, "#ffffff", BORDER, 0))
            s.setdefault("_videos", [])
            s["_videos"] = [v for v in s["_videos"] if v[0] != img] + [(img, x, top + 32, w, ih, cap)]
        else:
            body.append(image(x, top + 32, w, ih, img, f"{label[lang]}: {cap[lang]}"))
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"])


def flow_box(x, y, w, h, head, lines, kind="now", size=14):
    fg, bg, _ = KIND[kind]
    out = box(x, y, w, h, bg, fg, 8, 1.4) + text(x + 12, y + 23, head, size + 1.5, fg, "bold")
    for i, ln in enumerate(lines):
        out += text(x + 12, y + 45 + i * (size + 5), ln, size, INK)
    return out


def shortcuts_slide(page, total, lang, s):
    ar = Arrows(f"p{page}{lang}")
    t = s["text"]
    body = [para(36, 110, s["lead"][lang], 126, 16, GREY)[0]]
    y = 176
    body.append(chip(36, y, BEFORE_AFTER["before"][lang], "before")[0])
    b = t["before"]
    body.append(flow_box(36, y + 14, 250, 96, b[0][0][lang], [ln[lang] for ln in b[0][1]], "now"))
    body.append(ar(290, y + 62, 340, y + 62))
    body.append(flow_box(344, y + 14, 290, 96, b[1][0][lang], [ln[lang] for ln in b[1][1]], "before"))
    body.append(ar(638, y + 62, 688, y + 62))
    body.append(flow_box(692, y + 14, 472, 96, b[2][0][lang], [ln[lang] for ln in b[2][1]], "before"))
    y = 336
    body.append(chip(36, y, BEFORE_AFTER["after"][lang], "after")[0])
    a = t["after"]
    for i, (x, w) in enumerate(((36, 250), (344, 290), (692, 472))):
        body.append(flow_box(x, y + 14, w, 124, a[i][0][lang], [ln[lang] for ln in a[i][1]], "after"))
        if i < 2:
            body.append(ar(x + w + 4, y + 76, x + w + 54, y + 76))
    body.append(text(36, 516, t["feat_head"][lang], 16, INK, "bold"))
    for i, f in enumerate(t["features"]):
        c, r = divmod(i, 2)
        body.append(text(36 + c * 380, 545 + r * 23, "• " + f[lang], 14.5, INK))
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"], ar)


def config_slide(page, total, lang, s):
    ar = Arrows(f"p{page}{lang}")
    body = [para(36, 110, s["lead"][lang], 126, 16, GREY)[0]]
    cw = (W - 72 - 3 * 16) / 4
    y = 182
    for i, (head, before, after) in enumerate(s["cols"]):
        x = 36 + i * (cw + 16)
        body.append(box(x, y, cw, 46, INK, INK, 8) + text(x + 12, y + 29, head[lang], 14.5, "#ffffff", "bold"))
        body.append(box(x, y + 58, cw, 132, VERM_BG, VERM, 8, 1.4))
        body.append(chip(x + 10, y + 84, BEFORE_AFTER["before"][lang], "before", 12)[0])
        body.append(para(x + 12, y + 112, before[lang], 33, 14, INK)[0])
        body.append(ar(x + cw / 2, y + 194, x + cw / 2, y + 222))
        body.append(box(x, y + 226, cw, 160, BLUE_BG, BLUE, 8, 1.4))
        body.append(chip(x + 10, y + 252, BEFORE_AFTER["after"][lang], "after", 12)[0])
        body.append(para(x + 12, y + 280, after[lang], 33, 14, INK)[0])
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"], ar)


def pipeline_slide(page, total, lang, s):
    ar = Arrows(f"p{page}{lang}")
    b = s["boxes"]
    L = lambda k: (b[k][0][lang], [ln[lang] for ln in b[k][1]])  # noqa: E731
    body = [para(36, 110, s["lead"][lang], 126, 16, GREY)[0]]
    y = 182
    body.append(flow_box(36, y, 200, 112, *L("branches"), "now"))
    body.append(ar(240, y + 56, 280, y + 56))
    body.append(flow_box(284, y, 230, 112, *L("integration"), "after"))
    body.append(ar(518, y + 36, 560, y + 18))
    body.append(ar(518, y + 76, 560, y + 130))
    body.append(flow_box(564, y - 30, 270, 92, *L("house"), "now"))
    body.append(flow_box(564, y + 88, 270, 122, *L("build"), "after"))
    body.append(ar(838, y + 150, 878, y + 150))
    body.append(flow_box(882, y + 88, 282, 122, *L("publisher"), "after"))
    body.append(ar(1023, y + 214, 1023, y + 250))
    sx, sy, sw = 36, y + 254, (W - 72 - 4 * 14) / 5
    for i, (h, sub) in enumerate(s["steps"]):
        x = sx + i * (sw + 14)
        body.append(box(x, sy, sw, 64, BLUE_BG, BLUE, 8, 1.4)
                    + text(x + 12, sy + 26, f"{i + 1}. {h[lang]}", 15, BLUE, "bold") + text(x + 12, sy + 48, sub[lang], 13.5, INK))
        if i < 4:
            body.append(ar(x + sw + 1, sy + 32, x + sw + 13, sy + 32))
    body.append(text(36, sy + 100, s["note"][lang], 14, GREY))
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"], ar)


def docs_slide(page, total, lang, block, thumbs):
    key, title, lead, items = block
    body = [para(36, 104, lead[lang], 118, 17, GREY)[0]]
    top = 132
    cols, rows = 3, -(-len(items) // 3)
    cw = (W - 72 - 40) / 3
    step = 44
    for i, (t, d, st) in enumerate(items):
        c, r = divmod(i, rows)
        x, y = 36 + c * (cw + 20), top + r * step
        color, _, kind = STATUS[st]
        g = (box(x, y, cw, step - 6, PANEL, BORDER, 6) + f'<rect x="{x}" y="{y}" width="4" height="{step - 6}" rx="2" fill="{color}"/>'
             + shape(kind, x + cw - 16, y + 14, color, 5.5) + text(x + 14, y + 17, t[lang], 14, INK, "bold")
             + (text(x + 14, y + 33, d[lang], 13, GREY) if d[lang] else ""))
        body.append(tip(g, " — ".join(v for v in (t[lang], d[lang]) if v) + " · " + STATUS_TEXT[st][lang]))
    ty = top + rows * step + 8
    th = H - 104 - ty - 22
    for i, (img, cap) in enumerate(thumbs):
        x = 36 + i * (cw + 20)
        body.append(image(x, ty, cw, th, img, cap[lang]) + text(x, ty + th + 17, cap[lang], 13, GREY))
    body.append(box(36, H - 92, W - 72, 42, INK, INK) + legend_dark(56, H - 65, lang, {it[-1] for it in items})
                + text(W - 56, H - 65, counts(items, lang), 14, "#e3e8ea", anchor="end"))
    return frame(page, total, lang, title[lang], "".join(body), key)


def video_slide(page, total, lang, s):
    """Frames and captions in SVG; the clips themselves are HTML video
    elements laid over the frames (positions kept in s["_videos"])."""
    top = 92
    body = []
    if s.get("lead"):
        p, hh = para(36, 110, s["lead"][lang], 124, 16, GREY)
        body.append(p)
        top = 110 + hh
    clips = s["clips"]
    boxes = []
    if s.get("notes"):
        vw = s.get("video_w", 730)
        vh = vw / s["video_aspect"] if s.get("video_aspect") else H - 104 - top - 40
        boxes.append((36, top + 6, vw, vh))
        body.append(notes_column(36 + vw + 26, top + 24, W - 72 - vw - 26, s["notes"], lang, numbered=False))
    else:
        vw = (W - 72 - 20) / len(clips)
        boxes = [(36 + i * (vw + 20), top + 34, vw, H - 104 - top - 76) for i in range(len(clips))]
    for (x, y, w, h), (path, chip_l, cap) in zip(boxes, clips):
        if chip_l:
            body.append(chip(x, y - 10, chip_l[lang], "now", 12.5)[0])
        body.append(box(x - 1, y - 1, w + 2, h + 2, "#ffffff", BORDER, 0))
        body.append(text(x, y + h + 22, "▶ " + cap[lang], 14, GREY))
    s["_videos"] = [(path, x, y, w, h, cap) for (x, y, w, h), (path, _, cap) in zip(boxes, clips)]
    if s.get("numerals"):
        body.append(numeral_strip(boxes[0][1] + boxes[0][3] + 44, lang, s))
    else:
        body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"])


def fit_image(path, x, y, w, h, k=None):
    """The image scaled by k (image px to slide px), shrunk to fit the box
    (w, h) where needed, aspect kept, centred."""
    iw, ih = image_size(path)
    k = min(k or float("inf"), w / iw, h / ih)
    dw, dh = iw * k, ih * k
    return (f'<use href="#{IMG.ref(path)}" x="{x + (w - dw) / 2:.1f}" y="{y + (h - dh) / 2:.1f}" '
            f'width="{dw:.1f}" height="{dh:.1f}"/>')


def label(x, y, s, size, width, fill=GREY):
    """Centred label, squeezed to width when it would not fit."""
    fit = f' textLength="{width:.1f}" lengthAdjust="spacingAndGlyphs"' if len(s) * size * 0.56 > width else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="middle"{fit}>'
            f'{esc(s)}</text>')


def numeral_strip(y, lang, s):
    """Head line, one tile per 2345 sample (rendered glyphs from assets/numerals,
    no font needed, over the script name), then a row of single number-like
    signs; text, value and explanation in the tooltips."""
    num_dir = os.path.join(HERE, "assets", "numerals")
    head, hh = para(36, y, s["numerals_head"][lang], 150, 13.5, INK, "bold")
    out = [head]
    nums, signs = s["numerals"], s["number_signs"]
    cols, gap, vgap = 12, 6, 5
    rows = -(-len(nums) // cols)
    cw = (W - 72 - (cols - 1) * gap) / cols
    top = y + hh - 13.5 * 1.35 + 8
    sh = 40
    sy = H - 46 - sh
    th = (sy - 8 - top - (rows - 1) * vgap) / rows
    # one scale for all glyphs: Latin "2345" fills the image area
    k = (th - 21) / image_size(os.path.join(num_dir, "latn.webp"))[1]
    for i, (key, txt, name, how, _font) in enumerate(nums):
        r, c = divmod(i, cols)
        x, ty = 36 + c * (cw + gap), top + r * (th + vgap)
        g = (box(x, ty, cw, th, PANEL, BORDER, 6)
             + fit_image(os.path.join(num_dir, key + ".webp"), x + 4, ty + 3, cw - 8, th - 21, k)
             + label(x + cw / 2, ty + th - 5, name[lang], 13, cw - 6))
        out.append(tip(g, f"{name[lang]}: {txt} – {how[lang]}"))
    lead, lw = s["signs_head"][lang], 150
    out.append(para(36, sy + 15, lead, 22, 13, INK, "bold")[0])
    sx, sw = 36 + lw, (W - 36 - 36 - lw) / len(signs)
    ks = (sh - 16) / image_size(os.path.join(num_dir, "s-mbold.webp"))[1]
    for i, (key, txt, val, name, _font) in enumerate(signs):
        x = sx + i * sw
        g = (fit_image(os.path.join(num_dir, key + ".webp"), x + 2, sy, sw - 4, sh - 16, ks)
             + label(x + sw / 2, sy + sh - 2, val, 13, sw - 4))
        out.append(tip(g, f"{name[lang]}: {txt} = {val}"))
    return "".join(out)


def link_row(x, y, links, lang):
    """Clickable link chips (open in a new tab); returns (svg, right edge)."""
    out = []
    for label, url in links:
        lab = label[lang]
        href = url[lang] if isinstance(url, dict) else url
        w = len(lab) * 7.6 + 38
        out.append(f'<a href="{esc(href)}" target="_blank" rel="noopener">'
                   + tip(box(x, y, w, 28, BLUE_BG, BLUE, 14)
                         + text(x + 14, y + 19, lab + " ↗", 14, BLUE, "bold"), href) + "</a>")
        x += w + 10
    return "".join(out), x - 10


def credits_slide(page, total, lang, s):
    """Slide 0: maintainers, previous and current team, all code contributors,
    everyone else, and the employer."""
    c = CREDITS
    body = [text(36, 106, c["maint_head"][lang], 15, INK, "bold")]
    cw = (W - 72 - 18) / 2
    for i, (name, role) in enumerate(c["maintainers"]):
        x = 36 + i * (cw + 18)
        body.append(tip(box(x, 116, cw, 66, PANEL, BORDER, 8)
                        + f'<rect x="{x:.1f}" y="116" width="5" height="66" rx="2" fill="{BLUE}"/>'
                        + text(x + 22, 146, name, 22, BLUE, "bold") + text(x + 22, 170, role[lang], 14, GREY),
                        f"{name} – {role[lang]}"))

    def people(x, y, head, items, cols, colw):
        out = [text(x, y, head, 15, INK, "bold")]
        for i, (name, role) in enumerate(items):
            r, k = divmod(i, cols)
            ny = y + 24 + r * 20
            line = (f'<text x="{x + k * colw:.1f}" y="{ny:.1f}" font-size="13.5" fill="{INK}">'
                    f'<tspan font-weight="bold">{esc(name)}</tspan>'
                    + (f'<tspan fill="{GREY}"> · {esc(role[lang])}</tspan>' if role else "") + '</text>')
            out.append(tip(line, f"{name} – {role[lang]}" if role else name))
        return "".join(out)

    body.append(people(36, 214, c["past_head"][lang], c["past"], 3, 260))
    body.append(people(36 + 3 * 260 + 12, 214, c["team_head"][lang], c["team"], 1, 340))
    cy = 214 + 24 + 5 * 20 + 18
    names = c["contributors"]
    body.append(text(36, cy, f'{c["contrib_head"][lang]} ({len(names)})', 15, INK, "bold"))
    lines, line = [], ""
    for n in names:
        part = n if not line else line + " · " + n
        if len(part) * 13.5 * 0.5 > W - 72 and line:
            lines.append(line)
            line = n
        else:
            line = part
    lines.append(line)
    for i, ln in enumerate(lines):
        body.append(text(36, cy + 22 + i * 19, ln, 13.5, GREY))
    ry = cy + 22 + len(lines) * 19 + 8
    body.append(para(36, ry, c["rest"][lang], 150, 14, INK)[0])
    fy = ry + 30
    fb, fh = para(36, fy, c["feedback"][lang], 150, 14, INK, "bold")
    body.append(fb)
    ly = min(fy + fh - 6, H - 92 - 28 - 10)
    x = link_row(36, ly, c["sf_links"], lang)
    body.append(x[0])
    body.append(text(x[1] + 24, ly + 19, c["doc_head"][lang], 14, INK, "bold"))
    body.append(link_row(x[1] + 24 + 7.6 * len(c["doc_head"][lang]) + 8, ly, c["doc_links"], lang)[0])
    body.append(takeaway(c["sponsor"][lang]))
    return frame(page, total, lang, c["title"][lang], "".join(body))


def research_slide(page, total, lang, s):
    body = []
    lx, lw = 36, 556
    body.append(text(lx, 112, s["left_head"][lang], 19, INK, "bold"))
    body.append(text(lx, 134, s["left_sub"][lang], 13.5, GREY))
    tw, th = (lw - 12) / 2, 74
    for i, (num, lab) in enumerate(s["stats"]):
        x, y = lx + (i % 2) * (tw + 12), 152 + (i // 2) * (th + 12)
        body.append(box(x, y, tw, th, PANEL, BORDER, 8) + f'<rect x="{x:.1f}" y="{y}" width="5" height="{th}" rx="2" fill="{BLUE}"/>')
        body.append(text(x + 18, y + 36, num[lang], 26, BLUE, "bold"))
        body.append(text(x + 18, y + 60, lab[lang], 13.5, INK))
        body[-3] = '<g><title>' + esc(num[lang] + " " + lab[lang] + " – " + s["left_sub"][lang]) + '</title>' + body[-4]
        body[-1] += "</g>"
    cy = 152 + 2 * (th + 12) + 18
    for head, txt in s["bullets"]:
        body.append(text(lx, cy, head[lang], 15, INK, "bold"))
        p, hh = para(lx, cy + 20, txt[lang], 74, 14, GREY)
        body.append(p)
        cy += 20 + hh + 10
    rx = 616
    rw = W - 36 - rx
    body.append(text(rx, 112, s["right_head"][lang], 19, INK, "bold"))
    body.append(text(rx, 134, s["right_sub"][lang], 13.5, GREY))
    ih = 300
    body.append(image(rx, 150, rw, ih, s["img"], s["right_head"][lang]))
    cy = 150 + ih + 30
    for line in s["map_facts"]:
        body.append(f'<rect x="{rx}" y="{cy - 13}" width="4" height="18" rx="2" fill="{INK}"/>' + text(rx + 14, cy, line[lang], 14.5, INK))
        cy += 26
    body.append(f'<line x1="{rx - 12}" y1="100" x2="{rx - 12}" y2="{H - 104}" stroke="{BORDER}"/>')
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"])


def langpack_slide(page, total, lang, s):
    stats = {r["language"]: r for r in json.load(open(s["stats"], encoding="utf-8"))}
    T = s["tip"]
    body = [para(36, 106, s["lead"][lang], 124, 15.5, GREY)[0]]
    langs = s["langs"]
    cols, gap = 5, 10
    rows = -(-len(langs) // cols)
    top, step = 146, 41
    cw = (W - 72 - (cols - 1) * gap) / cols
    for i, (code, name) in enumerate(langs):
        c, r = divmod(i, rows)
        x, y = 36 + c * (cw + gap), top + r * step
        st = stats[code]
        lines = [f"{name[lang]} ({code}) · {T['source'][lang]}: {st['collection']} {st['version']} · {T['licence'][lang]}: {st['license']}"]
        for pr in st["pairs"]:
            forms = fmt_int(pr["forms"], lang) if pr["forms"] is not None else T["forms_na"][lang]
            lines.append(f"{pr['stem']}: {fmt_int(pr['entries'], lang)} {T['entries'][lang]} · {forms} {T['forms'][lang]}"
                         f" · {T['dic'][lang]} {fmt_bytes(pr['dic_bytes'], lang)} + {T['aff'][lang]} {fmt_bytes(pr['aff_bytes'], lang)}")
        lines.append(f"{T['jar'][lang]}: {fmt_bytes(st['jar_bytes'], lang)} · {T['locales'][lang]}: {', '.join(st['locales'])}")
        entries = sum(pr["entries"] for pr in st["pairs"][:1])
        g = (box(x, y, cw, step - 6, PANEL, BORDER, 6)
             + shape("circle", x + 12, y + (step - 6) / 2, BLUE, 4.5)
             + text(x + 24, y + (step - 6) / 2 + 5.5, code, 14.5, BLUE, "bold")
             + text(x + 62, y + (step - 6) / 2 + 5, name[lang], 13.5, INK)
             + text(x + cw - 8, y + (step - 6) / 2 + 5, (fmt_int(round(entries / 1000), lang) if entries >= 1000
                    else f"{entries / 1000:.1f}".replace(".", "," if lang != "en" else ".")) + "k", 12.5, GREY, anchor="end"))
        body.append(tip(g, "\n".join(lines)))
    ty = top + rows * step + 34
    body.append(text(36, ty + 4, s["tok_head"][lang], 15, INK, "bold"))
    tw = (W - 72 - 2 * gap - 330) / 3
    for i, (code, name, detail) in enumerate(s["tokenizers"]):
        x, y = 36 + 330 + i * (tw + gap), ty - 18
        g = (f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="34" rx="6" fill="{SLATE_BG}" stroke="{SLATE}" stroke-dasharray="5 3"/>'
             + shape("diamond", x + 12, y + 17, SLATE, 4.5)
             + text(x + 24, y + 22.5, code, 14.5, SLATE, "bold") + text(x + 62, y + 22, name[lang], 14, INK))
        body.append(tip(g, f"{name[lang]} ({code}) – {detail[lang]}"))
    body.append(text(W - 36, ty + 34, s["legend"][lang], 12.5, GREY, anchor="end"))
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"])


def timeline_slide(page, total, lang, s):
    """Size per date, points only. Broken time axis: an early panel for old
    releases, then the main range; events as rotated labels at the axis."""
    import datetime as dt
    D = dt.date.fromisoformat
    d0, d1 = D(s["main_from"]), D(s["main_to"])
    y0, y1 = s["y_range"]
    px0, px1, py0, py1 = 96, W - 50, H - 150, 160
    early = s["early_dates"]
    ex = {d: px0 + 30 + i * 60 for i, d in enumerate(early)}
    mx0 = px0 + 30 + len(early) * 60 + 10
    X = lambda d: ex[d] if d in ex else mx0 + (D(d) - d0).days / (d1 - d0).days * (px1 - mx0)  # noqa: E731
    Y = lambda v: py0 - (v - y0) / (y1 - y0) * (py0 - py1)  # noqa: E731
    fmt_d = lambda d: (f"{D(d):%d.%m.%Y}" if lang == "de" else d)  # noqa: E731
    num = lambda v: f"{v:.1f}".replace(".", "," if lang != "en" else ".")  # noqa: E731
    body = [para(36, 104, s["lead"][lang], 124, 15, GREY)[0]]
    for v in range(y0, y1 + 1, s["y_step"]):
        body.append(f'<line x1="{px0}" y1="{Y(v):.1f}" x2="{px1}" y2="{Y(v):.1f}" stroke="#e3e8ea"/>'
                    + text(px0 - 10, Y(v) + 4.5, str(v), 13, GREY, anchor="end"))
    body.append(text(36, py1 - 14, "MB", 13, GREY))
    bx = mx0 - 18
    body.append(f'<rect x="{px0}" y="{py1}" width="{bx - px0 - 6}" height="{py0 - py1}" fill="#f7f9fa"/>'
                f'<line x1="{px0}" y1="{py0}" x2="{bx - 4}" y2="{py0}" stroke="{GREY}"/>'
                f'<line x1="{bx + 4}" y1="{py0}" x2="{px1}" y2="{py0}" stroke="{GREY}"/>'
                f'<path d="M{bx - 8},{py0 + 6} L{bx},{py0 - 6} M{bx},{py0 + 6} L{bx + 8},{py0 - 6}" stroke="{GREY}" stroke-width="1.5"/>')
    for d in early:
        body.append(text(ex[d], py0 + 20, D(d).strftime("%Y"), 13, GREY, anchor="middle"))
    m = dt.date(d0.year, d0.month, 1)
    while m <= d1:
        if m >= d0:
            body.append(f'<line x1="{X(m.isoformat()):.1f}" y1="{py1}" x2="{X(m.isoformat()):.1f}" y2="{py0}" stroke="#eef1f2"/>'
                        + text(X(m.isoformat()), py0 + 20, s["months"][lang][m.month - 1], 13, GREY, anchor="middle"))
        m = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    for date, label in s["events"]:
        x = X(date)
        lab = f"{fmt_d(date)} · {label[lang]}"
        body.append(tip(f'<line x1="{x:.1f}" y1="{py1}" x2="{x:.1f}" y2="{py0}" stroke="{SLATE}" stroke-dasharray="3 3"/>'
                        f'<text x="{x - 5:.1f}" y="{py0 - 6}" font-size="12.5" fill="{SLATE}" '
                        f'transform="rotate(-90 {x - 5:.1f} {py0 - 6})" paint-order="stroke" stroke="#ffffff" '
                        f'stroke-width="3">{esc(lab)}</text>', lab))
    for key, color, kind, pts, name in s["series"]:
        for d, v, note in pts:
            a, b = X(d), Y(v)
            halo = f'font-size="13.5" font-weight="bold" fill="{color}" paint-order="stroke" stroke="#ffffff" stroke-width="3.5"'
            if key == "release":
                label = (f'<text x="{a:.1f}" y="{b + 24:.1f}" text-anchor="middle" {halo}>{esc(note[lang])}</text>'
                         f'<text x="{a:.1f}" y="{b + 40:.1f}" text-anchor="middle" {halo}>{esc(num(v))}</text>')
            else:
                label = f'<text x="{a + 10:.1f}" y="{b - 9:.1f}" {halo}>{esc(num(v))}</text>'
            body.append(tip(shape(kind, round(a, 1), round(b, 1), color, 7) + label,
                            f"{fmt_d(d)}: {num(v)} MB – {name[lang]}" + (f" – {note[lang]}" if note else "")))
    lx = px0
    for key, color, kind, pts, name in s["series"]:
        body.append(shape(kind, lx + 7, H - 106, color, 6) + text(lx + 20, H - 101, name[lang], 13.5, INK))
        lx += 34 + 7.2 * len(name[lang])
    body.append(takeaway(s["take"][lang]))
    return frame(page, total, lang, s["title"][lang], "".join(body), s["block"])


def video_html(s):
    out = []
    for path, x, y, w, h, cap in s.get("_videos", []):
        if not os.path.isfile(path):
            sys.exit(f"clip missing: {path}")
        src = "data:video/mp4;base64," + base64.b64encode(open(path, "rb").read()).decode("ascii")
        poster = path[:-4] + "-poster.jpg"
        pst = ("data:image/jpeg;base64," + base64.b64encode(open(poster, "rb").read()).decode("ascii")) if os.path.isfile(poster) else ""
        labels = " ".join(f'data-label-{l}="{esc(cap[l])}"' for l in LANGS)
        out.append(f'<video class="clip" controls muted loop playsinline preload="metadata" poster="{pst}" {labels} '
                   f'style="left:{x / W * 100:.3f}%;top:{y / H * 100:.3f}%;width:{w / W * 100:.3f}%;height:{h / H * 100:.3f}%">'
                   f'<source src="{src}" type="video/mp4"></video>')
    return "".join(out)


# ---------------------------------------------------------------- deck


def render(spec, page, total, lang, blocks):
    kind = spec["type"]
    if kind == "overview":
        return overview(page, total, lang, spec["pages"])
    if kind == "dense":
        return dense(page, total, lang, blocks[spec["block"]])
    if kind == "docs":
        return docs_slide(page, total, lang, blocks[spec["block"]], spec["thumbs"])
    return {"image": image_slide, "pair": pair_slide, "shortcuts": shortcuts_slide,
            "config": config_slide, "pipeline": pipeline_slide, "video": video_slide,
            "research": research_slide, "credits": credits_slide, "langpack": langpack_slide, "timeline": timeline_slide}[kind](page, total, lang, spec)


def build():
    blocks = {b[0]: b for b in BLOCKS}
    base = 0 if SLIDES[0]["type"] == "credits" else 1  # credits count as slide 0
    total = len(SLIDES) - 1 + base
    sections = []
    for i, spec in enumerate(SLIDES):
        page = i + base
        svgs = "".join(render(spec, page, total, lang, blocks) for lang in LANGS)
        buttons = "".join(f'<button type="button" data-lang="{l}" lang="{l}" aria-label="{UI["lang_name"][l]}">{l.upper()}</button>'
                          for l in LANGS)
        sections.append(f'<section class="slide" id="s{page}"><div class="stage">{svgs}{video_html(spec)}'
                        f'<nav class="langs" aria-label="Sprache / Lingvo / Language">{buttons}</nav></div></section>')
    defs = (f'<svg class="defs" aria-hidden="true" width="0" height="0" xmlns="http://www.w3.org/2000/svg">'
            f'<defs>{"".join(IMG.defs)}</defs></svg>')
    page = TEMPLATE.replace("@DEFS@", defs).replace("@SECTIONS@", "\n".join(sections)) \
        .replace("@BASE@", str(base)).replace("@W@", str(W)).replace("@H@", str(H))
    version = sys.argv[1] if len(sys.argv) > 1 else "dev"
    os.makedirs(os.path.join(HERE, "dist"), exist_ok=True)
    out = os.path.join(HERE, "dist", f"OmegaT-Beitraege-Sommer-2026-{version}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"{out}: {total} Folien × {len(LANGS)} Sprachen, {os.path.getsize(out) / 1e6:.1f} MB")


TEMPLATE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beiträge seit Sommer 2026 · Kontribuoj ekde somero 2026 · Contributions since summer 2026</title>
<style>
  html, body { margin: 0; height: 100%; background: #2a3236; overflow: hidden; }
  .defs { position: absolute; width: 0; height: 0; overflow: hidden; }
  .slide { display: none; position: absolute; inset: 0; align-items: center; justify-content: center; }
  .slide.on { display: flex; }
  .stage { position: relative; width: min(100vw, calc(100vh * @W@ / @H@)); aspect-ratio: @W@ / @H@;
           box-shadow: 0 6px 30px rgba(0,0,0,.4); }
  .stage svg { position: absolute; inset: 0; width: 100%; height: 100%; display: none; }
  body.de svg.l-de, body.eo svg.l-eo, body.en svg.l-en { display: block; }
  .clip { position: absolute; object-fit: contain; background: #fff; }
  .langs { position: absolute; top: 2.3%; right: 3%; display: flex; gap: .35em;
           font: 700 clamp(11px, 1.15vw, 16px)/1 Helvetica, Arial, sans-serif; }
  .langs button { font: inherit; padding: .4em .7em; border-radius: 999px; cursor: pointer;
                  border: 1.5px solid #555f64; background: #fff; color: #1e282c; }
  .langs button[aria-pressed="true"] { background: #1e282c; color: #fff; border-color: #1e282c; }
  .langs button:focus-visible { outline: 3px solid #0072B2; outline-offset: 2px; }
  @media print {
    @page { size: @W@px @H@px; margin: 0; }
    html, body { background: #fff; overflow: visible; height: auto; }
    .slide { display: block; position: static; page-break-after: always; }
    .stage { width: @W@px; box-shadow: none; }
    .langs { display: none; }
    .clip { display: none; }
  }
</style>
</head>
<body class="de">
@DEFS@
@SECTIONS@
<script>
  const LANGS = ['de', 'eo', 'en'];
  const BASE = @BASE@;
  const slides = [...document.querySelectorAll('.slide')];
  let i = 0, lang = 'de';
  const m = /^#s(\\d+)(?:-(de|eo|en))?$/.exec(location.hash);
  if (m) { i = Math.min(slides.length - 1, Math.max(0, +m[1] - BASE)); if (m[2]) lang = m[2]; }
  else { try { const l = localStorage.getItem('deck-lang'); if (LANGS.includes(l)) lang = l; } catch (e) {} }
  function render() {
    slides.forEach((s, k) => s.classList.toggle('on', k === i));
    document.body.className = lang;
    document.documentElement.lang = lang;
    document.querySelectorAll('video.clip').forEach(v => { v.setAttribute('aria-label', v.dataset['label' + lang[0].toUpperCase() + lang[1]]); if (!v.closest('.on')) v.pause(); });
    document.querySelectorAll('.langs button').forEach(b => b.setAttribute('aria-pressed', b.dataset.lang === lang));
    history.replaceState(null, '', '#s' + (i + BASE) + '-' + lang);
  }
  function show(n) { i = Math.min(slides.length - 1, Math.max(0, n)); render(); }
  function setLang(l) { lang = l; try { localStorage.setItem('deck-lang', l); } catch (e) {} render(); }
  document.addEventListener('keydown', e => {
    if ((e.target.tagName === 'BUTTON' || e.target.tagName === 'VIDEO') && (e.key === ' ' || e.key === 'Enter')) return;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) show(i + 1);
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(e.key)) show(i - 1);
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(slides.length - 1);
    else if (['1', '2', '3'].includes(e.key)) setLang(LANGS[+e.key - 1]);
    else return;
    e.preventDefault();
  });
  document.addEventListener('click', e => {
    const b = e.target.closest('.langs button');
    if (b) { setLang(b.dataset.lang); return; }
    if (e.target.closest('video') || e.target.closest('a')) return;
    show(e.clientX < innerWidth / 3 ? i - 1 : i + 1);
  });
  render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
