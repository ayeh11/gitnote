"""NoteMerge: git-style semantic merging for structured notes.

All processing runs locally and offline. Sentence embeddings are produced by a
local sentence-transformers model (downloaded once, then cached); no network
calls to any LLM API are made at merge time.
"""

from .merge import merge_notes, load_notes_from_files, load_note

__all__ = ["merge_notes", "load_notes_from_files", "load_note"]
