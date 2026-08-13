# -*- coding: utf-8 -*-
"""Erzeugt den Icon-Vorrat für Kanban-Boards (PNG + ICO)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "icons"
SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# Palette an Kanban-UI angelehnt
BG = (31, 61, 47, 255)
BG2 = (39, 76, 58, 255)
CHALK = (232, 240, 230, 255)
PAPER = (255, 253, 246, 255)
ACCENT = (226, 165, 58, 255)
INK = (26, 36, 28, 255)
DANGER = (196, 92, 74, 255)
BLUE = (111, 143, 173, 255)
GREEN = (111, 155, 106, 255)
ORANGE = (196, 122, 74, 255)
PURPLE = (138, 123, 181, 255)
PINK = (196, 92, 122, 255)
TEAL = (74, 155, 142, 255)


def _bg(size: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(1, size // 32)
    # abgerundetes Schild
    draw.rounded_rectangle(
        (pad, pad, size - 1 - pad, size - 1 - pad),
        radius=max(4, size // 6),
        fill=BG,
    )
    # leichter Verlauf oben
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(
        (pad, pad, size - 1 - pad, size // 2),
        radius=max(4, size // 6),
        fill=(255, 255, 255, 28),
    )
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    return img, draw


def _save(name: str, base: Image.Image) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    png_path = OUT / f"{name}.png"
    ico_path = OUT / f"{name}.ico"
    base = base.convert("RGBA").resize((256, 256), Image.Resampling.LANCZOS)
    base.save(png_path, format="PNG")
    # Pillow skaliert aus dem großen Bild die angegebenen Größen ins ICO
    base.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"  {name} ({ico_path.stat().st_size} bytes)")


def icon_kanban(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    # drei Spalten
    gap = m // 16
    left = m // 6
    top = m // 5
    bottom = m - m // 6
    width = (m - 2 * left - 2 * gap) // 3
    colors = [GREEN, ACCENT, BLUE]
    for i, color in enumerate(colors):
        x0 = left + i * (width + gap)
        d.rounded_rectangle((x0, top, x0 + width, bottom), radius=m // 28, fill=PAPER)
        # Karten
        cy = top + m // 14
        for _ in range(3):
            d.rounded_rectangle(
                (x0 + m // 40, cy, x0 + width - m // 40, cy + m // 12),
                radius=m // 40,
                fill=color,
            )
            cy += m // 9
    return img


def icon_sticky(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    notes = [
        (m // 5, m // 5, ACCENT, -8),
        (m // 3, m // 3, PAPER, 6),
        (int(m / 2.2), int(m / 4.5), TEAL, -4),
    ]
    for x, y, color, rot in notes:
        note = Image.new("RGBA", (m, m), (0, 0, 0, 0))
        nd = ImageDraw.Draw(note)
        s = m // 3
        nd.rounded_rectangle((0, 0, s, s), radius=max(2, m // 40), fill=color)
        nd.line((s // 6, s // 3, s - s // 6, s // 3), fill=(26, 36, 28, 180), width=max(1, m // 64))
        nd.line((s // 6, s // 2, s - s // 5, s // 2), fill=(26, 36, 28, 120), width=max(1, m // 64))
        note = note.rotate(rot, resample=Image.Resampling.BICUBIC, center=(s // 2, s // 2))
        img.alpha_composite(note, dest=(int(x), int(y)))
    return img


def icon_bulb(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    cx, cy = m // 2, m // 2 - m // 16
    r = m // 5
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT)
    # Sockel
    d.rectangle((cx - r // 2, cy + r - m // 32, cx + r // 2, cy + r + m // 8), fill=CHALK)
    d.rectangle((cx - r // 3, cy + r + m // 10, cx + r // 3, cy + r + m // 5), fill=(180, 190, 175, 255))
    # Strahlen
    for ang_dx, ang_dy in [(-1, -1), (0, -1), (1, -1), (-1.2, 0), (1.2, 0)]:
        x0 = cx + int(ang_dx * (r + m // 20))
        y0 = cy + int(ang_dy * (r + m // 20))
        x1 = cx + int(ang_dx * (r + m // 7))
        y1 = cy + int(ang_dy * (r + m // 7))
        d.line((x0, y0, x1, y1), fill=ACCENT, width=max(2, m // 32))
    return img


def icon_check(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    d.rounded_rectangle(
        (m // 5, m // 5, m - m // 5, m - m // 5),
        radius=m // 12,
        fill=PAPER,
    )
    # Haken
    pts = [
        (m // 3, m // 2),
        (m // 2 - m // 32, m // 2 + m // 6),
        (m - m // 3, m // 3),
    ]
    d.line(pts, fill=GREEN, width=max(4, m // 14), joint="curve")
    return img


def icon_game(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    d.rounded_rectangle(
        (m // 6, m // 3, m - m // 6, m - m // 4),
        radius=m // 6,
        fill=INK,
    )
    # D-Pad
    cx, cy = m // 3, m // 2 + m // 32
    s = m // 18
    d.rectangle((cx - s, cy - 3 * s, cx + s, cy + 3 * s), fill=CHALK)
    d.rectangle((cx - 3 * s, cy - s, cx + 3 * s, cy + s), fill=CHALK)
    # Buttons
    d.ellipse((m * 2 // 3 - s, cy - 3 * s, m * 2 // 3 + s, cy - s), fill=DANGER)
    d.ellipse((m * 2 // 3 + s, cy - s, m * 2 // 3 + 3 * s, cy + s), fill=ACCENT)
    d.ellipse((m * 2 // 3 - 3 * s, cy - s, m * 2 // 3 - s, cy + s), fill=BLUE)
    d.ellipse((m * 2 // 3 - s, cy + s, m * 2 // 3 + s, cy + 3 * s), fill=GREEN)
    return img


def icon_star(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    cx, cy = m // 2, m // 2
    r_out, r_in = m // 3, m // 7
    import math

    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=ACCENT)
    return img


def icon_rocket(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    cx = m // 2
    # Körper
    d.ellipse((cx - m // 8, m // 5, cx + m // 8, m // 5 + m // 3), fill=PAPER)
    d.rectangle((cx - m // 8, m // 3, cx + m // 8, m * 2 // 3), fill=PAPER)
    # Spitze
    d.polygon(
        [(cx, m // 8), (cx - m // 8, m // 3), (cx + m // 8, m // 3)],
        fill=ACCENT,
    )
    # Fenster
    d.ellipse((cx - m // 16, m // 2.6, cx + m // 16, m // 2.6 + m // 8), fill=BLUE)
    # Flossen
    d.polygon([(cx - m // 8, m * 2 // 3), (cx - m // 4, m * 3 // 4), (cx - m // 8, m // 2)], fill=DANGER)
    d.polygon([(cx + m // 8, m * 2 // 3), (cx + m // 4, m * 3 // 4), (cx + m // 8, m // 2)], fill=DANGER)
    # Flamme
    d.polygon(
        [(cx - m // 14, m * 2 // 3), (cx, m - m // 8), (cx + m // 14, m * 2 // 3)],
        fill=ORANGE,
    )
    return img


def icon_palette(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    d.ellipse((m // 5, m // 5, m - m // 5, m - m // 5), fill=PAPER)
    # Daumenloch
    d.ellipse((m // 2, m // 2, m // 2 + m // 6, m // 2 + m // 6), fill=BG)
    spots = [
        (m // 3, m // 3, DANGER),
        (m // 2, m // 4, ACCENT),
        (m * 2 // 3, m // 3, BLUE),
        (m // 3, m // 2, GREEN),
        (m * 2 // 3, m // 2, PURPLE),
    ]
    r = m // 16
    for x, y, c in spots:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    return img


def icon_target(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    cx, cy = m // 2, m // 2
    for r, c in [(m // 3, PAPER), (m // 4, DANGER), (m // 6, PAPER), (m // 12, DANGER)]:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    return img


def icon_book(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    d.rounded_rectangle((m // 5, m // 5, m // 2, m - m // 5), radius=m // 40, fill=BLUE)
    d.rounded_rectangle((m // 2 - 2, m // 5, m - m // 5, m - m // 5), radius=m // 40, fill=PAPER)
    d.line((m // 2, m // 5, m // 2, m - m // 5), fill=INK, width=max(2, m // 48))
    for i in range(3):
        y = m // 3 + i * m // 10
        d.line((m // 2 + m // 16, y, m - m // 4, y), fill=(180, 170, 150, 255), width=max(1, m // 64))
    return img


def icon_puzzle(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    # 2x2 Puzzle
    cells = [
        (m // 5, m // 5, ACCENT),
        (m // 2, m // 5, TEAL),
        (m // 5, m // 2, PURPLE),
        (m // 2, m // 2, ORANGE),
    ]
    s = m * 3 // 10
    for x, y, c in cells:
        d.rounded_rectangle((x, y, x + s, y + s), radius=m // 28, fill=c)
    # Noppen
    r = m // 18
    d.ellipse((m // 2 - r, m // 3 - r, m // 2 + r, m // 3 + r), fill=ACCENT)
    d.ellipse((m // 3 - r, m // 2 - r, m // 3 + r, m // 2 + r), fill=PURPLE)
    return img


def icon_heart(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    cx, cy = m // 2, m // 2 + m // 32
    r = m // 6
    d.ellipse((cx - 2 * r, cy - r - r // 2, cx, cy + r // 2), fill=PINK)
    d.ellipse((cx, cy - r - r // 2, cx + 2 * r, cy + r // 2), fill=PINK)
    d.polygon(
        [
            (cx - 2 * r + m // 64, cy),
            (cx + 2 * r - m // 64, cy),
            (cx, cy + 2 * r),
        ],
        fill=PINK,
    )
    return img


def icon_folder(size: int = 256) -> Image.Image:
    img, d = _bg(size)
    m = size
    d.rounded_rectangle((m // 5, m // 3, m - m // 5, m - m // 5), radius=m // 28, fill=ACCENT)
    d.rounded_rectangle((m // 5, m // 4, m // 2, m // 2), radius=m // 40, fill=(200, 140, 40, 255))
    # Karte peekt raus
    d.rounded_rectangle((m // 3, m // 5, m * 2 // 3, m // 2), radius=m // 40, fill=PAPER)
    return img


CATALOG = [
    ("kanban", "Kanban", icon_kanban),
    ("sticky", "Notizen", icon_sticky),
    ("bulb", "Ideen", icon_bulb),
    ("check", "Erledigt", icon_check),
    ("game", "Spiel", icon_game),
    ("star", "Favorit", icon_star),
    ("rocket", "Start", icon_rocket),
    ("palette", "Design", icon_palette),
    ("target", "Ziel", icon_target),
    ("book", "Lernen", icon_book),
    ("puzzle", "Rätsel", icon_puzzle),
    ("heart", "Kids", icon_heart),
    ("folder", "Ordner", icon_folder),
]


def main() -> None:
    print(f"Icons nach {OUT}")
    meta = []
    for slug, label, fn in CATALOG:
        _save(slug, fn(256))
        meta.append({"id": slug, "label": label, "png": f"{slug}.png", "ico": f"{slug}.ico"})
    (OUT / "catalog.json").write_text(
        __import__("json").dumps({"icons": meta}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(meta)} Icons erzeugt.")


if __name__ == "__main__":
    main()
