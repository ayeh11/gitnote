"""Shared dataclasses for the merge pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Bullet:
    """A single bullet point from a source note."""

    note_id: str
    index: int  # 1-based position within its header
    text: str
    preprocessed: str
    avg_word_length: float
    embedding: np.ndarray | None = None

    @property
    def bullet_id(self) -> str:
        return f"{self.note_id}_{self.index}"


@dataclass
class SourceHeader:
    """A header (with its bullets) as it appears in one source note."""

    header_id: int
    note_id: str
    name: str
    bullets: list[str]
    embedding: np.ndarray | None = None


@dataclass
class MergedBullet:
    """A retained bullet plus the bullets it absorbed as conflicts."""

    note_id: str
    bullet_id: str
    text: str
    avg_word_length: float
    conflicts: list[dict] = field(default_factory=list)


@dataclass
class MergedHeader:
    """A merged header group: the accepted header, its bullets, and conflicts."""

    header_id: int
    note_id: str
    name: str
    bullets: list[MergedBullet]
    conflicts: list[dict] = field(default_factory=list)
