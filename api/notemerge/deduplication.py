"""Deduplicate near-identical bullets within a header group.

Two bullets are considered duplicates when they are both semantically similar
(cosine similarity over embeddings >= ``similarity_threshold``) and lexically
overlapping (word overlap ratio >= ``overlap_threshold``). The requirement that
*both* hold guards against the failure mode where unrelated sentences happen to
land close in embedding space.

When duplicates are found, the bullet with the greater average word length is
kept (a heuristic for "more detailed"); the other is recorded as a conflict so
the user can still review and choose it in the UI.
"""

from __future__ import annotations

import logging

from .faiss_util import add_embeddings, create_index
from .models import Bullet, MergedBullet
from .preprocess import overlap_ratio

logger = logging.getLogger(__name__)


def _conflict_entry(bullet: Bullet, similarity: float, overlap: float) -> dict:
    return {
        "note_id": bullet.note_id,
        "bullet_id": bullet.bullet_id,
        "text": bullet.text,
        "similarity": float(similarity),
        "overlap_ratio": float(overlap),
    }


def deduplicate_bullets(
    bullets: list[Bullet],
    similarity_threshold: float = 0.7,
    overlap_threshold: float = 0.4,
) -> list[MergedBullet]:
    """Deduplicate a list of bullets, returning the retained bullets.

    Each retained :class:`MergedBullet` carries the list of bullets that were
    folded into it as ``conflicts``.
    """
    if not bullets:
        return []

    dimension = bullets[0].embedding.shape[0]
    index = create_index(dimension)

    retained: list[MergedBullet] = []
    retained_pre: list[str] = []

    for bullet in bullets:
        text = bullet.text.strip(".")

        if index.ntotal == 0:
            retained.append(
                MergedBullet(bullet.note_id, bullet.bullet_id, text,
                             bullet.avg_word_length)
            )
            retained_pre.append(bullet.preprocessed)
            add_embeddings(index, bullet.embedding.reshape(1, -1))
            continue

        # Compare against every retained bullet at once.
        similarities, indices = index.search(bullet.embedding.reshape(1, -1),
                                              index.ntotal)

        is_duplicate = False
        for sim, ridx in zip(similarities[0], indices[0]):
            if sim < similarity_threshold:
                # Results are sorted by descending similarity; nothing further
                # can clear the threshold.
                break

            existing = retained[ridx]
            overlap = overlap_ratio(bullet.preprocessed, retained_pre[ridx])
            if overlap < overlap_threshold:
                continue

            if bullet.avg_word_length > existing.avg_word_length:
                # Promote the current (more detailed) bullet; demote the old one.
                promoted = MergedBullet(
                    bullet.note_id, bullet.bullet_id, text,
                    bullet.avg_word_length, conflicts=existing.conflicts
                )
                promoted.conflicts.append({
                    "note_id": existing.note_id,
                    "bullet_id": existing.bullet_id,
                    "text": existing.text,
                    "similarity": float(sim),
                    "overlap_ratio": float(overlap),
                })
                retained[ridx] = promoted
                retained_pre[ridx] = bullet.preprocessed
            else:
                existing.conflicts.append(_conflict_entry(bullet, sim, overlap))

            is_duplicate = True
            break

        if not is_duplicate:
            retained.append(
                MergedBullet(bullet.note_id, bullet.bullet_id, text,
                             bullet.avg_word_length)
            )
            retained_pre.append(bullet.preprocessed)
            add_embeddings(index, bullet.embedding.reshape(1, -1))

    logger.info("Retained %d of %d bullets after deduplication.",
                len(retained), len(bullets))
    return retained
