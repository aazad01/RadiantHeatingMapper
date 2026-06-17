"""HTTP API for the radiant heating layout generator.

A small Flask application that exposes the layout engine so other services
(and a built-in browser UI) can request pipe layouts over HTTP.

Endpoints:
    GET  /                 Interactive HTML UI.
    GET  /health           Liveness/readiness probe.
    GET  /openapi.json     Machine-readable OpenAPI 3.0 description.
    GET  /api/layout       Compute a layout from query parameters.
    POST /api/layout       Compute a layout from a JSON body.
    GET  /api/layout.svg   Render a layout as an SVG image.

Run locally:
    python src/api.py            # http://127.0.0.1:8000
    gunicorn 'api:create_app()'  # production WSGI server
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, Response

# Allow running as a script (``python src/api.py``) as well as a module.
sys.path.append(str(Path(__file__).resolve().parent))

from radiantheat import compute_layout, LayoutError  # noqa: E402
from render import render_svg  # noqa: E402

DEFAULT_SPACING = 0.2


def _parse_params(source):
    """Extract and coerce layout parameters from a dict-like source.

    Returns a tuple ``(room_length, room_width, pipe_spacing)``.
    Raises ``ValueError`` (with a friendly message) on missing/invalid values.
    """
    def num(name, required=True, default=None):
        if name not in source or source.get(name) in (None, ""):
            if required:
                raise ValueError(f"Missing required parameter: '{name}'")
            return default
        try:
            return float(source.get(name))
        except (TypeError, ValueError):
            raise ValueError(f"Parameter '{name}' must be a number")

    room_length = num("room_length")
    room_width = num("room_width")
    pipe_spacing = num("pipe_spacing", required=False, default=DEFAULT_SPACING)
    return room_length, room_width, pipe_spacing


def _layout_from_request():
    """Build a layout from the current Flask request (JSON body or query)."""
    if request.method == "POST":
        source = request.get_json(silent=True)
        if source is None:
            # Fall back to form data so curl --data works without a JSON header.
            source = request.form.to_dict() or {}
    else:
        source = request.args.to_dict()

    room_length, room_width, pipe_spacing = _parse_params(source)
    return compute_layout(room_length, room_width, pipe_spacing)


def create_app():
    """Application factory. Returns a configured Flask app."""
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/layout", methods=["GET", "POST"])
    def api_layout():
        try:
            layout = _layout_from_request()
        except LayoutError as exc:
            return jsonify({"error": str(exc)}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(layout)

    @app.get("/api/layout.svg")
    def api_layout_svg():
        try:
            layout = _layout_from_request()
        except LayoutError as exc:
            return jsonify({"error": str(exc)}), 422
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        try:
            width_px = int(request.args.get("width", 640))
        except (TypeError, ValueError):
            width_px = 640
        svg = render_svg(layout, width_px=max(200, min(width_px, 2000)))
        return Response(svg, mimetype="image/svg+xml")

    @app.get("/openapi.json")
    def openapi():
        return jsonify(_OPENAPI_SPEC)

    @app.get("/")
    def index():
        return Response(_INDEX_HTML, mimetype="text/html")

    return app


_OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Radiant Heating Layout API",
        "version": "1.0.0",
        "description": "Compute serpentine radiant heating pipe layouts for rectangular rooms.",
    },
    "paths": {
        "/api/layout": {
            "get": {
                "summary": "Compute a layout (query parameters)",
                "parameters": [
                    {"name": "room_length", "in": "query", "required": True,
                     "schema": {"type": "number"}, "description": "Room length in meters."},
                    {"name": "room_width", "in": "query", "required": True,
                     "schema": {"type": "number"}, "description": "Room width in meters."},
                    {"name": "pipe_spacing", "in": "query", "required": False,
                     "schema": {"type": "number", "default": DEFAULT_SPACING},
                     "description": "Spacing between pipe runs in meters."},
                ],
                "responses": {
                    "200": {"description": "Computed layout",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Layout"}}}},
                    "400": {"description": "Invalid parameters"},
                    "422": {"description": "Room too small / unprocessable"},
                },
            },
            "post": {
                "summary": "Compute a layout (JSON body)",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LayoutRequest"}}},
                },
                "responses": {
                    "200": {"description": "Computed layout",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Layout"}}}},
                    "400": {"description": "Invalid parameters"},
                    "422": {"description": "Room too small / unprocessable"},
                },
            },
        },
        "/api/layout.svg": {
            "get": {
                "summary": "Render a layout as SVG",
                "parameters": [
                    {"name": "room_length", "in": "query", "required": True, "schema": {"type": "number"}},
                    {"name": "room_width", "in": "query", "required": True, "schema": {"type": "number"}},
                    {"name": "pipe_spacing", "in": "query", "required": False, "schema": {"type": "number"}},
                    {"name": "width", "in": "query", "required": False, "schema": {"type": "integer"}},
                ],
                "responses": {"200": {"description": "SVG image",
                                      "content": {"image/svg+xml": {}}}},
            }
        },
        "/health": {"get": {"summary": "Health check",
                            "responses": {"200": {"description": "Service healthy"}}}},
    },
    "components": {
        "schemas": {
            "LayoutRequest": {
                "type": "object",
                "required": ["room_length", "room_width"],
                "properties": {
                    "room_length": {"type": "number"},
                    "room_width": {"type": "number"},
                    "pipe_spacing": {"type": "number", "default": DEFAULT_SPACING},
                },
            },
            "Layout": {
                "type": "object",
                "properties": {
                    "room_length": {"type": "number"},
                    "room_width": {"type": "number"},
                    "pipe_spacing": {"type": "number"},
                    "coordinates": {"type": "array", "items": {
                        "type": "array", "items": {"type": "number"}}},
                    "grid": {"type": "object"},
                    "pipe_length_m": {"type": "number"},
                    "coverage": {"type": "object"},
                    "warnings": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    },
}


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Radiant Heating Layout</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 0; background: #f4f6f8; color: #1f2933; }
  header { background: #1f2933; color: #fff; padding: 1rem 1.5rem; }
  header h1 { margin: 0; font-size: 1.25rem; }
  main { max-width: 920px; margin: 1.5rem auto; padding: 0 1rem; }
  form { background: #fff; padding: 1rem 1.25rem; border-radius: 8px; display: flex;
         gap: 1rem; flex-wrap: wrap; align-items: flex-end; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  label { display: flex; flex-direction: column; font-size: .85rem; color: #52606d; gap: .25rem; }
  input { padding: .45rem .5rem; border: 1px solid #cbd2d9; border-radius: 6px; width: 8rem; }
  button { padding: .55rem 1.1rem; background: #2f6fd0; color: #fff; border: 0;
           border-radius: 6px; cursor: pointer; font-size: .95rem; }
  button:hover { background: #275fb0; }
  #result { margin-top: 1.25rem; background: #fff; border-radius: 8px; padding: 1rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  #stats { display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
  .stat b { display: block; font-size: 1.3rem; }
  .stat span { color: #52606d; font-size: .8rem; }
  svg { max-width: 100%; height: auto; border: 1px solid #e4e7eb; border-radius: 6px; }
  .err { color: #cf1124; }
  a { color: #2f6fd0; }
</style>
</head>
<body>
<header><h1>Radiant Heating Layout Generator</h1></header>
<main>
  <form id="f">
    <label>Room length (m)<input id="room_length" type="number" step="any" value="10"/></label>
    <label>Room width (m)<input id="room_width" type="number" step="any" value="10"/></label>
    <label>Pipe spacing (m)<input id="pipe_spacing" type="number" step="any" value="1"/></label>
    <button type="submit">Generate</button>
  </form>
  <div id="result"></div>
  <p style="color:#7b8794;font-size:.85rem">
    API: <code>GET /api/layout</code>, <code>POST /api/layout</code>,
    <code>GET /api/layout.svg</code> &middot;
    <a href="/openapi.json">OpenAPI spec</a>
  </p>
</main>
<script>
const f = document.getElementById('f');
const result = document.getElementById('result');
async function run(e) {
  if (e) e.preventDefault();
  const p = new URLSearchParams({
    room_length: document.getElementById('room_length').value,
    room_width: document.getElementById('room_width').value,
    pipe_spacing: document.getElementById('pipe_spacing').value,
  });
  result.innerHTML = 'Computing…';
  try {
    const res = await fetch('/api/layout?' + p.toString());
    const data = await res.json();
    if (!res.ok) { result.innerHTML = '<p class="err">' + (data.error || 'Error') + '</p>'; return; }
    const c = data.coverage;
    const warn = (data.warnings && data.warnings.length)
      ? '<p class="err">' + data.warnings.join(' ') + '</p>' : '';
    result.innerHTML =
      '<div id="stats">' +
      '<div class="stat"><b>' + data.pipe_length_m + ' m</b><span>Pipe length</span></div>' +
      '<div class="stat"><b>' + c.coverage_percent + '%</b><span>Coverage</span></div>' +
      '<div class="stat"><b>' + c.room_area_m2 + ' m²</b><span>Room area</span></div>' +
      '<div class="stat"><b>' + data.coordinates.length + '</b><span>Path points</span></div>' +
      '</div>' + warn +
      '<img alt="layout" src="/api/layout.svg?' + p.toString() + '&width=820"/>';
  } catch (err) {
    result.innerHTML = '<p class="err">' + err + '</p>';
  }
}
f.addEventListener('submit', run);
run();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    create_app().run(host="0.0.0.0", port=port, debug=False)
