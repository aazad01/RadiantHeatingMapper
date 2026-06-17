"""Real-world scenario tests across a range of room sizes and pipe spacings.

These validate structural invariants the layout must satisfy for any room
(grid alignment, axis-aligned uniform steps, pipes inside the walls, sane pipe
length and coverage) rather than hard-coded coordinate dumps, so they exercise
many realistic configurations at once.
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from radiantheat import compute_layout, LayoutError  # noqa: E402
from render import render_svg  # noqa: E402

# name, room_length (m), room_width (m), pipe_spacing (m)
ROOMS = [
    ("bathroom", 3.0, 2.0, 0.15),
    ("bedroom", 5.0, 4.0, 0.20),
    ("kitchen", 5.0, 3.5, 0.15),
    ("living_room", 8.0, 6.0, 0.20),
    ("open_plan", 12.0, 9.0, 0.25),
    ("hallway", 8.0, 1.6, 0.15),
    ("warehouse_750m2", 30.0, 25.0, 0.30),
    ("square_small", 4.0, 4.0, 0.20),
    ("wide_shallow", 4.0, 12.0, 0.30),
    ("locked_10x10", 10.0, 10.0, 1.0),
]
ROOM_IDS = [r[0] for r in ROOMS]


@pytest.mark.parametrize("name,length,width,spacing", ROOMS, ids=ROOM_IDS)
def test_layout_invariants(name, length, width, spacing):
    layout = compute_layout(length, width, spacing)
    coords = layout["coordinates"]
    grid = layout["grid"]

    # A usable serpentine needs several points.
    assert len(coords) >= 4

    # Every point lies on a grid line.
    xs = {round(x, 6) for x in grid["x_positions"]}
    ys = {round(y, 6) for y in grid["y_positions"]}
    for x, y in coords:
        assert round(x, 6) in xs, f"{name}: x={x} off-grid"
        assert round(y, 6) in ys, f"{name}: y={y} off-grid"

    # Each step is axis-aligned (no diagonals) and exactly one pipe-spacing long.
    for (x0, y0), (x1, y1) in zip(coords, coords[1:]):
        dx, dy = x1 - x0, y1 - y0
        assert math.isclose(dx, 0, abs_tol=1e-9) or math.isclose(dy, 0, abs_tol=1e-9), \
            f"{name}: diagonal segment {(x0, y0)}->{(x1, y1)}"
        assert math.isclose(math.hypot(dx, dy), spacing, rel_tol=1e-6, abs_tol=1e-9), \
            f"{name}: step length != spacing at {(x0, y0)}->{(x1, y1)}"

    # Pipe stays strictly inside the room, one spacing in from the nearest walls.
    assert all(0 < x < width for x, _ in coords)
    assert all(0 < y < length for _, y in coords)
    assert math.isclose(min(x for x, _ in coords), spacing, abs_tol=1e-9)
    assert math.isclose(min(y for _, y in coords), spacing, abs_tol=1e-9)

    # Reported pipe length equals the number of unit steps times the spacing.
    assert math.isclose(layout["pipe_length_m"], (len(coords) - 1) * spacing, rel_tol=1e-6)


@pytest.mark.parametrize("name,length,width,spacing", ROOMS, ids=ROOM_IDS)
def test_coverage_and_density_are_realistic(name, length, width, spacing):
    layout = compute_layout(length, width, spacing)
    cov = layout["coverage"]

    assert 0 < cov["coverage_percent"] <= 100
    assert cov["covered_area_m2"] < cov["room_area_m2"]

    # Pipe per covered m² should be close to 1/spacing (serpentine of parallel
    # runs spaced `spacing` apart), allowing for return-leg/turn overhead.
    density = layout["pipe_length_m"] / cov["covered_area_m2"]
    assert (0.85 / spacing) <= density <= (1.7 / spacing), \
        f"{name}: implausible density {density:.3f} m/m² for spacing {spacing}"


@pytest.mark.parametrize("name,length,width,spacing", ROOMS, ids=ROOM_IDS)
def test_svg_renders_for_each_room(name, length, width, spacing):
    svg = render_svg(compute_layout(length, width, spacing))
    assert svg.startswith("<svg")
    assert "polyline" in svg
    assert svg.rstrip().endswith("</svg>")


def test_tighter_spacing_uses_more_pipe():
    """For the same room, halving the spacing should substantially increase pipe."""
    loose = compute_layout(8.0, 6.0, 0.30)["pipe_length_m"]
    tight = compute_layout(8.0, 6.0, 0.15)["pipe_length_m"]
    assert tight > loose * 1.5


def test_results_are_deterministic():
    a = compute_layout(8.0, 6.0, 0.2)
    b = compute_layout(8.0, 6.0, 0.2)
    assert a == b


def test_large_room_is_handled():
    """A 750 m² slab should still produce a dense, valid layout."""
    layout = compute_layout(30.0, 25.0, 0.30)
    assert layout["coverage"]["room_area_m2"] == 750.0
    assert len(layout["coordinates"]) > 1000
    assert layout["pipe_length_m"] > 1000


@pytest.mark.parametrize("length,width,spacing", [
    (0.4, 0.4, 0.2),   # room barely larger than two offsets
    (1.0, 1.0, 0.6),   # spacing too large for the room
    (2.0, 2.0, 1.0),   # spacing == half the smallest dimension (invalid)
])
def test_rooms_too_small_raise(length, width, spacing):
    with pytest.raises(LayoutError):
        compute_layout(length, width, spacing)


def test_negative_and_zero_inputs_raise():
    for args in [(0, 5, 0.2), (5, 0, 0.2), (5, 5, 0), (-3, 5, 0.2)]:
        with pytest.raises(LayoutError):
            compute_layout(*args)
