# GitNote

Git-style merging for your notes. Upload two or more sets of notes (extracted
from PDFs or as JSON) and GitNote **semantically merges** them: it groups similar
sections, deduplicates near-identical bullet points, and surfaces the rest as
**merge conflicts** you resolve in a diff-style UI — keep mine, keep theirs, keep
both, or drop.

Everything runs **locally and offline**. Embeddings are produced by a local
sentence-transformers model; no note content is ever sent to an LLM API.

## How it works

1. **Extract** — `pdfplumber` turns PDFs into a header/bullet structure.
2. **Embed** — each header and bullet is embedded locally with
   `all-MiniLM-L6-v2` (`sentence-transformers`).
3. **Group** — headers that are both semantically similar *and* lexically
   overlapping are merged (union-find over the similarity matrix).
4. **Deduplicate** — within each group, near-identical bullets (cosine similarity
   + word overlap, via FAISS) collapse into one; the more detailed version is
   kept and the alternatives become conflicts.
5. **Resolve** — the frontend shows only the conflicts and lets you assemble the
   final document, then copy or download it.

## Project layout

```
.
├── index.html, vite.config.js, package.json   # Vite + React frontend
├── src/                                        # React app (views, components)
└── api/                                        # FastAPI backend
    ├── main.py                                 # HTTP API
    ├── notemerge/                              # merge pipeline (embedding, dedup, pdf…)
    ├── tests/                                  # pytest suite + fixtures
    └── requirements.txt
```

## Quick start

### Backend (Python 3.12)

```bash
cd api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The first run downloads the embedding model (~90 MB) and NLTK data, then caches
them. After that you can run fully offline: `HF_HUB_OFFLINE=1 uvicorn main:app`.

### Frontend

```bash
npm install
npm run dev        # http://localhost:5173
```

Set the backend URL by copying `.env.example` to `.env` (defaults to
`http://localhost:8000`).

## API

| Method | Path           | Body                         | Returns                              |
|--------|----------------|------------------------------|--------------------------------------|
| GET    | `/api/health`  | —                            | `{"status": "ok"}`                   |
| POST   | `/api/extract` | one or more PDF files        | extracted header/bullet JSON         |
| POST   | `/api/merge`   | two or more `.json`/`.pdf`   | `{ merged_text, headers: [...] }`    |

## Tests

```bash
cd api && .venv/bin/python -m pytest
```

See [CHANGELOG.md](CHANGELOG.md) for the 2026 modernization notes.
