"""Thin helpers around FAISS for cosine-similarity search.

Embeddings are L2-normalized upstream, so an inner-product index gives cosine
similarity directly.
"""

from __future__ import annotations

import logging

import faiss
import numpy as np

logger = logging.getLogger(__name__)


def create_index(dimension: int) -> "faiss.IndexFlatIP":
    """Create a flat inner-product index for `dimension`-D vectors."""
    return faiss.IndexFlatIP(dimension)


def add_embeddings(index: "faiss.IndexFlatIP", embeddings: np.ndarray) -> None:
    """Add one or more embeddings (shape ``(n, dim)``) to the index."""
    index.add(np.ascontiguousarray(embeddings, dtype=np.float32))
    logger.debug("Added %d embeddings; index now holds %d.",
                 embeddings.shape[0], index.ntotal)
