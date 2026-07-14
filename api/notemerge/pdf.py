"""Extract a header/bullet structure from PDF notes using pdfplumber.

Headers are detected heuristically as runs of text noticeably larger than the
page's most common font size; the text between consecutive headers becomes that
header's section, split into bullets. Output matches the note format consumed by
:mod:`notemerge.merge`.
"""

from __future__ import annotations

import os
import re
from collections import Counter

import pdfplumber

# Bullet glyphs handled when splitting section text.
_BULLET_GLYPHS = "•○▪●⁃"
_BULLET_PATTERNS = [
    r"(\s*-\s+)",
    r"(\s*\d+\.\s+)",
] + [rf"(\s*{re.escape(g)}\s+)" for g in _BULLET_GLYPHS]
_SPLIT_RE = re.compile("|".join(_BULLET_PATTERNS))
_STARTS_BULLET_RE = re.compile(rf"^[-{_BULLET_GLYPHS}]|^\d+\.")
_GLYPH_STRIP_RE = re.compile(rf"[{_BULLET_GLYPHS}]")


def _extract_headers(words, normal_font_size, size_threshold):
    headers = []
    current = ""
    current_size = None
    current_doctop = None
    last_doctop = None

    for word in words:
        size = round(word["size"], 1)
        if size < normal_font_size * size_threshold:
            continue
        doctop = word["doctop"]

        if current_size is None or abs(size - current_size) < 0.1:
            new_line = not current or (
                last_doctop is not None and abs(doctop - last_doctop) > 5
            )
            if new_line:
                if current:
                    headers.append({"text": current.strip(), "doctop": current_doctop})
                current, current_size, current_doctop = word["text"], size, doctop
            else:
                current += " " + word["text"]
        else:
            headers.append({"text": current.strip(), "doctop": current_doctop})
            current, current_size, current_doctop = word["text"], size, doctop
        last_doctop = doctop

    if current:
        headers.append({"text": current.strip(), "doctop": current_doctop})
    return headers


def _parse_bullets(text: str) -> list[str]:
    segments = [s.strip() for s in _SPLIT_RE.split(text) if s and s.strip()]

    entries: list[str] = []
    current = ""
    for segment in segments:
        if _STARTS_BULLET_RE.match(segment):
            if current:
                entries.append(current.strip())
            current = segment
        else:
            current += " " + segment
    if current:
        entries.append(current.strip())

    cleaned = []
    for entry in entries:
        entry = re.sub(r"^\s*-\s*", "", entry)
        entry = _GLYPH_STRIP_RE.sub("", entry).strip()
        if entry:
            cleaned.append(entry)
    return cleaned


def _extract_sections(page, headers):
    boundaries = headers + [{"text": None, "doctop": float("inf")}]
    words = page.extract_words(use_text_flow=True, extra_attrs=["doctop"])

    sections = []
    for i in range(len(boundaries) - 1):
        start, end = boundaries[i]["doctop"], boundaries[i + 1]["doctop"]
        body = " ".join(w["text"] for w in words if start < w["doctop"] < end)
        bullets = _parse_bullets(body)
        if bullets:
            sections.append({"header": boundaries[i]["text"], "section_text": bullets})
    return sections


def process_pdf(pdf_path: str, size_threshold: float = 1.2) -> list[dict]:
    """Return a list of ``{text, page_num, section_text}`` for one PDF."""
    hierarchy = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(extra_attrs=["fontname", "size", "top", "doctop"])
            if not words:
                continue
            font_sizes = [round(w["size"], 1) for w in words if "size" in w]
            if not font_sizes:
                continue
            normal_font_size = Counter(font_sizes).most_common(1)[0][0]

            headers = _extract_headers(words, normal_font_size, size_threshold)
            if not headers:
                continue
            for section in _extract_sections(page, headers):
                hierarchy.append({
                    "text": section["header"],
                    "page_num": page_number,
                    "section_text": section["section_text"],
                })
    return hierarchy


def pdf_to_note(pdf_path: str, size_threshold: float = 1.2) -> dict:
    """Extract one PDF into the merge input format, keyed by the file name."""
    pdf_id = os.path.basename(pdf_path)
    return {pdf_id: {"pdf_id": pdf_id, "headers": process_pdf(pdf_path, size_threshold)}}
