# Changelog

## Modernization (2026-07)

A cleanup and modernization pass, ~2 years after the original build. The app
still runs entirely offline (no LLM API calls).

### Fixed
- **Real embeddings.** `embedding.py` previously returned *random vectors*, so
  the "semantic" merge wasn't semantic at all. It now uses a local
  `sentence-transformers` model (`all-MiniLM-L6-v2`).
- **Broken conflict UI.** The frontend read fields the backend never produced.
  Frontend and backend now share one contract, and the final merged document is
  assembled from the user's choices instead of fragile regex string-replacement.

### Changed
- **Backend consolidated to a single FastAPI service** (`api/`). The old Node/
  Express server that just shelled out to Python is gone; merging now runs
  in-process — no subprocesses, no temp-file passing.
- **Merge pipeline refactored** into the `notemerge` package with one canonical
  implementation (the duplicate `merge.py`/`merge_logic.py` versions were merged),
  typed dataclasses, and lazy model loading.
- **Frontend migrated from Create React App (deprecated) to Vite.** JSX files
  renamed to `.jsx`; API base URL is configurable via `VITE_API_URL`.
- **Dependencies modernized** for Python 3.12 (torch/faiss/numpy/etc.) and
  Node 24.

### Added
- `pytest` suite for the merge pipeline (`api/tests/`).
- `/api/health` and `/api/extract` endpoints.
- Upload now accepts multiple `.json`/`.pdf` files in one merge.

### Removed
- Committed runtime artifacts (`debug.log`, `merged_results.json`, sample
  uploads) — now gitignored.
- CRA build tooling (`react-scripts`, `web-vitals`, `reportWebVitals`,
  CRA test scaffolding).
