"""
scripts/generate_island_placeholders.py
Generate placeholder PNGs for island decoration + shop items.

Outputs to:
  frontend/static/img/island/decor/{zone}_{slug}.png   (46 decor items)
  frontend/static/img/island/items/{slug}.png           (9 evo/food items)

Style: 256×256 px, transparent background, zone-colored rounded card
       with a simple geometric icon + readable label.

Run:
  python3 scripts/generate_island_placeholders.py
  python3 scripts/generate_island_placeholders.py --force   # overwrite existing
"""

import argparse
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install pillow")
    sys.exit(1)

# ── Paths ────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
DECOR_DIR  = ROOT / "frontend" / "static" / "img" / "island" / "decor"
ITEMS_DIR  = ROOT / "frontend" / "static" / "img" / "island" / "items"

# ── Zone color palette (matches theme.css) ───────────────────────
ZONE_COLORS = {
    "forest":  {"bg": (238, 247, 240), "accent": (138, 196, 168), "ink": (58, 106, 84)},
    "ocean":   {"bg": (238, 244, 250), "accent": (127, 168, 204), "ink": (52, 90, 128)},
    "savanna": {"bg": (251, 238, 242), "accent": (224, 154, 174), "ink": (132, 66, 90)},
    "space":   {"bg": (242, 236, 250), "accent": (184, 164, 220), "ink": (90, 72, 131)},
    "legend":  {"bg": (251, 243, 222), "accent": (238, 199, 112), "ink": (122, 90, 30)},
    # shop items
    "evo_a":   {"bg": (240, 248, 255), "accent": (100, 160, 220), "ink": (30, 80, 140)},
    "evo_b":   {"bg": (255, 240, 255), "accent": (200, 140, 210), "ink": (100, 40, 120)},
    "evo_2":   {"bg": (255, 248, 230), "accent": (230, 180, 60),  "ink": (120, 80, 10)},
    "food":    {"bg": (240, 255, 245), "accent": (80, 200, 120),  "ink": (20, 100, 50)},
}

# ── Decoration items — (zone, slug, emoji_hint, shape) ──────────
#   shape: "circle" | "diamond" | "star" | "square" | "triangle"
DECOR_ITEMS = [
    # Forest (9)
    ("forest", "mushroom_lantern",  "🍄", "circle"),
    ("forest", "signpost",          "🪧", "square"),
    ("forest", "honey_jar",         "🍯", "circle"),
    ("forest", "cabin",             "🏡", "square"),
    ("forest", "fairy_gate",        "🚪", "diamond"),
    ("forest", "treehouse",         "🌳", "triangle"),
    ("forest", "firefly",           "✨", "star"),
    ("forest", "flower_rain",       "🌸", "circle"),
    ("forest", "mist",              "🌫", "diamond"),
    # Ocean (9)
    ("ocean",  "treasure_chest",    "💎", "square"),
    ("ocean",  "shell_chime",       "🐚", "circle"),
    ("ocean",  "coral_lantern",     "🪸", "circle"),
    ("ocean",  "garden",            "🌊", "diamond"),
    ("ocean",  "sea_cave",          "🫧", "triangle"),
    ("ocean",  "palace",            "🏛", "square"),
    ("ocean",  "bubbles",           "○",  "circle"),
    ("ocean",  "light_pillar",      "☀",  "diamond"),
    ("ocean",  "aurora",            "🌈", "star"),
    # Savanna (9)
    ("savanna","baobab",            "🌴", "triangle"),
    ("savanna","pride_rock",        "⬡",  "diamond"),
    ("savanna","oasis",             "💧", "circle"),
    ("savanna","waterfall",         "〰", "square"),
    ("savanna","cliff",             "⛰", "triangle"),
    ("savanna","cave",              "◑",  "square"),
    ("savanna","sunset",            "🌅", "star"),
    ("savanna","migration",         "→",  "diamond"),
    ("savanna","starry_sky",        "★",  "star"),
    # Space (9)
    ("space",  "meteorite",         "●",  "circle"),
    ("space",  "crater",            "◎",  "circle"),
    ("space",  "nebula",            "☁",  "star"),
    ("space",  "black_hole",        "⊛",  "circle"),
    ("space",  "asteroids",         "✦",  "diamond"),
    ("space",  "star_cloud",        "☁",  "star"),
    ("space",  "meteor_shower",     "⟡",  "diamond"),
    ("space",  "aurora",            "≋",  "star"),
    ("space",  "wormhole",          "⊚",  "circle"),
    # Legend (10)
    ("legend", "dragon_nest",       "◈",  "diamond"),
    ("legend", "rainbow_bridge",    "⌒",  "star"),
    ("legend", "phoenix_tree",      "✺",  "triangle"),
    ("legend", "gumiho_shrine",     "⛩",  "square"),
    ("legend", "qilin_prints",      "⟣",  "diamond"),
    ("legend", "sacred_tree",       "✦",  "triangle"),
    ("legend", "magic_circle",      "◉",  "circle"),
    ("legend", "golden_aura",       "☀",  "star"),
    ("legend", "rainbow_waterfall", "≋",  "diamond"),
    ("legend", "star_altar",        "★",  "square"),
]

