# Radiant Heating Layout Generator

[![CI](https://github.com/aazad01/RadiantHeatingMapper/actions/workflows/ci.yml/badge.svg)](https://github.com/aazad01/RadiantHeatingMapper/actions/workflows/ci.yml)

This project generates and visualizes radiant heating pipe layouts for rooms. It creates an efficient serpentine pattern that ensures even heat distribution while minimizing pipe length, and exposes the layout engine three ways: a structured Python API, a command-line visualizer, and an HTTP service other applications can call.

## Features

- Serpentine pipe-path planning with total pipe length and coverage statistics
- Structured `compute_layout()` function returning JSON-serializable results
- **HTTP API** (Flask) so other services can request layouts over the network
- Dependency-free SVG rendering of layouts (no display backend required)
- Interactive matplotlib visualization with animated installation (rooms < 600m²) or static layout (larger rooms)
- Browser UI for quick experimentation
- Continuous integration running the test suite across Python 3.9–3.12

## Project Structure

```
RadiantHeatingMapper/
├── src/
│   ├── radiantheat.py        # Core geometry + matplotlib CLI visualizer
│   ├── render.py             # Dependency-free SVG renderer
│   └── api.py                # Flask HTTP API + browser UI
├── tests/
│   ├── test_radiantheat.py   # Geometry unit tests
│   ├── test_compute_layout.py# compute_layout()/SVG tests
│   ├── test_api.py           # HTTP API tests
│   └── test_coordinates.json # Test data
├── .github/workflows/ci.yml  # CI pipeline
├── requirements.txt          # Dependencies
└── README.md                 # Documentation
```

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Command-line visualizer

```bash
python src/radiantheat.py
```

You will be prompted to enter:
- Room length (in meters)
- Room width (in meters)
- Pipe spacing (in meters, typically 0.2)

### Python library

```python
from radiantheat import compute_layout

layout = compute_layout(room_length=10, room_width=10, pipe_spacing=1.0)
print(layout["pipe_length_m"])          # 71.0
print(layout["coverage"]["coverage_percent"])  # 64.0
print(layout["coordinates"][:3])        # [[1.0, 1.0], [1.0, 2.0], [1.0, 3.0]]
```

### Standalone executable

Build a self-contained binary (no Python install required to run it):

```bash
./build_executable.sh        # produces dist/radiant-heat
```

The executable exposes the same engine via subcommands:

```bash
./dist/radiant-heat compute --length 10 --width 10 --spacing 1   # print JSON layout
./dist/radiant-heat svg --length 10 --width 10 -o layout.svg     # write an SVG file
./dist/radiant-heat png --length 10 --width 10 -o layout.png     # write a PNG file (needs matplotlib)
./dist/radiant-heat floor --rooms-file floor.json --png -o floor.png  # multi-room floor plan
./dist/radiant-heat serve --port 8000                            # run the HTTP API
```

The `floor` subcommand reads rooms as JSON (a list of `{name, x, y, width, length}`
or a `{"rooms": [...], "pipe_spacing": n}` object) and generates a separate
serpentine loop per room with interior walls drawn between them.

PyInstaller binaries are **platform-specific** — a Linux build will not run on
Windows or macOS. CI therefore builds a native binary for each OS on every run
and publishes them as downloadable artifacts:

| OS | Artifact | File |
| -- | -------- | ---- |
| Windows | `radiant-heat-windows-x86_64` | `radiant-heat.exe` |
| macOS (Apple Silicon) | `radiant-heat-macos-arm64` | `radiant-heat` |
| Linux | `radiant-heat-linux-x86_64` | `radiant-heat` |

Download the one matching your OS from the workflow run's **Artifacts** section.
The bundled binary excludes matplotlib to stay small; the interactive `show`
command works from a source checkout with `pip install -e '.[viz]'`.

If you prefer a pip-installed command instead of a frozen binary:

```bash
pip install -e .
radiant-heat compute --length 10 --width 10 --spacing 1
```

### Docker

The most portable option — runs identically on Windows, macOS and Linux with
Docker Desktop, with no platform-specific binary to worry about:

```bash
docker build -t radiant-heat .

# Serve the API/UI on http://localhost:8000
docker run --rm -p 8000:8000 radiant-heat

# Or run the CLI directly
docker run --rm radiant-heat compute --length 10 --width 10 --spacing 1
```

On pushes to the default branch, CI also publishes the image to GitHub
Container Registry, so you can skip the build and pull it directly:

```bash
docker pull ghcr.io/aazad01/radiantheatingmapper:latest
docker run --rm -p 8000:8000 ghcr.io/aazad01/radiantheatingmapper:latest
```

## Front end

A browser front end lives in [`web/index.html`](web/index.html). It supports both
single rooms and multi-room **floor plans** (with editable rooms and doorway
openings), renders the layout inline, shows pipe-length/coverage stats, and can
download the drawing as SVG or PNG.

The running server serves it at its root:

```bash
docker run --rm -p 8000:8000 radiant-heat   # then open http://localhost:8000
# or, from source:
python src/api.py
```

### Deploying the front end separately (GitHub Pages)

`web/` is a static, dependency-free page, so it can also be hosted on its own.
The included workflow [`.github/workflows/pages.yml`](.github/workflows/pages.yml)
publishes it to GitHub Pages on pushes to `main` (enable Pages → "GitHub Actions"
in the repo settings). Because the page and API are then on different origins:

- The API sends CORS headers (`Access-Control-Allow-Origin`, configurable via the
  `RADIANT_CORS_ORIGIN` env var, default `*`), so cross-origin calls work.
- In the page's **Backend settings**, set the **API base URL** to wherever the
  API is hosted (e.g. your Docker/GHCR deployment). It is saved in the browser.

When the front end is served by the API itself (Docker/`serve`), the API base
can stay blank — calls go to the same origin automatically.

### Web API

Start the service:

```bash
python src/api.py                       # http://127.0.0.1:8000
# or, for production:
pip install gunicorn
gunicorn --chdir src 'api:create_app()'
```

Open `http://127.0.0.1:8000/` for the browser UI, or call the API from another service:

| Method & path         | Description                                          |
| --------------------- | ---------------------------------------------------- |
| `GET /health`         | Health/readiness probe                               |
| `GET`/`POST /api/layout` | Compute a single-room layout (query or JSON body) |
| `GET /api/layout.svg` | Render a single room as SVG (with dimensions)        |
| `GET /api/layout.png` | Render a single room as PNG (needs matplotlib)       |
| `POST /api/floor`     | Compute a multi-room floor plan (loop per room)      |
| `POST /api/floor.svg` | Render a floor plan as SVG (walls + dimensions)      |
| `POST /api/floor.png` | Render a floor plan as PNG (needs matplotlib)        |
| `GET /openapi.json`   | Machine-readable OpenAPI 3.0 description              |

```bash
# Single room (query parameters)
curl "http://127.0.0.1:8000/api/layout?room_length=10&room_width=10&pipe_spacing=1"

# Single room as an annotated SVG (recommended for dynamic web rendering)
curl "http://127.0.0.1:8000/api/layout.svg?room_length=10&room_width=10&pipe_spacing=1" -o layout.svg

# Multi-room floor plan: one serpentine loop per room, interior walls drawn,
# with doorway openings cut out of the walls.
curl -X POST http://127.0.0.1:8000/api/floor \
  -H 'Content-Type: application/json' \
  -d '{"pipe_spacing": 0.2,
       "rooms": [
        {"name": "Living",  "x": 0, "y": 0, "width": 6, "length": 5},
        {"name": "Kitchen", "x": 6, "y": 0, "width": 4, "length": 5}
       ],
       "openings": [[6, 2.0, 6, 2.9]]}'

# ...and the same floor plan as an SVG drawing
curl -X POST "http://127.0.0.1:8000/api/floor.svg" \
  -H 'Content-Type: application/json' \
  -d '{"rooms": [{"x":0,"y":0,"width":6,"length":5},{"x":6,"y":0,"width":4,"length":5}]}' \
  -o floor.svg
```

`pipe_spacing` is optional and defaults to `0.2`. The API returns `400` for
missing/invalid parameters and `422` when a room is too small for the requested
spacing. Drawings include **dimension annotations**; floor plans also draw **interior
walls** between rooms and **doorway openings** (passed as `openings` — segments
`[x1, y1, x2, y2]` in floor coordinates, or per-room `openings`) that are cut
out of the walls as gaps. SVG is served directly (no rendering dependency —
best for the web); PNG endpoints require matplotlib and return `501` in builds
without it (e.g. the slim Docker image).

### Example Output

For a 10x10 room with 1m spacing:

```
Grid Information:
Vertical lines: 8
Horizontal lines: 8
Grid spacing: 1.0m

Coverage Information:
Room area: 100.00m²
Covered area: 64.00m²
Coverage percentage: 64.0%

Pipe Information:
Total pipe length: 71.00m
Pipe length per m² of room: 0.71m/m²
```

### Visualization

The script provides two types of visualizations:

1. **Animated Installation (Rooms < 600m²)**
   
   ![Animated Installation](https://raw.githubusercontent.com/aazad01/RadiantHeatingMapper/main/docs/images/animation_example.gif)

   Shows the pipe being installed in real-time with:
   - Red → Yellow gradient for supply line
   - Blue gradient for return line
   - Installation point tracker
   - Progress percentage

2. **Static Layout (Rooms ≥ 600m²)**
   
   ![Static Layout](https://raw.githubusercontent.com/aazad01/RadiantHeatingMapper/main/docs/images/static_example.png)

   Shows the complete layout with:
   - Red line for supply
   - Blue line for return
   - Grid overlay
   - Room boundaries

## Examples

The [`examples/`](examples/) directory contains runnable demonstrations:

- [`examples/usage.py`](examples/usage.py) — using the engine as a Python library.
- [`examples/api_requests.sh`](examples/api_requests.sh) — calling the HTTP API with `curl`.
- [`examples/generate_gallery.py`](examples/generate_gallery.py) — renders a gallery of
  layouts for realistic rooms (bathroom, bedroom, living room, hallway, warehouse, …).

A pre-rendered gallery with pipe-length and coverage figures for each room is in
[`examples/README.md`](examples/README.md). Regenerate it with:

```bash
python examples/generate_gallery.py
```

> **Edge offset:** the first and last pipe runs sit one pipe-spacing in from the
> walls, so coverage scales sensibly with the chosen spacing for rooms of any size.

## Testing

Run the full test suite from the repository root:
```bash
python -m pytest tests/ -v
```

`tests/test_real_world.py` exercises a range of realistic room sizes and pipe
spacings, asserting structural invariants (grid alignment, uniform axis-aligned
steps, pipes inside the walls, plausible pipe length and coverage).

CI runs the same suite (with coverage) on every push and pull request across
Python 3.9–3.12 via `.github/workflows/ci.yml`.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 