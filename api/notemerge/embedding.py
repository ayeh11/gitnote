"""Local, offline sentence embeddings.

This replaces the original random-vector placeholder with a real sentence
embedding model that runs entirely on-device via ``sentence-transformers``.
The model weights are downloaded from the Hugging Face hub on first use and
cached locally (``~/.cache/huggingface``); after that, and if
``HF_HUB_OFFLINE=1`` is set, everything runs with no network access.

The default model, ``all-MiniLM-L6-v2``, produces 384-dimensional embeddings
and is small (~90 MB) and fast on CPU, which suits merging notes locally.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("NOTEMERGE_MODEL", "all-MiniLM-L6-v2")


@lru_cache(maxsize=2)
def _get_model(model_name: str):
    """Load (and cache) the sentence-transformers model.

    Imported lazily so that importing this package is cheap and does not pull
    torch into memory until embeddings are actually needed.
    """
    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model '%s'...", model_name)
    return SentenceTransformer(model_name)


def generate_embeddings(
    texts: list[str],
    normalize: bool = True,
    model_name: str | None = None,
) -> np.ndarray:
    """Embed a list of texts.

    Parameters
    ----------
    texts:
        Texts to embed.
    normalize:
        L2-normalize each vector so that inner product equals cosine similarity.
    model_name:
        Override the default model.

    Returns
    -------
    np.ndarray
        A ``(len(texts), dim)`` float32 array. Empty input yields an empty array.
    """
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    model = _get_model(model_name or DEFAULT_MODEL)
    embeddings = model.encode(
        list(texts),
        normalize_embeddings=normalize,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return embeddings.astype(np.float32)


def embedding_dimension(model_name: str | None = None) -> int:
    """Return the embedding dimension of the configured model."""
    return _get_model(model_name or DEFAULT_MODEL).get_sentence_embedding_dimension()
