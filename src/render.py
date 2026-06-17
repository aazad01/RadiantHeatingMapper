"""Render radiant heating layouts as SVG (web) or PNG (files/downloads).

Both renderers accept either:
  - a single-room layout dict from :func:`radiantheat.compute_layout`, or
  - a floor-plan dict from :func:`radiantheat.compute_floor_layout`
    (multiple room loops separated by interior walls).

Drawings include dimension annotations and, for floor plans, interior walls and
per-room labels. ``render_svg`` is dependency-free (ideal for serving on the
web); ``render_png`` uses matplotlib (for downloadable raster files).
"""

from xml.sax.saxutils import escape

SUPPLY_COLOR = "#e8513b"
RETURN_COLOR = "#2f6fd0"
WALL_COLOR = "#222222"
OPENING_COLOR = "#b9a06a"
GRID_COLOR = "#d9dee3"
DIM_COLOR = "#52606d"


def _normalize(obj):
    """Reduce either layout type to a common drawing description."""
    if "rooms" in obj:  # floor plan
        loops = [r["coordinates"] for r in obj["rooms"]]
        labels = [
            (r["x"] + r["width"] / 2, r["y"] + r["length"] / 2,
             f"{r['name']}\n{r['width']:g}×{r['length']:g} m")
            for r in obj["rooms"]
        ]
        t = obj["totals"]
        caption = (
            f"{obj['floor_width']:g}×{obj['floor_length']:g} m floor  |  "
            f"{t['num_rooms']} rooms  |  spacing {obj['pipe_spacing']:g} m  |  "
            f"pipe {t['pipe_length_m']:g} m  |  coverage {t['coverage_percent']:g}%"
        )
        return {
            "width": obj["floor_width"], "length": obj["floor_length"],
            "loops": loops, "walls": obj.get("walls", []),
            "openings": obj.get("openings", []),
            "labels": labels, "caption": caption,
            "rooms": [(r["x"], r["y"], r["width"], r["length"]) for r in obj["rooms"]],
        }
    # single room
    return {
        "width": obj["room_width"], "length": obj["room_length"],
        "loops": [obj["coordinates"]],
        "walls": [],
        "openings": [],
        "labels": [],
        "caption": (
            f"{obj['room_width']:g}×{obj['room_length']:g} m  |  "
            f"spacing {obj['pipe_spacing']:g} m  |  pipe {obj['pipe_length_m']:g} m  |  "
            f"coverage {obj['coverage']['coverage_percent']:g}%"
        ),
        "rooms": [(0, 0, obj["room_width"], obj["room_length"])],
    }


def _split_supply_return(loop):
    """Split a loop into (supply, return) halves for two-tone coloring."""
    if len(loop) < 2:
        return loop, []
    half = len(loop) // 2
    return loop[: half + 1], loop[half:]


