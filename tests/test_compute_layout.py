"""Tests for the structured compute_layout() entry point and SVG renderer."""

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from radiantheat import compute_layout, LayoutError  # noqa: E402
from render import render_svg  # noqa: E402


class TestComputeLayout(unittest.TestCase):
    def test_structure_and_values(self):
        layout = compute_layout(10.0, 10.0, 1.0)

        # Top-level keys
        for key in ("room_length", "room_width", "pipe_spacing", "coordinates",
                    "grid", "pipe_length_m", "coverage", "warnings"):
            self.assertIn(key, layout)

        # Matches the known 10x10 / 1m result used elsewhere in the suite.
        self.assertEqual(len(layout["coordinates"]), 72)
        self.assertAlmostEqual(layout["pipe_length_m"], 71.0, places=2)
        self.assertAlmostEqual(layout["coverage"]["coverage_percent"], 64.0, places=1)

        # Coordinates are JSON-friendly [x, y] pairs.
        self.assertTrue(all(len(pt) == 2 for pt in layout["coordinates"]))
        self.assertEqual(layout["warnings"], [])

    def test_invalid_inputs_raise(self):
        with self.assertRaises(LayoutError):
            compute_layout(0, 10, 1.0)
        with self.assertRaises(LayoutError):
            compute_layout(10, 10, 9.0)  # spacing too large

    def test_room_too_small_raises(self):
        with self.assertRaises(LayoutError):
            compute_layout(1.0, 1.0, 0.6)

    def test_small_spacing_warns_but_succeeds(self):
        layout = compute_layout(10.0, 10.0, 0.05)
        self.assertTrue(layout["warnings"])
        self.assertGreater(layout["pipe_length_m"], 0)

    def test_render_svg(self):
        layout = compute_layout(10.0, 10.0, 1.0)
        svg = render_svg(layout)
        self.assertIn("<svg", svg)
        self.assertIn("polyline", svg)
        self.assertTrue(svg.strip().endswith("</svg>"))


if __name__ == "__main__":
    unittest.main()
