#!/usr/bin/env bash
# Starts the GitNote backend (FastAPI on :8000) and frontend (Vite on :5173)
# together. Press Ctrl-C to stop both. If either process exits, the other is
# stopped and the reason is reported.
#
# Env:
#   OFFLINE=1   run the embedding model fully offline (must be cached already)
set -uo pipefail

cd "$(dirname "$0")"

if [ ! -x api/.venv/bin/uvicorn ]; then
  echo "Backend not set up (api/.venv missing). Run ./setup.sh first." >&2
  exit 1
fi

if [ ! -d node_modules ]; then
  echo "Frontend not set up (node_modules missing). Run ./setup.sh first." >&2
  exit 1
fi

cleanup() { trap - EXIT INT TERM; kill 0 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "==> Backend:  http://localhost:8000"
(
  cd api
  if [ "${OFFLINE:-0}" = "1" ]; then export HF_HUB_OFFLINE=1; fi
  exec .venv/bin/uvicorn main:app --reload --port 8000
) &
BACKEND=$!

echo "==> Frontend: http://localhost:5173"
npm run dev &
FRONTEND=$!

# Wait for whichever exits first and say which one, so a crash isn't silent.
wait -n "$BACKEND" "$FRONTEND"
if ! kill -0 "$BACKEND" 2>/dev/null; then
  echo >&2
  echo "!! Backend (uvicorn) exited. Check the messages above for the cause." >&2
  echo "!! Try running it alone:  cd api && source .venv/bin/activate && uvicorn main:app --port 8000" >&2
else
  echo >&2
  echo "!! Frontend (vite) exited. Check the messages above for the cause." >&2
fi
