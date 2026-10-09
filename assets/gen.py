#!/usr/bin/env python3
"""Generate whoami.svg — the 'whoami' card under the desert-night header.

Drawn the way ascii.rest's desert-night is drawn, so the two read as one piece:
a 200-column grid (6.4 px cells at 1280 px), each cell one dot from " ·•●",
coloured from desert-night's own palette on its ground colour. The sky is a
random dither (star dust), the sand an ordered 4×4 Bayer dither. The name is a
5×7 dot-matrix font made of the same dots; the terminal lines are plain mono
text in the palette's colours.

Pure stdlib. GitHub renders SVG <img> with CSS animations (no JS): lines type
out, stars twinkle, a shimmer sweeps the name, sand glints, meteors fall.

Edit LEFT / RIGHT (and optionally NAME) below, then: python3 assets/gen.py
"""
import math
from html import escape
from pathlib import Path

# ── content ────────────────────────────────────────────────────────────────
NAME = ""   # optional dot-matrix banner (letters in FONT below); empty = none
LEFT = [
    ("$", "whoami", "cmd"),
    (">", "fateen ahmed — ai / cs", "out"),
    ("$", "cat about.txt", "cmd"),
    (">", "building agentic ai @ byanat", "out"),
    (">", "prev: simulation @ amazon", "out"),
]
RIGHT = [
    ("$", "ls ./interests", "cmd"),
    (">", "agentic-ai/  llm-agents/  rag/  tool-use/", "dir"),
    (">", "machine-learning/  deep-learning/  nlp/", "dir"),
    ("$", "echo $STATUS", "cmd"),
    (">", "building things under desert skies ✦", "status"),
]

# ── desert-night's palette (ascii.rest, MIT) ───────────────────────────────
GROUND = "#04060c"
SKY_DUST = ["#101830", "#16213f", "#1e2b50", "#283864"]
BAND = ["#34477a", "#45598f", "#5a6fa6", "#7488bd", "#93a5d2"]
STARS = ["#b6c3e4", "#d8e0f2", "#f4f6fb", "#cfe0ff", "#fff3dc"]
NAME_RAMP = ["#fff3dc", "#ffe2b4", "#ffd8a8", "#f5c98e", "#e2a86e", "#c9a3a3", "#a88590"]
SAND = ["#2a2230", "#3d2f3a", "#56404a", "#735358", "#946a62", "#b6836c"]
TOWN = ["#ffd8a8", "#ff9a52", "#e07a3e", "#f5c98e"]
GLOW = ["#2a2230", "#3d2f3a", "#56404a"]
TEXT = {"$": "#f5c98e", ">": "#57498a", "cmd": "#b6c3e4", "out": "#f4f6fb",
        "dir": "#a9c4ff", "status": "#ffe2b4"}

# ── grid ───────────────────────────────────────────────────────────────────
COLS, ROWS = 200, 48
CELL = 1280 / COLS                       # 6.4 px, same as the header GIF
W, H = 1280, round(ROWS * CELL)
R = {1: 0.85, 2: 1.75, 3: 2.75}          # dot radius for · • ●
BAYER = [v / 16 - 0.47 for v in (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)]


def hash01(x, y, salt=0):
    h = (x * 374761393 + y * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 0xFFFFFF


def ordered(v, x, y):
    """brightness 0..1 → dot level 0..3 through the 4×4 Bayer matrix."""
    return max(0, min(3, round(v * 3 + BAYER[(x % 4) + (y % 4) * 4])))


cells = {}   # (c, r) -> (level, colour, cls, style)


def put(c, r, level, colour, cls="", style=""):
    if 0 <= c < COLS and 0 <= r < ROWS and level > 0:
        cells[(c, r)] = (level, colour, cls, style)


# ── 5×7 dot font ───────────────────────────────────────────────────────────
FONT = {
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    " ": ["000"] * 7,
}
SCALE, GAP, NAME_TOP = 2, 2, 5
name_w = sum(len(FONT[ch][0]) * SCALE + GAP for ch in NAME) - GAP
x0 = (COLS - name_w) // 2
name_cells = set()
x = x0
for ch in NAME:
    g = FONT[ch]
    for fy, row in enumerate(g):
        for fx, bit in enumerate(row):
            if bit == "1":
                for dy in range(SCALE):
                    for dx in range(SCALE):
                        name_cells.add((x + fx * SCALE + dx, NAME_TOP + fy * SCALE + dy))
    x += len(g[0]) * SCALE + GAP
name_rows = 7 * SCALE if NAME else 0
for (c, r) in name_cells:
    t = (r - NAME_TOP) / (name_rows - 1)
    colour = NAME_RAMP[min(len(NAME_RAMP) - 1, int(t * len(NAME_RAMP)))]
    put(c, r, 3, colour, "shim", f"animation-delay:{(c - x0) * 0.03:.2f}s")
# a soft halo of small warm dots around the letters
for (c, r) in name_cells:
    for dc, dr in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1)):
        n = (c + dc, r + dr)
        if n not in name_cells and n not in cells and hash01(*n, 3) < 0.55:
            put(*n, 1, "#3d3466")

