"""Keyword-based sentiment scoring engine for cotton market headlines."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import nltk
from nltk.corpus import stopwords
from textblob import TextBlob

logger = logging.getLogger(__name__)

_NLTK_DATA_READY = False


def _ensure_nltk_data() -> None:
    """Download required NLTK resources on first use."""
    global _NLTK_DATA_READY
    if _NLTK_DATA_READY:
        return
    for resource in ("punkt", "stopwords", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            try:
                nltk.data.find(f"corpora/{resource}")
            except LookupError:
                nltk.download(resource, quiet=True)
    _NLTK_DATA_READY = True


class SentimentLabel(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


BULLISH_KEYWORDS: set[str] = {
    "surge",
    "rally",
    "gain",
    "up",
    "rise",
    "bullish",
    "soar",
    "jump",
    "strong",
    "demand",
    "shortage",
    "export",
    "recover",
    "outperform",
    "record",
    "boom",
    "tight",
    "peak",
    "growth",
    "optimistic",
}

BEARISH_KEYWORDS: set[str] = {
    "drop",
    "fall",
    "decline",
    "bearish",
    "weak",
    "plunge",
    "slump",
    "loss",
    "surplus",
    "glut",
    "oversupply",
    "collapse",
    "downgrade",
    "recession",
    "default",
    "downturn",
    "flood",
    "crash",
    "cut",
    "reduce",
}


@dataclass
class SentimentResult:
    label: SentimentLabel
    confidence: float
    polarity: float
    matched_keywords: list[str] = field(default_factory=list)


class KeywordScorer:
    """Tier-1 keyword + polarity sentiment scorer for cotton market headlines."""

    def __init__(
        self,
        bullish_keywords: set[str] | None = None,
        bearish_keywords: set[str] | None = None,
        neutral_threshold: float = 0.05,
    ) -> None:
        _ensure_nltk_data()
        self._bullish = bullish_keywords or BULLISH_KEYWORDS
        self._bearish = bearish_keywords or BEARISH_KEYWORDS
        self._neutral_threshold = neutral_threshold
        self._stop_words: set[str] = set(stopwords.words("english"))

    def score(self, headline: str) -> SentimentResult:
        """Score a headline and return sentiment label, confidence, and matched keywords."""
        tokens = self._tokenize(headline)
        matched_bullish = [t for t in tokens if t in self._bullish]
        matched_bearish = [t for t in tokens if t in self._bearish]
        matched_keywords = matched_bullish + matched_bearish

        keyword_score = len(matched_bullish) - len(matched_bearish)
        blob = TextBlob(headline)
        polarity = blob.sentiment.polarity

        combined = 0.6 * (keyword_score / max(len(tokens), 1)) + 0.4 * polarity

        if combined > self._neutral_threshold:
            label = SentimentLabel.BULLISH
        elif combined < -self._neutral_threshold:
            label = SentimentLabel.BEARISH
        else:
            label = SentimentLabel.NEUTRAL

        confidence = min(abs(combined) * 2.0, 1.0)

        return SentimentResult(
            label=label,
            confidence=round(confidence, 4),
            polarity=round(polarity, 4),
            matched_keywords=matched_keywords,
        )

    def _tokenize(self, text: str) -> list[str]:
        from nltk.tokenize import word_tokenize

        tokens = word_tokenize(text.lower())
        return [t for t in tokens if t.isalpha() and t not in self._stop_words]
