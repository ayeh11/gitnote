#!/usr/bin/env bash
# One-time setup for GitNote: creates the Python venv, installs backend +
# frontend dependencies. Safe to re-run.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3.12}"

echo "==> Backend: creating virtualenv (api/.venv) with $PYTHON"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Error: $PYTHON not found. Install Python 3.12 (e.g. 'brew install python@3.12')" >&2
  echo "or set PYTHON=/path/to/python3.12 and re-run." >&2
  exit 1
fi
"$PYTHON" -m venv api/.venv
api/.venv/bin/python -m pip install --upgrade pip
api/.venv/bin/python -m pip install -r api/requirements.txt

echo "==> Frontend: installing npm dependencies"
npm install

echo
echo "Done. Start the app with: ./dev.sh"
