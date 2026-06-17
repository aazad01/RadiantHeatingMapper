"""Tests for the unified command-line entrypoint."""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from cli import main  # noqa: E402


class TestCli(unittest.TestCase):
    def test_compute_prints_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["compute", "-l", "10", "-w", "10", "-s", "1"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertAlmostEqual(data["pipe_length_m"], 71.0, places=2)
        self.assertEqual(len(data["coordinates"]), 72)

    def test_svg_to_stdout(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["svg", "-l", "6", "-w", "4", "-s", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("<svg", buf.getvalue())

    def test_svg_to_file(self, ):
        out = Path(__file__).parent / "_cli_tmp.svg"
        try:
            rc = main(["svg", "-l", "6", "-w", "4", "-s", "1", "-o", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            self.assertIn("<svg", out.read_text())
        finally:
            out.unlink(missing_ok=True)

    def test_invalid_layout_returns_error_code(self):
        rc = main(["compute", "-l", "1", "-w", "1", "-s", "0.6"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
