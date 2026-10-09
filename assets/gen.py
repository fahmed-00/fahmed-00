#!/usr/bin/env python3
"""Generate an animated ASCII 'desert night' SVG + a terminal card SVG for a GitHub profile.

Pure stdlib. GitHub renders SVG <img> with CSS animations (no JS), so everything
moves with @keyframes. Each glyph gets an explicit x position so the grid stays
aligned whatever monospace font the viewer has.
"""
import math
import random
from html import escape
from pathlib import Path

random.seed(7)

COLS, ROWS = 120, 46
CW, CH = 8, 13          # cell size in px
W, H = COLS * CW, ROWS * CH
OUT = Path(__file__).parent  # writes next to this script

grid = [[None] * COLS for _ in range(ROWS)]   # (char, color, cls, style)


def put(r, c, ch, color, cls="", style=""):
    if 0 <= r < ROWS and 0 <= c < COLS and ch != " ":
        grid[r][c] = (ch, color, cls, style)


# ── terrain heightfields (row index of the surface; smaller = higher) ──────
def far_dune(c):
    return 33 + 1.6 * math.sin(c / 9.0) + 1.1 * math.sin(c / 4.3 + 1.2)


def near_dune(c):
    # tall dune on the left where the acacia stands, a long slope to the right
    peak = 25 + 0.012 * (c - 30) ** 2
    return min(44.0, peak + 0.9 * math.sin(c / 5.0))


horizon = [far_dune(c) for c in range(COLS)]
near = [near_dune(c) for c in range(COLS)]

# ── sky: milky way band + stars ────────────────────────────────────────────
STAR_COLORS = ["#e8ecff", "#cdd6ff", "#fff3d6", "#bfe3ff", "#ffffff"]
for r in range(ROWS):
    for c in range(COLS):
        if r >= horizon[c] - 0.5 or r >= near[c] - 0.5:
            continue
        # band runs from bottom-left to top-right
        d = (r - (30 - c * 0.27)) / 5.5
        band = math.exp(-d * d)
        p = random.random()
        if p < 0.7 * band:
            ch = random.choice("·.:·∙")
            put(r, c, ch, random.choice(["#8f86c9", "#a99be0", "#6f7fc4", "#c3b6f0"]),
                "mw", f"animation-delay:-{random.uniform(0, 9):.1f}s")
        elif p < 0.7 * band + 0.035:
            ch = random.choices("·∙•+*✦", weights=[40, 25, 15, 8, 6, 3])[0]
            cls = "tw" if random.random() < 0.45 else ""
            style = (f"animation-delay:-{random.uniform(0, 4):.2f}s;"
                     f"animation-duration:{random.uniform(1.8, 4.5):.2f}s") if cls else ""
            put(r, c, ch, random.choice(STAR_COLORS), cls, style)

# ── distant town on the horizon ────────────────────────────────────────────
for c in range(78, 104):
    r = int(min(horizon[78:104])) - 1
    if random.random() < 0.55:
        ch = random.choice("▪▫ı╻▖▗·")
        put(r, c, ch, random.choice(["#ffb454", "#ffcc80", "#ff9e5e"]), "town",
            f"animation-delay:-{random.uniform(0, 3):.2f}s;animation-duration:{random.uniform(.6, 2.2):.2f}s")
        if random.random() < 0.25:
            put(r - 1, c, "ı", "#ffb454", "town",
                f"animation-delay:-{random.uniform(0, 3):.2f}s")
# warm glow above the town
for c in range(74, 108):
    for dr in (2, 3):
        if random.random() < 0.35:
            put(int(min(horizon[74:108])) - dr - 1, c, "·", "#7a4b3a", "glow")

