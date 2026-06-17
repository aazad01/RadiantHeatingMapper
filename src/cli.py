"""Unified command-line entrypoint for the radiant heating tools.

This module powers both the pip-installed ``radiant-heat`` console script and
the standalone PyInstaller executable. It exposes three subcommands:

    radiant-heat compute --length 10 --width 10 --spacing 1   # print JSON layout
    radiant-heat svg --length 10 --width 10 -o layout.svg      # write an SVG file
    radiant-heat serve --port 8000                             # run the HTTP API

A separate ``show`` subcommand launches the interactive matplotlib visualizer
when matplotlib is available.
"""

import argparse
import json
import sys
from pathlib import Path

# Support running both as an installed module and as a frozen/script file.
sys.path.append(str(Path(__file__).resolve().parent))

from radiantheat import compute_layout, LayoutError  # noqa: E402
from render import render_svg  # noqa: E402


def _add_layout_args(parser):
    parser.add_argument("--length", "-l", type=float, required=True,
                        help="Room length in meters (Y dimension).")
    parser.add_argument("--width", "-w", type=float, required=True,
                        help="Room width in meters (X dimension).")
    parser.add_argument("--spacing", "-s", type=float, default=0.2,
                        help="Spacing between pipe runs in meters (default: 0.2).")


def _cmd_compute(args):
    layout = compute_layout(args.length, args.width, args.spacing)
    print(json.dumps(layout, indent=2))
    return 0


def _cmd_svg(args):
    layout = compute_layout(args.length, args.width, args.spacing)
    svg = render_svg(layout, width_px=args.width_px)
    if args.output and args.output != "-":
        Path(args.output).write_text(svg, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        sys.stdout.write(svg)
    return 0


def _cmd_serve(args):
    from api import create_app
    app = create_app()
    print(f"Serving radiant heating API on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def _cmd_show(args):
    try:
        from radiantheat import radiant_heating_layout
    except ImportError as exc:  # pragma: no cover - defensive
        print(f"Visualization unavailable: {exc}", file=sys.stderr)
        return 1
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        print("The 'show' command requires matplotlib. Install it with "
              "'pip install matplotlib', or use 'compute'/'svg' instead.",
              file=sys.stderr)
        return 1
    ok = radiant_heating_layout(args.length, args.width, args.spacing)
    return 0 if ok else 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="radiant-heat",
        description="Generate and serve radiant heating pipe layouts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_compute = sub.add_parser("compute", help="Compute a layout and print JSON.")
    _add_layout_args(p_compute)
    p_compute.set_defaults(func=_cmd_compute)

    p_svg = sub.add_parser("svg", help="Render a layout as an SVG image.")
    _add_layout_args(p_svg)
    p_svg.add_argument("--output", "-o", default="-",
                       help="Output file path, or '-' for stdout (default).")
    p_svg.add_argument("--width-px", type=int, default=640,
                       help="SVG drawing width in pixels (default: 640).")
    p_svg.set_defaults(func=_cmd_svg)

    p_serve = sub.add_parser("serve", help="Run the HTTP API server.")
    p_serve.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0).")
    p_serve.add_argument("--port", "-p", type=int, default=8000, help="Bind port (default: 8000).")
    p_serve.add_argument("--debug", action="store_true", help="Enable Flask debug mode.")
    p_serve.set_defaults(func=_cmd_serve)

    p_show = sub.add_parser("show", help="Open the interactive matplotlib visualizer.")
    _add_layout_args(p_show)
    p_show.set_defaults(func=_cmd_show)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except LayoutError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
