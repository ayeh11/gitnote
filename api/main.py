"""GitNote backend: a single FastAPI service for merging structured notes.

Everything runs locally. The only network access is a one-time download of the
local embedding model on first run; set ``HF_HUB_OFFLINE=1`` to forbid even that
once the model is cached. No note content is ever sent to a remote service.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from notemerge import merge_notes
from notemerge.merge import load_note
from notemerge.pdf import pdf_to_note

logging.basicConfig(
    level=os.environ.get("NOTEMERGE_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("gitnote")

app = FastAPI(title="GitNote", version="1.0.0")

# Frontend dev servers (Vite defaults). Override with NOTEMERGE_CORS_ORIGINS.
_origins = os.environ.get(
    "NOTEMERGE_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _upload_to_note(upload: UploadFile, raw: bytes) -> dict:
    """Turn one uploaded file (.json note or .pdf) into a normalized note."""
    name = upload.filename or "note"
    ext = os.path.splitext(name)[1].lower()

    if ext == ".json":
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(400, f"'{name}' is not valid JSON: {exc}") from exc
        return load_note(data, name)

    if ext == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(raw)
            tmp.flush()
            return load_note(pdf_to_note(tmp.name), name)

    raise HTTPException(400, f"Unsupported file type '{ext}'. Upload .json or .pdf.")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/extract")
async def extract(files: list[UploadFile] = File(...)) -> dict:
    """Extract structured notes from uploaded PDFs (no merging)."""
    notes = {}
    for upload in files:
        raw = await upload.read()
        if not (upload.filename or "").lower().endswith(".pdf"):
            raise HTTPException(400, "The /api/extract endpoint accepts PDFs only.")
        notes.update(pdf_to_note_from_bytes(upload.filename, raw))
    return notes


@app.post("/api/merge")
async def merge(files: list[UploadFile] = File(...)) -> dict:
    """Merge two or more uploaded notes (.json and/or .pdf) into one document."""
    if len(files) < 2:
        raise HTTPException(400, "Upload at least two notes to merge.")

    notes = []
    for upload in files:
        raw = await upload.read()
        notes.append(_upload_to_note(upload, raw))

    logger.info("Merging %d notes...", len(notes))
    result = merge_notes(notes)
    logger.info("Merge produced %d header group(s).", len(result["headers"]))
    return result


def pdf_to_note_from_bytes(filename: str | None, raw: bytes) -> dict:
    name = filename or "note.pdf"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(raw)
        tmp.flush()
        note = pdf_to_note(tmp.name)
    # Re-key by the original filename rather than the temp path's basename.
    return {name: {"pdf_id": name, "headers": next(iter(note.values()))["headers"]}}
