"""Tests for the Flask HTTP API."""

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from api import create_app  # noqa: E402


class TestApi(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "ok")

    def test_index_serves_html(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.content_type)

    def test_openapi(self):
        resp = self.client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        spec = resp.get_json()
        self.assertEqual(spec["openapi"], "3.0.3")
        self.assertIn("/api/layout", spec["paths"])

    def test_layout_get(self):
        resp = self.client.get("/api/layout?room_length=10&room_width=10&pipe_spacing=1")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertAlmostEqual(data["pipe_length_m"], 71.0, places=2)
        self.assertEqual(len(data["coordinates"]), 72)

    def test_layout_post_json(self):
        resp = self.client.post("/api/layout",
                                json={"room_length": 10, "room_width": 10, "pipe_spacing": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["coverage"]["coverage_percent"], 64.0)

    def test_default_spacing(self):
        resp = self.client.get("/api/layout?room_length=10&room_width=10")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["pipe_spacing"], 0.2)

    def test_missing_param_is_400(self):
        resp = self.client.get("/api/layout?room_length=10")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

    def test_non_numeric_is_400(self):
        resp = self.client.get("/api/layout?room_length=abc&room_width=10")
        self.assertEqual(resp.status_code, 400)

    def test_room_too_small_is_422(self):
        resp = self.client.get("/api/layout?room_length=1&room_width=1&pipe_spacing=0.6")
        self.assertEqual(resp.status_code, 422)

    def test_svg_endpoint(self):
        resp = self.client.get("/api/layout.svg?room_length=10&room_width=10&pipe_spacing=1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("image/svg+xml", resp.content_type)
        self.assertIn(b"<svg", resp.data)


if __name__ == "__main__":
    unittest.main()