# --------------------------------------------------------------------------- #
# SVG
# --------------------------------------------------------------------------- #
def render_svg(layout, width_px=640):
    """Render a layout (single room or floor) as an SVG document string."""
    d = _normalize(layout)
    room_w, room_l = float(d["width"]), float(d["length"])

    # Margins leave room for dimension annotations (more on left/bottom).
    pad_l, pad_r, pad_t, pad_b = 64, 28, 28, 70
    draw_w = max(width_px - pad_l - pad_r, 1)
    scale = draw_w / room_w if room_w else 1
    draw_h = room_l * scale
    svg_w = draw_w + pad_l + pad_r
    svg_h = draw_h + pad_t + pad_b

    def tx(x):
        return pad_l + x * scale

    def ty(y):
        return pad_t + (room_l - y) * scale  # flip Y (room origin is bottom-left)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w:.1f}" '
        f'height="{svg_h:.1f}" viewBox="0 0 {svg_w:.1f} {svg_h:.1f}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<rect x="{tx(0):.2f}" y="{ty(room_l):.2f}" width="{room_w*scale:.2f}" '
        f'height="{room_l*scale:.2f}" fill="#f4f6f8" stroke="#9aa5b1" stroke-width="1.5"/>',
    ]

    # Pipe loops (supply red, return blue) with start/end markers.
    for loop in d["loops"]:
        if len(loop) < 2:
            continue
        supply, ret = _split_supply_return(loop)
        sp = " ".join(f"{tx(x):.2f},{ty(y):.2f}" for x, y in supply)
        rp = " ".join(f"{tx(x):.2f},{ty(y):.2f}" for x, y in ret)
        parts.append(f'<polyline points="{sp}" fill="none" stroke="{SUPPLY_COLOR}" '
                     'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
        parts.append(f'<polyline points="{rp}" fill="none" stroke="{RETURN_COLOR}" '
                     'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
        sx, sy = loop[0]
        ex, ey = loop[-1]
        parts.append(f'<circle cx="{tx(sx):.2f}" cy="{ty(sy):.2f}" r="4" fill="#1a8917"/>')
        parts.append(f'<circle cx="{tx(ex):.2f}" cy="{ty(ey):.2f}" r="4" fill="#7048e8"/>')

    # Interior + perimeter walls.
    for x1, y1, x2, y2 in d["walls"]:
        parts.append(f'<line x1="{tx(x1):.2f}" y1="{ty(y1):.2f}" x2="{tx(x2):.2f}" '
                     f'y2="{ty(y2):.2f}" stroke="{WALL_COLOR}" stroke-width="3.5" '
                     'stroke-linecap="square"/>')

    # Doorway openings drawn as a light threshold across the wall gap.
    for x1, y1, x2, y2 in d["openings"]:
        parts.append(f'<line x1="{tx(x1):.2f}" y1="{ty(y1):.2f}" x2="{tx(x2):.2f}" '
                     f'y2="{ty(y2):.2f}" stroke="{OPENING_COLOR}" stroke-width="2.5" '
                     'stroke-linecap="round" stroke-dasharray="1,3"/>')

    # Per-room labels (floor plans).
    for cx, cy, text in d["labels"]:
        lines = text.split("\n")
        for j, line in enumerate(lines):
            dy = (j - (len(lines) - 1) / 2) * 14
            parts.append(
                f'<text x="{tx(cx):.2f}" y="{ty(cy) + dy:.2f}" text-anchor="middle" '
                f'font-family="sans-serif" font-size="11" fill="#1f2933">{escape(line)}</text>'
            )

    # Dimension annotations: overall width (bottom) and length (left).
    parts += _svg_dim(tx(0), ty(0) + 22, tx(room_w), ty(0) + 22, f"{room_w:g} m", "h")
    parts += _svg_dim(tx(0) - 26, ty(room_l), tx(0) - 26, ty(0), f"{room_l:g} m", "v")

    parts.append(
        f'<text x="{pad_l}" y="{svg_h - 12:.1f}" font-family="sans-serif" '
        f'font-size="12" fill="{DIM_COLOR}">{escape(d["caption"])}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _svg_dim(x1, y1, x2, y2, label, orient):
    """Draw a dimension line with end ticks and a centered label."""
    segs = [f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{DIM_COLOR}" stroke-width="1"/>']
    if orient == "h":
        for x in (x1, x2):
            segs.append(f'<line x1="{x:.2f}" y1="{y1-4:.2f}" x2="{x:.2f}" y2="{y1+4:.2f}" '
                        f'stroke="{DIM_COLOR}" stroke-width="1"/>')
        segs.append(f'<text x="{(x1+x2)/2:.2f}" y="{y1+15:.2f}" text-anchor="middle" '
                    f'font-family="sans-serif" font-size="11" fill="{DIM_COLOR}">{escape(label)}</text>')
    else:
        for y in (y1, y2):
            segs.append(f'<line x1="{x1-4:.2f}" y1="{y:.2f}" x2="{x1+4:.2f}" y2="{y:.2f}" '
                        f'stroke="{DIM_COLOR}" stroke-width="1"/>')
        midy = (y1 + y2) / 2
        segs.append(f'<text x="{x1-8:.2f}" y="{midy:.2f}" text-anchor="middle" '
                    f'font-family="sans-serif" font-size="11" fill="{DIM_COLOR}" '
                    f'transform="rotate(-90 {x1-8:.2f} {midy:.2f})">{escape(label)}</text>')
    return segs


# --------------------------------------------------------------------------- #
# PNG (matplotlib)
# --------------------------------------------------------------------------- #
def render_png(layout, out, dpi=110):
    """Render a layout (single room or floor) to a PNG.

    Args:
        layout: a single-room or floor layout dict.
        out: a file path (str/Path) or a writable binary file-like object.
        dpi: output resolution.

    Raises:
        RuntimeError: if matplotlib is not installed.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without matplotlib
        raise RuntimeError(
            "render_png requires matplotlib. Install it with 'pip install matplotlib' "
            "(or 'pip install radiant-heat-mapper[viz]')."
        ) from exc

    d = _normalize(layout)
    room_w, room_l = float(d["width"]), float(d["length"])

    fig_w = 8.0
    fig_h = max(2.0, fig_w * (room_l / room_w)) if room_w else 6.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.add_patch(plt.Rectangle((0, 0), room_w, room_l, facecolor="#f4f6f8",
                               edgecolor="#9aa5b1", linewidth=1.5, zorder=0))

    for loop in d["loops"]:
        if len(loop) < 2:
            continue
        supply, ret = _split_supply_return(loop)
        sx, sy = zip(*supply)
        ax.plot(sx, sy, color=SUPPLY_COLOR, linewidth=1.8, zorder=2)
        if ret:
            rx, ry = zip(*ret)
            ax.plot(rx, ry, color=RETURN_COLOR, linewidth=1.8, zorder=2)
        ax.plot(loop[0][0], loop[0][1], "o", color="#1a8917", markersize=5, zorder=3)
        ax.plot(loop[-1][0], loop[-1][1], "o", color="#7048e8", markersize=5, zorder=3)

    for x1, y1, x2, y2 in d["walls"]:
        ax.plot([x1, x2], [y1, y2], color=WALL_COLOR, linewidth=3.5,
                solid_capstyle="projecting", zorder=4)

    for x1, y1, x2, y2 in d["openings"]:
        ax.plot([x1, x2], [y1, y2], color=OPENING_COLOR, linewidth=2.5,
                linestyle=(0, (1, 2)), zorder=5)

    for cx, cy, text in d["labels"]:
        ax.text(cx, cy, text, ha="center", va="center", fontsize=9,
                color="#1f2933", zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))

    # Dimension annotations outside the room.
    margin = max(room_w, room_l) * 0.06
    ax.annotate("", xy=(room_w, -margin), xytext=(0, -margin),
                arrowprops=dict(arrowstyle="<->", color=DIM_COLOR, lw=1))
    ax.text(room_w / 2, -margin * 1.6, f"{room_w:g} m", ha="center", va="top",
            color=DIM_COLOR, fontsize=10)
    ax.annotate("", xy=(-margin, room_l), xytext=(-margin, 0),
                arrowprops=dict(arrowstyle="<->", color=DIM_COLOR, lw=1))
    ax.text(-margin * 1.6, room_l / 2, f"{room_l:g} m", ha="right", va="center",
            rotation=90, color=DIM_COLOR, fontsize=10)

    ax.set_title(d["caption"], fontsize=10)
    ax.set_aspect("equal")
    ax.set_xlim(-margin * 2.5, room_w + margin)
    ax.set_ylim(-margin * 2.5, room_l + margin)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out
