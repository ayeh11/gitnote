"""Text preprocessing helpers for the merge pipeline.

Sentences are lowercased, tokenized, lemmatized, and stripped of stopwords.
The preprocessed form is used only for the lexical *overlap* check that
complements the semantic (embedding) similarity check -- the embeddings
themselves are always computed from the original text.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"\b\w+\b")

# Lemmatizer / stopwords are initialized lazily so importing this module does
# not require the NLTK data to be present until it is actually used.
_lemmatizer = None
_stop_words: set[str] | None = None


def _ensure_nltk() -> None:
    global _lemmatizer, _stop_words
    if _lemmatizer is not None and _stop_words is not None:
        return

    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    for resource, path in (("stopwords", "corpora/stopwords"),
                           ("wordnet", "corpora/wordnet")):
        try:
            nltk.data.find(path)
        except LookupError:
            logger.info("Downloading NLTK resource '%s'...", resource)
            nltk.download(resource, quiet=True)

    _lemmatizer = WordNetLemmatizer()
    _stop_words = set(stopwords.words("english"))


@lru_cache(maxsize=4096)
def preprocess_sentence(sentence: str) -> tuple[str, float]:
    """Return ``(preprocessed_text, average_word_length)`` for a sentence.

    Average word length is used as a tie-breaker when deduplicating: given two
    near-identical bullets, the one with longer words (a proxy for more detail)
    is kept.
    """
    _ensure_nltk()
    words = _TOKEN_RE.findall(sentence.lower())
    lemmatized = [
        _lemmatizer.lemmatize(word) for word in words if word not in _stop_words
    ]
    preprocessed = " ".join(lemmatized)
    avg_word_length = (
        sum(len(w) for w in lemmatized) / len(lemmatized) if lemmatized else 0.0
    )
    return preprocessed, avg_word_length


def preprocess_header(header: str) -> str:
    """Normalize a header for comparison (lowercase, trimmed)."""
    return header.lower().strip()


def overlap_ratio(text_a: str, text_b: str) -> float:
    """Jaccard-style word overlap ratio between two (preprocessed) strings.

    Defined as ``|A ∩ B| / max(|A|, |B|)`` over the sets of words.
    """
    words_a = set(text_a.split())
    words_b = set(text_b.split())
    if not words_a or not words_b:
        return 0.0
    overlap = words_a & words_b
    return len(overlap) / max(len(words_a), len(words_b))
