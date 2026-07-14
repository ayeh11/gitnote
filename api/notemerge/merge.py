"""Merge multiple structured notes into one, git-conflict style.

Pipeline
--------
1. Collect every header from every note.
2. Group headers that are both semantically similar and lexically overlapping
   (union-find over the pairwise similarity matrix).
3. Within each header group, pool all bullets and deduplicate them.
4. Emit an accepted merged document plus, for every group and bullet, the
   alternatives that were folded in as *conflicts* for the user to resolve.

Input note format (as produced by :mod:`notemerge.pdf`)::

    {
      "<pdf_id>": {
        "pdf_id": "<pdf_id>",
        "headers": [
          {"text": "Header", "section_text": ["bullet", ...]},
          ...
        ]
      },
      ...
    }
"""

from __future__ import annotations

import json
import logging
import os

import numpy as np

from .deduplication import deduplicate_bullets
from .embedding import generate_embeddings
from .models import Bullet, MergedHeader, SourceHeader
from .preprocess import overlap_ratio, preprocess_header, preprocess_sentence

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_note(data: dict, note_id: str) -> dict:
    """Normalize one parsed note file into ``{"note_id", "headers"}``.

    Accepts the multi-PDF wrapper format; each contained PDF's headers are
    flattened into a single note keyed by ``note_id``.
    """
    headers = []
    for pdf_key, pdf_data in data.items():
        for header in pdf_data.get("headers", []):
            name = header.get("text") or "Untitled"
            section = header.get("section_text", [])
            if isinstance(section, str):
                section = [section]
            bullets = [b.strip() for b in section if isinstance(b, str) and b.strip()]
            headers.append({"header_name": name, "bullets": bullets})
    return {"note_id": note_id, "headers": headers}


def load_notes_from_files(directory: str) -> list[dict]:
    """Load and normalize all ``*.json`` notes in a directory, sorted by name."""
    notes = []
    for file_name in sorted(os.listdir(directory)):
        if not file_name.endswith(".json"):
            continue
        path = os.path.join(directory, file_name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            notes.append(load_note(json.load(f), file_name))
    return notes


# --------------------------------------------------------------------------- #
# Header grouping (union-find)
# --------------------------------------------------------------------------- #
class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, u: int) -> int:
        while self.parent[u] != u:
            self.parent[u] = self.parent[self.parent[u]]  # path compression
            u = self.parent[u]
        return u

    def union(self, u: int, v: int) -> None:
        pu, pv = self.find(u), self.find(v)
        if pu != pv:
            self.parent[pu] = pv


def _collect_headers(notes: list[dict]) -> list[SourceHeader]:
    headers: list[SourceHeader] = []
    for note in notes:
        for header in note["headers"]:
            headers.append(SourceHeader(
                header_id=len(headers),
                note_id=note["note_id"],
                name=header["header_name"].strip().strip(":"),
                bullets=header["bullets"],
            ))
    return headers


def _group_headers(
    headers: list[SourceHeader],
    similarity_threshold: float,
    overlap_threshold: float,
) -> list[list[int]]:
    """Return groups of header indices that should be merged together."""
    embeddings = generate_embeddings([h.name for h in headers], normalize=True)
    for header, emb in zip(headers, embeddings):
        header.embedding = emb

    similarity = embeddings @ embeddings.T

    uf = _UnionFind(len(headers))
    for i in range(len(headers)):
        for j in range(i + 1, len(headers)):
            overlap = overlap_ratio(preprocess_header(headers[i].name),
                                    preprocess_header(headers[j].name))
            if similarity[i, j] >= similarity_threshold and overlap >= overlap_threshold:
                uf.union(i, j)

    groups: dict[int, list[int]] = {}
    for idx in range(len(headers)):
        groups.setdefault(uf.find(idx), []).append(idx)
    return list(groups.values())


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def merge_notes(
    notes: list[dict],
    similarity_threshold: float = 0.7,
    overlap_threshold: float = 0.4,
    header_similarity_threshold: float = 0.75,
    header_overlap_threshold: float = 0.3,
) -> dict:
    """Merge notes and return a JSON-serializable result.

    Returns a dict with ``merged_text`` and ``headers`` (each header carries its
    accepted bullets, ``conflicting_headers`` and per-bullet
    ``conflicting_bullets``).
    """
    headers = _collect_headers(notes)
    if not headers:
        return {"merged_text": "", "headers": []}

    groups = _group_headers(headers, header_similarity_threshold,
                            header_overlap_threshold)

    merged_headers: list[MergedHeader] = []
    for group in groups:
        group_headers = sorted((headers[i] for i in group),
                               key=lambda h: (str(h.note_id), h.header_id))
        accepted = group_headers[0]

        header_conflicts = []
        for other in group_headers[1:]:
            sim = float(np.dot(other.embedding, accepted.embedding))
            overlap = overlap_ratio(preprocess_header(accepted.name),
                                    preprocess_header(other.name))
            header_conflicts.append({
                "note_id": other.note_id,
                "header_id": other.header_id,
                "header_name": other.name,
                "similarity": sim,
                "overlap_ratio": overlap,
            })

        bullets = _build_bullets(group_headers)
        merged_bullets = deduplicate_bullets(bullets, similarity_threshold,
                                             overlap_threshold)

        merged_headers.append(MergedHeader(
            header_id=accepted.header_id,
            note_id=accepted.note_id,
            name=accepted.name,
            bullets=merged_bullets,
            conflicts=header_conflicts,
        ))

    return _serialize(merged_headers)


def _build_bullets(group_headers: list[SourceHeader]) -> list[Bullet]:
    """Flatten a header group's bullets and attach embeddings (dedup by text)."""
    bullets: list[Bullet] = []
    for header in group_headers:
        for i, text in enumerate(header.bullets, start=1):
            pre, avg_len = preprocess_sentence(text)
            bullets.append(Bullet(header.note_id, i, text, pre, avg_len))

    # Embed each distinct preprocessed form once, then fan back out.
    unique = list({b.preprocessed for b in bullets})
    if unique:
        embeddings = generate_embeddings(unique, normalize=True)
        by_text = {pre: emb for pre, emb in zip(unique, embeddings)}
        for bullet in bullets:
            bullet.embedding = by_text[bullet.preprocessed]
    return bullets


def _serialize(merged_headers: list[MergedHeader]) -> dict:
    lines: list[str] = []
    headers_out = []
    for header in merged_headers:
        lines.append(f"{header.name}:")
        bullets_out = []
        for bullet in header.bullets:
            lines.append(f"- {bullet.text}")
            bullets_out.append({
                "bullet_id": bullet.bullet_id,
                "note_id": bullet.note_id,
                "text": bullet.text,
                "conflicting_bullets": bullet.conflicts,
            })
        headers_out.append({
            "header_id": header.header_id,
            "note_id": header.note_id,
            "header_name": header.name,
            "conflicting_headers": header.conflicts,
            "bullets": bullets_out,
        })
    return {"merged_text": "\n".join(lines), "headers": headers_out}
