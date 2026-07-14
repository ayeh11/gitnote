"""Tests for the merge pipeline and API.

Run with: .venv/bin/python -m pytest
The embedding model is downloaded once (or loaded from the local HF cache).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from notemerge import merge_notes  # noqa: E402
from notemerge.merge import load_note  # noqa: E402

NOTE_A = {
    "a.pdf": {
        "pdf_id": "a.pdf",
        "headers": [
            {"text": "Sorting Algorithms", "section_text": [
                "Bubble sort repeatedly swaps adjacent out-of-order elements.",
                "Merge sort is a stable divide-and-conquer algorithm.",
            ]},
        ],
    }
}

NOTE_B = {
    "b.pdf": {
        "pdf_id": "b.pdf",
        "headers": [
            {"text": "Sorting Techniques", "section_text": [
                "Bubble sort repeatedly swaps adjacent elements that are out of order.",
                "Quick sort partitions data around a pivot value.",
            ]},
        ],
    }
}


def test_load_note_normalizes_structure():
    note = load_note(NOTE_A, "a.pdf")
    assert note["note_id"] == "a.pdf"
    assert note["headers"][0]["header_name"] == "Sorting Algorithms"
    assert len(note["headers"][0]["bullets"]) == 2


def test_merge_groups_similar_headers_and_dedupes_bullets():
    notes = [load_note(NOTE_A, "a.pdf"), load_note(NOTE_B, "b.pdf")]
    result = merge_notes(notes)

    # "Sorting Algorithms" and "Sorting Techniques" should merge into one group.
    assert len(result["headers"]) == 1
    header = result["headers"][0]
    assert header["conflicting_headers"], "expected the other header as a conflict"

    # The near-identical bubble-sort bullet should be deduplicated into a
    # conflict; unique bullets (merge sort, quick sort) should both survive.
    texts = [b["text"] for b in header["bullets"]]
    assert any("Merge sort" in t for t in texts)
    assert any("Quick sort" in t for t in texts)
    bubble = [b for b in header["bullets"] if "Bubble sort" in b["text"]]
    assert len(bubble) == 1
    assert bubble[0]["conflicting_bullets"], "expected a bubble-sort conflict"


def test_merge_empty_input():
    assert merge_notes([]) == {"merged_text": "", "headers": []}


def test_merged_text_shape():
    notes = [load_note(NOTE_A, "a.pdf"), load_note(NOTE_B, "b.pdf")]
    result = merge_notes(notes)
    assert result["merged_text"].startswith("Sorting")
    assert "- " in result["merged_text"]
