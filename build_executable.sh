#!/usr/bin/env bash
# Build the standalone "radiant-heat" executable with PyInstaller.
#
# Usage:
#   ./build_executable.sh
#
# The resulting binary is written to dist/radiant-heat and is fully
# self-contained (no Python installation required to run it).
set -euo pipefail

cd "$(dirname "$0")"

python -m pip install --upgrade pip >/dev/null 2>&1 || true
python -m pip install pyinstaller numpy flask >/dev/null

rm -rf build dist
pyinstaller --clean --noconfirm radiant-heat.spec

echo
echo "Built: $(pwd)/dist/radiant-heat"
./dist/radiant-heat --help >/dev/null && echo "Smoke test (--help) passed."