# ── dunes ──────────────────────────────────────────────────────────────────
for c in range(COLS):
    top_far = int(round(horizon[c]))
    top_near = int(round(near[c]))
    for r in range(top_far, ROWS):
        if r >= top_near:
            break
        depth = r - top_far
        ch = "·" if depth < 3 else random.choice("·•")
        put(r, c, ch, "#3a2f52" if depth < 2 else "#2c2440")
    for r in range(top_near, ROWS):
        depth = r - top_near
        if depth == 0:
            # ridge line, some grains glint
            glint = random.random() < 0.22
            put(r, c, "▁" if not glint else "•", "#b79a7a" if glint else "#6e5a7e",
                "glint" if glint else "",
                f"animation-delay:-{random.uniform(0, 6):.2f}s" if glint else "")
            continue
        ch = random.choices(" ·•●", weights=[18, 40, 28, 14 + depth * 2])[0]
        shade = ["#5a4a6e", "#4a3d5e", "#3c3150", "#2f2742"][min(3, depth // 3)]
        put(r, c, ch, shade)

# ── the acacia on the tall dune ────────────────────────────────────────────
ACACIA = [
    "      ▂▄▅▆▆▅▄▃▂▂▃▄▅▆▆▅▄▂      ",
    "  ▃▅▇██████████████████████▇▅▃ ",
    " ▀▀▀▀▀▀▀▀▀██▀▀▀▀▀▀▀██▀▀▀▀▀▀▀▀▀  ",
    "           ╲╲      ╱╱           ",
    "            ╲╲    ╱╱            ",
    "             ╲╲  ╱╱             ",
    "              ╲╲╱╱              ",
    "               ██               ",
    "               ██               ",
    "               ██               ",
]
tree_c0 = 30 - len(ACACIA[0]) // 2
base_r = int(round(near[30]))
tree_r0 = base_r - len(ACACIA) + 1
for i, line in enumerate(ACACIA):
    for j, ch in enumerate(line):
        put(tree_r0 + i, tree_c0 + j, ch, "#07060d")

# ── render ─────────────────────────────────────────────────────────────────
def render_grid():
    out = []
    for r, row in enumerate(grid):
        y = (r + 1) * CH - 3
        run, key = [], None

        def flush():
            if not run:
                return
            color, cls, style = key
            xs = " ".join(str(c * CW) for c, _ in run)
            txt = "".join(escape(ch) for _, ch in run)
            a = f' class="{cls}"' if cls else ""
            s = f' style="{style}"' if style else ""
            out.append(f'<text x="{xs}" y="{y}" fill="{color}"{a}{s}>{txt}</text>')

        for c, cell in enumerate(row):
            if cell is None:
                flush(); run, key = [], None
                continue
            ch, color, cls, style = cell
            k = (color, cls, style)
            # animated glyphs carry their own delay, so each is its own element
            if k != key or style:
                flush(); run, key = [], k
            run.append((c, ch))
        flush()
    return "\n".join(out)


def meteors():
    trail = "━──····"
    out = []
    specs = [  # (start x, start y, period s, delay s)
        (700, 20, 7.0, 0.5),
        (420, 10, 11.0, 4.0),
        (900, 60, 9.0, 7.5),
    ]
    for i, (x, y, period, delay) in enumerate(specs):
        # tail first, head last: the text runs along the direction of travel
        glyphs = "".join(
            f'<tspan fill-opacity="{1 - k / len(trail):.2f}">{ch}</tspan>'
            for k, ch in reversed(list(enumerate(trail)))
        )
        out.append(
            f'<g class="meteor" style="animation-duration:{period}s;animation-delay:{delay}s">'
            f'<g transform="translate({x} {y}) rotate(152) translate(-64 0)">'
            f'<text x="0" y="0" fill="#fff8e1" font-size="13">{glyphs}✦</text></g></g>'
        )
    return "\n".join(out)


SKY = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Animated ASCII art: the milky way over a lone acacia on desert dunes, meteors falling">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05060f"/>
    <stop offset=".55" stop-color="#0d0f24"/>
    <stop offset=".72" stop-color="#1b1430"/>
    <stop offset="1" stop-color="#120d1e"/>
  </linearGradient>
  <radialGradient id="townglow" cx=".75" cy=".72" r=".25">
    <stop offset="0" stop-color="#ff9e5e" stop-opacity=".18"/>
    <stop offset="1" stop-color="#ff9e5e" stop-opacity="0"/>
  </radialGradient>
</defs>
<style>
  text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size: 12px; white-space: pre; }}
  .tw {{ animation: tw 3s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity: 1 }} 50% {{ opacity: .15 }} }}
  .mw {{ animation: mw 9s ease-in-out infinite; }}
  @keyframes mw {{ 0%,100% {{ opacity: .55 }} 50% {{ opacity: .95 }} }}
  .town {{ animation: town 1.4s steps(2) infinite; }}
  @keyframes town {{ 0%,100% {{ opacity: 1 }} 50% {{ opacity: .45 }} }}
  .glint {{ animation: glint 6s ease-in-out infinite; }}
  @keyframes glint {{ 0%,85%,100% {{ opacity: .35 }} 92% {{ opacity: 1 }} }}
  .glow {{ opacity: .6 }}
  .meteor {{ opacity: 0; animation: fall 8s linear infinite; }}
  @keyframes fall {{
    0%   {{ opacity: 0; transform: translate(0,0) }}
    2%   {{ opacity: 1 }}
    12%  {{ opacity: 0; transform: translate(-260px,140px) }}
    100% {{ opacity: 0; transform: translate(-260px,140px) }}
  }}
  @media (prefers-reduced-motion: reduce) {{ .tw,.mw,.town,.glint,.meteor {{ animation: none }} }}
