#!/usr/bin/env bash
# Starts the GitNote backend (FastAPI on :8000) and frontend (Vite on :5173)
# together. Press Ctrl-C to stop both.
#
# Env:
#   OFFLINE=1   run the embedding model fully offline (must be cached already)
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -x api/.venv/bin/uvicorn ]; then
  echo "Backend not set up. Run ./setup.sh first." >&2
  exit 1
fi

# Stop background children on exit (Ctrl-C included).
cleanup() { kill 0 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "==> Backend:  http://localhost:8000"
(
  cd api
  if [ "${OFFLINE:-0}" = "1" ]; then export HF_HUB_OFFLINE=1; fi
  exec .venv/bin/uvicorn main:app --reload --port 8000
) &

echo "==> Frontend: http://localhost:5173"
npm run dev &

wait
