"""Tests for multi-room floor plans (separate loop per room) and PNG rendering."""

import io
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from radiantheat import compute_floor_layout, LayoutError  # noqa: E402
from render import render_svg, render_png  # noqa: E402

APARTMENT = [
    {"name": "Living", "x": 0, "y": 0, "width": 6, "length": 5},
    {"name": "Kitchen", "x": 6, "y": 0, "width": 4, "length": 5},
    {"name": "Bedroom", "x": 0, "y": 5, "width": 6, "length": 4},
    {"name": "Bathroom", "x": 6, "y": 5, "width": 4, "length": 4},
]


def test_floor_has_one_loop_per_room():
    floor = compute_floor_layout(APARTMENT, pipe_spacing=0.2)
    assert floor["totals"]["num_rooms"] == 4
    assert len(floor["rooms"]) == 4
    assert all(len(r["coordinates"]) > 2 for r in floor["rooms"])
    assert floor["floor_width"] == 10
    assert floor["floor_length"] == 9


def test_each_loop_stays_inside_its_room():
    floor = compute_floor_layout(APARTMENT, pipe_spacing=0.2)
    for room in floor["rooms"]:
        x0, y0, w, ln = room["x"], room["y"], room["width"], room["length"]
        for x, y in room["coordinates"]:
            assert x0 < x < x0 + w, f"{room['name']}: x={x} outside room"
            assert y0 < y < y0 + ln, f"{room['name']}: y={y} outside room"


def test_totals_sum_room_values():
    floor = compute_floor_layout(APARTMENT, pipe_spacing=0.2)
    assert floor["totals"]["pipe_length_m"] == pytest.approx(
        sum(r["pipe_length_m"] for r in floor["rooms"]), rel=1e-6)
    assert floor["totals"]["floor_area_m2"] == pytest.approx(
        sum(r["coverage"]["room_area_m2"] for r in floor["rooms"]), rel=1e-6)


def test_shared_interior_wall_is_deduplicated():
    # Two rooms sharing the x=5 edge should not duplicate that wall segment.
    floor = compute_floor_layout(
        [{"x": 0, "y": 0, "width": 5, "length": 4},
         {"x": 5, "y": 0, "width": 5, "length": 4}],
        pipe_spacing=0.2,
    )
    # 4 + 4 edges minus 1 shared = 7 unique walls.
    assert len(floor["walls"]) == 7


def test_floor_is_deterministic():
    assert compute_floor_layout(APARTMENT, 0.2) == compute_floor_layout(APARTMENT, 0.2)


def test_empty_rooms_raises():
    with pytest.raises(LayoutError):
        compute_floor_layout([], pipe_spacing=0.2)


def test_invalid_room_in_floor_raises():
    with pytest.raises(LayoutError):
        compute_floor_layout([{"x": 0, "y": 0, "width": 1.0, "length": 1.0}], pipe_spacing=0.6)


def test_missing_room_field_raises():
    with pytest.raises(LayoutError):
        compute_floor_layout([{"x": 0, "y": 0, "width": 5}], pipe_spacing=0.2)


def test_floor_svg_has_walls_dims_and_multiple_loops():
    svg = render_svg(compute_floor_layout(APARTMENT, 0.2))
    assert svg.count("polyline") >= 8           # >= 2 per room (supply+return)
    assert "Kitchen" in svg and "Bedroom" in svg  # room labels
    assert "10 m" in svg and "9 m" in svg          # overall dimensions
    assert "#222222" in svg                        # wall color present


@pytest.mark.parametrize("layout_factory", [
    lambda: compute_floor_layout(APARTMENT, 0.2),
])
def test_render_png_floor(layout_factory):
    buf = io.BytesIO()
    render_png(layout_factory(), buf)
    data = buf.getvalue()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"   # PNG magic number
    assert len(data) > 1000


def test_render_png_to_path(tmp_path):
    from radiantheat import compute_layout
    out = tmp_path / "room.png"
    render_png(compute_layout(5, 4, 0.2), out)
    assert out.exists()
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


# --- openings / doorways --------------------------------------------------- #

TWO_ROOMS = [
    {"x": 0, "y": 0, "width": 5, "length": 4},
    {"x": 5, "y": 0, "width": 5, "length": 4},
]


def _wall_length(floor):
    return sum(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 for x1, y1, x2, y2 in floor["walls"])


def test_opening_cuts_the_shared_wall():
    plain = compute_floor_layout(TWO_ROOMS, 0.2)
    holed = compute_floor_layout(TWO_ROOMS, 0.2, openings=[[5, 1.5, 5, 2.4]])
    # The shared wall is split into two pieces, total wall length drops by ~0.9 m.
    assert len(holed["walls"]) == len(plain["walls"]) + 1
    assert _wall_length(plain) - _wall_length(holed) == pytest.approx(0.9, abs=1e-6)
    assert holed["openings"] == [[5.0, 1.5, 5.0, 2.4]]


def test_opening_accepts_dict_form():
    floor = compute_floor_layout(TWO_ROOMS, 0.2,
                                 openings=[{"x1": 5, "y1": 1.5, "x2": 5, "y2": 2.4}])
    assert floor["openings"] == [[5.0, 1.5, 5.0, 2.4]]


def test_per_room_openings_are_merged():
    rooms = [dict(TWO_ROOMS[0], openings=[[5, 1.0, 5, 1.9]]), TWO_ROOMS[1]]
    floor = compute_floor_layout(rooms, 0.2)
    assert floor["openings"] == [[5.0, 1.0, 5.0, 1.9]]


def test_opening_off_any_wall_leaves_walls_unchanged():
    plain = compute_floor_layout(TWO_ROOMS, 0.2)
    floor = compute_floor_layout(TWO_ROOMS, 0.2, openings=[[2, 2, 3, 2]])  # mid-room, no wall
    assert len(floor["walls"]) == len(plain["walls"])


def test_floor_svg_draws_openings():
    svg = render_svg(compute_floor_layout(TWO_ROOMS, 0.2, openings=[[5, 1.5, 5, 2.4]]))
    assert "#b9a06a" in svg  # opening threshold color


def test_invalid_opening_raises():
    with pytest.raises(LayoutError):
        compute_floor_layout(TWO_ROOMS, 0.2, openings=[[5, 1.5, 5]])