# ── Shop items — (slug, palette_key, label, shape) ───────────────
SHOP_ITEMS = [
    ("evo_stone_a",  "evo_a",  "Stone A",   "diamond"),
    ("evo_stone_b",  "evo_b",  "Stone B",   "diamond"),
    ("evo_stone_2",  "evo_2",  "Stone 2nd", "diamond"),
    ("legend_stone_a","evo_a", "Legend A",  "star"),
    ("legend_stone_b","evo_b", "Legend B",  "star"),
    ("legend_stone_2","evo_2", "Legend 2",  "star"),
    ("food_small",   "food",   "Small",     "circle"),
    ("food_big",     "food",   "Big",       "circle"),
    ("food_special", "food",   "Special",   "star"),
]

SIZE = 256
PAD  = 28   # inner padding

# ── Drawing helpers ──────────────────────────────────────────────

def _try_font(size: int) -> ImageFont.FreeTypeFont:
    """Load a system font; fall back to default if none found."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Futura.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _rgba(rgb: tuple, a: int = 255) -> tuple:
    return (*rgb, a)


def _draw_rounded_rect(draw: ImageDraw.Draw, xy, radius: int, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius * 2, y0 + radius * 2], fill=fill)
    draw.ellipse([x1 - radius * 2, y0, x1, y0 + radius * 2], fill=fill)
    draw.ellipse([x0, y1 - radius * 2, x0 + radius * 2, y1], fill=fill)
    draw.ellipse([x1 - radius * 2, y1 - radius * 2, x1, y1], fill=fill)


def _draw_shape(draw: ImageDraw.Draw, shape: str, cx: int, cy: int,
                r: int, fill, outline):
    if shape == "circle":
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=3)
    elif shape == "diamond":
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        draw.polygon(pts, fill=fill, outline=outline)
    elif shape == "star":
        pts = []
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(angle), cy + rr * math.sin(angle)))
        draw.polygon(pts, fill=fill, outline=outline)
    elif shape == "triangle":
        pts = [(cx, cy - r), (cx + r, cy + r * 0.75), (cx - r, cy + r * 0.75)]
        draw.polygon(pts, fill=fill, outline=outline)
    else:  # square
        draw.rectangle([cx - r * 0.75, cy - r * 0.75, cx + r * 0.75, cy + r * 0.75],
                       fill=fill, outline=outline, width=3)


def _wrap_text(text: str, max_chars: int = 11) -> list[str]:
    """Split slug_name into readable lines."""
    words = text.replace("_", " ").title().split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def make_placeholder(palette_key: str, label: str, shape: str,
                     out_path: Path, force: bool) -> bool:
    if out_path.exists() and not force:
        return False

    pal = ZONE_COLORS[palette_key]
    bg_rgb    = pal["bg"]
    accent    = pal["accent"]
    ink       = pal["ink"]

    img  = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Card background
    _draw_rounded_rect(draw, [4, 4, SIZE - 4, SIZE - 4], 32,
                       fill=_rgba(bg_rgb, 240))

    # Subtle border
    border_color = _rgba(accent, 180)
    for i in range(3):
        draw.rounded_rectangle([4 + i, 4 + i, SIZE - 4 - i, SIZE - 4 - i],
                                radius=32 - i, outline=border_color, width=1)

    # Shape icon (upper 60% of card)
    cx, cy = SIZE // 2, int(SIZE * 0.40)
    shape_r = int(SIZE * 0.22)
    shape_fill    = _rgba(accent, 200)
    shape_outline = _rgba(ink, 160)
    _draw_shape(draw, shape, cx, cy, shape_r, shape_fill, shape_outline)

    # Label text (lower 35%)
    lines    = _wrap_text(label)
    font_lg  = _try_font(22)
    font_sm  = _try_font(16)
    line_h   = 26
    total_h  = len(lines) * line_h
    start_y  = int(SIZE * 0.67) - total_h // 2

    for i, line in enumerate(lines):
        font = font_lg if i == 0 else font_sm
        bbox = draw.textbbox((0, 0), line, font=font)
        tw   = bbox[2] - bbox[0]
        draw.text(((SIZE - tw) // 2, start_y + i * line_h),
                  line, fill=_rgba(ink, 230), font=font)

    img.save(out_path, "PNG")
    return True


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate island placeholder PNGs")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing PNGs")
    args = parser.parse_args()

    DECOR_DIR.mkdir(parents=True, exist_ok=True)
    ITEMS_DIR.mkdir(parents=True, exist_ok=True)

    created = skipped = 0

    # Decoration items (46)
    print("Generating decoration placeholders…")
    for zone, slug, _emoji, shape in DECOR_ITEMS:
        out  = DECOR_DIR / f"{zone}_{slug}.png"
        label = slug
        ok = make_placeholder(zone, label, shape, out, args.force)
        status = "created" if ok else "skip"
        print(f"  [{status}] decor/{zone}_{slug}.png")
        if ok:
            created += 1
        else:
            skipped += 1

    # Shop items (9 — evolution stones + food)
    print("\nGenerating shop item placeholders…")
    for slug, pal_key, label, shape in SHOP_ITEMS:
        out = ITEMS_DIR / f"{slug}.png"
        ok  = make_placeholder(pal_key, label, shape, out, args.force)
        status = "created" if ok else "skip"
        print(f"  [{status}] items/{slug}.png")
        if ok:
            created += 1
        else:
            skipped += 1

    print(f"\nDone — {created} created, {skipped} skipped.")
    print(f"Decor dir : {DECOR_DIR}")
    print(f"Items dir : {ITEMS_DIR}")
    print("\nTo overwrite all: python3 scripts/generate_island_placeholders.py --force")


if __name__ == "__main__":
    main()