</style>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<rect width="{W}" height="{H}" fill="url(#townglow)"/>
{meteors()}
{render_grid()}
</svg>
"""

# ── terminal card ──────────────────────────────────────────────────────────
LINES = [
    ("$", "whoami", "#7ee787"),
    (">", "fateen ahmed — ai / cs", "#e6edf3"),
    ("$", "cat about.txt", "#7ee787"),
    (">", "student @ illinois tech · chicago", "#c9d1d9"),
    (">", "ml · data pipelines · agents · full-stack", "#c9d1d9"),
    ("$", "ls ./interests", "#7ee787"),
    (">", "llm-agents/  network-analysis/  iot/  flutter/", "#79c0ff"),
    ("$", "echo $STATUS", "#7ee787"),
    (">", "building things under desert skies ✦", "#ffb454"),
]
CARD_W, LH = 620, 22
CARD_H = 44 + LH * len(LINES) + 18
step = 0.9
rows = []
for i, (p, txt, color) in enumerate(LINES):
    y = 44 + LH * i + 14
    d = 0.4 + i * step
    n = len(txt)
    pc = "#6e7681" if p == ">" else "#ffb454"
    rows.append(
        f'<g class="ln" style="animation-delay:{d:.2f}s">'
        f'<text x="24" y="{y}" fill="{pc}">{escape(p)}</text>'
        f'<text x="44" y="{y}" fill="{color}">{escape(txt)}</text>'
        f'<rect class="cover" x="40" y="{y - 15}" width="{n * 8.4 + 12:.0f}" height="20" fill="#0d1117" '
        f'style="animation-delay:{d:.2f}s;animation-duration:{max(.35, n * .03):.2f}s;animation-timing-function:steps({max(1, n)})"/></g>'
    )
last_y = 44 + LH * (len(LINES) - 1) + 14
CARD = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {CARD_H}" width="{CARD_W}" height="{CARD_H}" role="img" aria-label="Terminal: fateen ahmed — AI / CS at Illinois Tech, Chicago">
<style>
  text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size: 14px; white-space: pre; }}
  .ln {{ opacity: 0; animation: show .01s forwards; }}
  @keyframes show {{ to {{ opacity: 1 }} }}
  .cover {{ animation: type 1s forwards; }}
  @keyframes type {{ to {{ transform: translateX(440px) }} }}
  .cur {{ animation: show .01s forwards, blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0 }} }}
  @media (prefers-reduced-motion: reduce) {{ .ln {{ opacity: 1; animation: none }} .cover {{ display: none }} }}
</style>
<rect x=".5" y=".5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>
<circle cx="22" cy="18" r="5.5" fill="#ff5f57"/><circle cx="40" cy="18" r="5.5" fill="#febc2e"/><circle cx="58" cy="18" r="5.5" fill="#28c840"/>
<text x="{CARD_W / 2}" y="22" fill="#6e7681" text-anchor="middle" font-size="12">fateen@desert-night: ~</text>
{chr(10).join(rows)}
<rect class="cur ln" x="{44 + len(LINES[-1][1]) * 8.4 + 16:.0f}" y="{last_y - 12}" width="8" height="15" fill="#ffb454" style="animation-delay:{0.4 + len(LINES) * step:.1f}s"/>
</svg>
"""

# header is ascii.rest's desert-night.gif now; the hand-drawn sky is kept but not written
(OUT / "terminal.svg").write_text(CARD)
print(f"terminal.svg {len(CARD) / 1024:.1f} kB")