# ── text layout (kept clear of dots) ───────────────────────────────────────
FS, CHAR_W, LINE_H = 22, 13.2, 33
TEXT_TOP = (NAME_TOP + name_rows + 9) if NAME else 10          # first baseline, in rows
LEFT_X, RIGHT_X = 10 * CELL, 100 * CELL
clear = set()
for base_x, lines in ((LEFT_X, LEFT), (RIGHT_X, RIGHT)):
    for i, (_, s, _) in enumerate(lines):
        y = TEXT_TOP * CELL + i * LINE_H
        c0 = int(base_x / CELL) - 1
        c1 = int((base_x + (len(s) + 3) * CHAR_W) / CELL) + 1
        for r in range(int((y - FS) / CELL) - 1, int(y / CELL) + 2):
            for c in range(c0, c1 + 1):
                clear.add((c, r))

# ── dunes: a heightfield lit by the town on the right ──────────────────────
def ridge(c):
    return 38 + 2.0 * math.sin(c / 19.0 + 0.4) + 1.3 * math.sin(c / 7.3 + 1.1)


TOWN_C = (158, 186)
for c in range(COLS):
    top = round(ridge(c))
    slope = ridge(c + 1) - ridge(c - 1)
    for r in range(top, ROWS):
        depth = r - top
        lit = 0.18 + 0.32 * (c / COLS) ** 2 + (0.18 if slope > 0 else -0.04)
        v = max(0.0, lit * (1 - depth / 16))
        lvl = ordered(v + 0.12, c, r)
        if depth == 0:
            if hash01(c, r, 7) < 0.2:
                put(c, r, 2, "#e2bfb4", "glint", f"animation-delay:-{hash01(c, r, 8) * 6:.2f}s")
            else:
                put(c, r, 2, SAND[min(5, 3 + int(v * 4))])
            continue
        put(c, r, lvl, SAND[min(5, max(0, int(v * 9)))])

# town lights on the far ridge + the warm glow above them
for c in range(*TOWN_C):
    top = round(ridge(c)) - 1
    if hash01(c, 0, 11) < 0.45:
        put(c, top, 2 if hash01(c, 1, 11) < 0.7 else 3, TOWN[int(hash01(c, 2, 11) * 4)],
            "town", f"animation-delay:-{hash01(c, 3, 11) * 3:.2f}s;animation-duration:{0.7 + hash01(c, 4, 11) * 1.6:.2f}s")
mid = sum(TOWN_C) / 2
for c in range(TOWN_C[0] - 26, min(COLS, TOWN_C[1] + 26)):
    for r in range(round(ridge(c)) - 12, round(ridge(c)) - 1):
        if (c, r) in cells:
            continue
        d = math.hypot((c - mid) / 30, (r - ridge(c)) / 9)
        v = max(0.0, 0.42 - 0.42 * d)
        if v > 0 and hash01(c, r, 13) < v * 1.3:
            put(c, r, 1, GLOW[min(2, int(v * 6))])

# ── sky: star dust, the milky way band, bright stars ───────────────────────
for c in range(COLS):
    sky_bottom = round(ridge(c))
    for r in range(sky_bottom):
        if (c, r) in cells or (c, r) in clear or (c, r) in name_cells:
            continue
        # the band arcs from the lower left up to the upper right, split by a dust lane
        d = (r - (44 - c * 0.2)) / 7.5
        band = math.exp(-d * d) * (0.35 + 0.65 * (c / COLS))
        lane = math.exp(-((d + 0.15) / 0.22) ** 2) * 0.75
        band = max(0.0, band * (1 - lane))
        near_name = (min(abs(c - x0), abs(c - (x0 + name_w))) < 3 or NAME_TOP - 2 < r < NAME_TOP + name_rows + 2) and x0 - 3 < c < x0 + name_w + 3
        if near_name:
            band *= 0.25
        p = hash01(c, r, 1)
        if p < 0.006:
            lvl = 3 if hash01(c, r, 2) < 0.3 else 2
            tw = hash01(c, r, 4) < 0.6
            put(c, r, lvl, STARS[int(hash01(c, r, 5) * len(STARS))], "tw" if tw else "",
                f"animation-delay:-{hash01(c, r, 6) * 4:.2f}s;animation-duration:{2 + hash01(c, r, 9) * 3:.2f}s" if tw else "")
        elif p < 0.006 + 0.55 * band:
            lvl = 2 if hash01(c, r, 10) < band * 0.5 else 1
            put(c, r, lvl, BAND[min(4, int(band * 5 + hash01(c, r, 12)))], "mw",
                f"animation-delay:-{hash01(c, r, 14) * 9:.1f}s")
        elif p < 0.006 + 0.55 * band + 0.05:
            put(c, r, 1, SKY_DUST[int(hash01(c, r, 15) * 4)])

