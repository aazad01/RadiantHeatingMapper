"""Minimal demonstration of using the layout engine as a library.

    python examples/usage.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from radiantheat import compute_layout  # noqa: E402
from render import render_svg  # noqa: E402


def main():
    # A 5 m x 4 m bedroom with 200 mm pipe spacing.
    layout = compute_layout(room_length=5.0, room_width=4.0, pipe_spacing=0.2)

    print(f"Room:        {layout['room_width']} x {layout['room_length']} m")
    print(f"Spacing:     {layout['pipe_spacing']} m")
    print(f"Pipe length: {layout['pipe_length_m']} m")
    print(f"Coverage:    {layout['coverage']['coverage_percent']} %")
    print(f"Path points: {len(layout['coordinates'])}")
    print(f"First 3 pts: {layout['coordinates'][:3]}")

    # Render and save an SVG of the layout.
    out = Path(__file__).resolve().parent / "bedroom_usage.svg"
    out.write_text(render_svg(layout), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
