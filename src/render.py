"""Lightweight SVG rendering of radiant heating layouts.

This module renders the dictionary produced by
:func:`radiantheat.compute_layout` into an SVG image. It is intentionally
dependency-free (pure string building) so the web API can return a visual
representation without pulling in matplotlib or a display backend.
"""

from xml.sax.saxutils import escape


def render_svg(layout, width_px=640, padding_px=40):
    """Render a layout dict as an SVG document string.

    Args:
        layout: The dict returned by :func:`radiantheat.compute_layout`.
        width_px: Target width of the drawing area in pixels. The height is
            derived from the room aspect ratio.
        padding_px: Padding around the room, in pixels.

    Returns:
        A string containing a complete SVG document.
    """
    room_w = float(layout["room_width"])
    room_l = float(layout["room_length"])
    coords = layout["coordinates"]
    grid = layout["grid"]

    # Scale so the room fits within width_px (minus padding). Use a uniform
    # scale for both axes to preserve aspect ratio.
    draw_w = max(width_px - 2 * padding_px, 1)
    scale = draw_w / room_w if room_w else 1
    draw_h = room_l * scale

    svg_w = draw_w + 2 * padding_px
    svg_h = draw_h + 2 * padding_px

    def tx(x):
        return padding_px + x * scale

    def ty(y):
        # Flip Y so that 0 is at the bottom (room coordinates are bottom-left
        # origin, SVG is top-left origin).
        return padding_px + (room_l - y) * scale

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w:.1f}" '
        f'height="{svg_h:.1f}" viewBox="0 0 {svg_w:.1f} {svg_h:.1f}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        # Room outline
        f'<rect x="{tx(0):.2f}" y="{ty(room_l):.2f}" width="{room_w*scale:.2f}" '
        f'height="{room_l*scale:.2f}" fill="#f4f6f8" stroke="#9aa5b1" '
        'stroke-width="1.5"/>',
    ]

    # Grid lines
    for gx in grid["x_positions"]:
        parts.append(
            f'<line x1="{tx(gx):.2f}" y1="{ty(0):.2f}" x2="{tx(gx):.2f}" '
            f'y2="{ty(room_l):.2f}" stroke="#d9dee3" stroke-width="0.5" '
            'stroke-dasharray="2,3"/>'
        )
    for gy in grid["y_positions"]:
        parts.append(
            f'<line x1="{tx(0):.2f}" y1="{ty(gy):.2f}" x2="{tx(room_w):.2f}" '
            f'y2="{ty(gy):.2f}" stroke="#d9dee3" stroke-width="0.5" '
            'stroke-dasharray="2,3"/>'
        )

    # Pipe path. Split into supply (first half) and return (second half) so the
    # flow direction is visible, mirroring the matplotlib visualization.
    if len(coords) >= 2:
        half = len(coords) // 2
        supply_pts = " ".join(f"{tx(x):.2f},{ty(y):.2f}" for x, y in coords[: half + 1])
        return_pts = " ".join(f"{tx(x):.2f},{ty(y):.2f}" for x, y in coords[half:])
        parts.append(
            f'<polyline points="{supply_pts}" fill="none" stroke="#e8513b" '
            'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        parts.append(
            f'<polyline points="{return_pts}" fill="none" stroke="#2f6fd0" '
            'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )

        # Start and end markers
        sx, sy = coords[0]
        ex, ey = coords[-1]
        parts.append(f'<circle cx="{tx(sx):.2f}" cy="{ty(sy):.2f}" r="5" fill="#1a8917"/>')
        parts.append(f'<circle cx="{tx(ex):.2f}" cy="{ty(ey):.2f}" r="5" fill="#7048e8"/>')

    # Caption
    caption = (
        f"{room_w:g}m x {room_l:g}m  |  spacing {layout['pipe_spacing']:g}m  |  "
        f"pipe {layout['pipe_length_m']:g}m  |  coverage "
        f"{layout['coverage']['coverage_percent']:g}%"
    )
    parts.append(
        f'<text x="{padding_px}" y="{svg_h - 12:.1f}" font-family="sans-serif" '
        f'font-size="13" fill="#52606d">{escape(caption)}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)