# ── typing ─────────────────────────────────────────────────────────────────
DELAY, CPS, PAUSE = 0.6, 0.032, 0.3
t = DELAY
text_out = []
cursor = None
for base_x, lines in ((LEFT_X, LEFT), (RIGHT_X, RIGHT)):
    for i, (p, s, kind) in enumerate(lines):
        y = TEXT_TOP * CELL + i * LINE_H
        glyphs = [(p, TEXT[p])] + [(" ", None)] + [(ch, TEXT[kind]) for ch in s]
        for j, (ch, col) in enumerate(glyphs):
            if ch == " ":
                continue
            text_out.append(f'<text class="ty" x="{base_x + j * CHAR_W:.1f}" y="{y:.1f}" fill="{col}" '
                            f'style="animation-delay:{t + j * CPS:.2f}s">{escape(ch)}</text>')
        t += len(glyphs) * CPS + PAUSE
        cursor = (base_x + len(glyphs) * CHAR_W + 2, y)
CURSOR_T = t


# ── meteors: a head and a fading tail of dots ──────────────────────────────
def meteor(x, y, period, delay):
    dots = []
    for k in range(9):
        r = [2.6, 2.1, 1.8, 1.5, 1.2, 1.0, .85, .7, .6][k]
        op = 1 - k / 9
        dots.append(f'<circle cx="{x + k * 5.6:.1f}" cy="{y - k * 3.2:.1f}" r="{r}" fill="#f4f6fb" fill-opacity="{op:.2f}"/>')
    return (f'<g class="meteor" style="animation-duration:{period}s;animation-delay:{delay}s">'
            + "".join(dots) + "</g>")


# ── render: one <circle> per dot, grouped by colour/animation ──────────────
groups = {}
for (c, r), (lvl, colour, cls, style) in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    cx, cy = (c + 0.5) * CELL, (r + 0.5) * CELL
    circle = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R[lvl]}"/>'
    groups.setdefault((colour, cls, style), []).append(circle)
dots_svg = "\n".join(
    f'<g fill="{colour}"' + (f' class="{cls}"' if cls else "") + (f' style="{style}"' if style else "") + ">"
    + "".join(circles) + "</g>"
    for (colour, cls, style), circles in groups.items()
)

cx, cy = cursor
SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="whoami: fateen ahmed — AI / CS — building agentic AI at Byanat, previously simulation at Amazon — interests: agentic AI, LLM agents, RAG, tool use, machine learning, deep learning, NLP">
<style>
  text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size: {FS}px; }}
  .ty {{ opacity: 0; animation: show .01s forwards; }}
  @keyframes show {{ to {{ opacity: 1 }} }}
  .shim {{ animation: shim 6s ease-in-out infinite; }}
  @keyframes shim {{ 0%,100% {{ opacity: .78 }} 7% {{ opacity: 1 }} 14% {{ opacity: .78 }} }}
  .tw {{ animation: tw 3s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity: 1 }} 50% {{ opacity: .15 }} }}
  .mw {{ animation: mw 9s ease-in-out infinite; }}
  @keyframes mw {{ 0%,100% {{ opacity: .6 }} 50% {{ opacity: 1 }} }}
  .glint {{ animation: glint 6s ease-in-out infinite; }}
  @keyframes glint {{ 0%,85%,100% {{ opacity: .35 }} 92% {{ opacity: 1 }} }}
  .town {{ animation: town 1.4s steps(2) infinite; }}
  @keyframes town {{ 0%,100% {{ opacity: 1 }} 50% {{ opacity: .45 }} }}
  .meteor {{ opacity: 0; animation: fall 9s linear infinite; }}
  @keyframes fall {{
    0%   {{ opacity: 0; transform: translate(0,0) }}
    2%   {{ opacity: 1 }}
    11%  {{ opacity: 0; transform: translate(-240px,140px) }}
    100% {{ opacity: 0; transform: translate(-240px,140px) }}
  }}
  .cur {{ opacity: 0; animation: show .01s {CURSOR_T:.2f}s forwards, blink 1s steps(1) {CURSOR_T:.2f}s infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0 }} }}
  @media (prefers-reduced-motion: reduce) {{
    .ty,.cur {{ opacity: 1; animation: none }}
    .shim,.tw,.mw,.glint,.town,.meteor {{ animation: none }}
  }}
</style>
<rect width="{W}" height="{H}" fill="{GROUND}"/>
{meteor(1040, 24, 9, 2)}
{meteor(560, 14, 13, 7)}
{dots_svg}
{chr(10).join(text_out)}
<rect class="cur" x="{cx:.1f}" y="{cy - FS + 2:.1f}" width="8" height="{FS + 2}" fill="#f5c98e"/>
</svg>
"""

out = Path(__file__).parent / "whoami.svg"
out.write_text(SVG)
print(f"{out.name} {len(SVG) / 1024:.0f} kB · {len(cells)} dots · typing ends at {CURSOR_T:.1f}s")
