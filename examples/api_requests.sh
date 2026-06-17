#!/usr/bin/env bash
# Demonstrate calling the HTTP API the way another service would.
#
# Start the server first (in another terminal), then run this script:
#   python src/api.py                       # or: docker run --rm -p 8000:8000 radiant-heat
#   ./examples/api_requests.sh
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8000}"

echo "# Health check"
curl -s "$BASE/health"; echo

echo "# Bedroom layout via GET (query params)"
curl -s "$BASE/api/layout?room_length=5&room_width=4&pipe_spacing=0.2"; echo

echo "# Living room layout via POST (JSON body)"
curl -s -X POST "$BASE/api/layout" \
  -H 'Content-Type: application/json' \
  -d '{"room_length": 8, "room_width": 6, "pipe_spacing": 0.2}'; echo

echo "# Render the bedroom as an SVG image"
curl -s "$BASE/api/layout.svg?room_length=5&room_width=4&pipe_spacing=0.2&width=820" -o bedroom_api.svg
echo "wrote bedroom_api.svg"

echo "# Machine-readable API description"
curl -s "$BASE/openapi.json" | head -c 200; echo " ..."
