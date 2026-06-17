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
./dist/radiant-heat serve --port 8000                            # run the HTTP API
```

CI also builds the Linux binary on every run and publishes it as the
`radiant-heat-linux-x86_64` artifact. The bundled binary excludes matplotlib to
stay small; the interactive `show` command works from a source checkout with
`pip install -e '.[viz]'`.

If you prefer a pip-installed command instead of a frozen binary:

```bash
pip install -e .
radiant-heat compute --length 10 --width 10 --spacing 1
```

### Web API

Start the service:

```bash
python src/api.py                       # http://127.0.0.1:8000
# or, for production:
pip install gunicorn
gunicorn --chdir src 'api:create_app()'
```

Open `http://127.0.0.1:8000/` for the browser UI, or call the API from another service:

| Method & path        | Description                                  |
| -------------------- | -------------------------------------------- |
| `GET /health`        | Health/readiness probe                       |
| `GET /api/layout`    | Compute a layout from query parameters       |
| `POST /api/layout`   | Compute a layout from a JSON body            |
| `GET /api/layout.svg`| Render a layout as an SVG image              |
| `GET /openapi.json`  | Machine-readable OpenAPI 3.0 description      |

```bash
# Query parameters
curl "http://127.0.0.1:8000/api/layout?room_length=10&room_width=10&pipe_spacing=1"

# JSON body
curl -X POST http://127.0.0.1:8000/api/layout \
  -H 'Content-Type: application/json' \
  -d '{"room_length": 10, "room_width": 10, "pipe_spacing": 1}'

# SVG image
curl "http://127.0.0.1:8000/api/layout.svg?room_length=10&room_width=10&pipe_spacing=1" -o layout.svg
```

`pipe_spacing` is optional and defaults to `0.2`. The API returns `400` for
missing/invalid parameters and `422` when the room is too small for the
requested spacing.

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
Total pipe length: 77.00m
Pipe length per m² of room: 0.77m/m²
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

## Testing

Run the full test suite from the repository root:
```bash
python -m pytest tests/ -v
```

CI runs the same suite (with coverage) on every push and pull request across
Python 3.9–3.12 via `.github/workflows/ci.yml`.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 