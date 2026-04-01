"""Unit tests for sentiment engine (KeywordScorer).

Tests the keyword-based scoring engine with curated keywords and TextBlob polarity refinement.
"""

from __future__ import annotations

from nlp.keyword_scorer import (
    BEARISH_KEYWORDS,
    BULLISH_KEYWORDS,
    KeywordScorer,
    SentimentLabel,
    SentimentResult,
)


class TestKeywordScorer:
    """Unit tests for KeywordScorer."""

    def test_bullish_headline_surge(self):
        """Test that 'surge' keyword produces bullish sentiment."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton prices surge on strong demand")

        assert result.label == SentimentLabel.BULLISH
        assert "surge" in result.matched_keywords

    def test_bullish_headline_rally(self):
        """Test that 'rally' keyword produces bullish sentiment."""
        scorer = KeywordScorer()
        result = scorer.score("Market rally continues")

        assert result.label == SentimentLabel.BULLISH
        assert "rally" in result.matched_keywords

    def test_bullish_headline_record(self):
        """Test that 'record' keyword produces bullish sentiment."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton hits record high")

        assert result.label == SentimentLabel.BULLISH

    def test_bearish_headline_drop(self):
        """Test that 'drop' keyword produces bearish sentiment."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton prices drop sharply")

        assert result.label == SentimentLabel.BEARISH
        assert "drop" in result.matched_keywords

    def test_bearish_headline_plunge(self):
        """Test that 'plunge' keyword produces bearish sentiment."""
        scorer = KeywordScorer()
        result = scorer.score("Market plunge continues")

        assert result.label == SentimentLabel.BEARISH
        assert "plunge" in result.matched_keywords

    def test_bearish_headline_oversupply(self):
        """Test that 'oversupply' keyword produces bearish sentiment."""
        scorer = KeywordScorer()
        result = scorer.score("Oversupply concerns weigh on cotton")

        assert result.label == SentimentLabel.BEARISH

    def test_neutral_headline(self):
        """Test neutral sentiment when keywords balanced or weak."""
        scorer = KeywordScorer()
        result = scorer.score("No major changes in market today")

        assert result.label == SentimentLabel.NEUTRAL

    def test_mixed_keywords_balance(self):
        """Test mixed keywords produce deterministic result."""
        scorer = KeywordScorer()
        result = scorer.score("Surge in supply but drop in demand")

        assert result.label == SentimentLabel.BULLISH

    def test_confidence_high_for_strong_signal(self):
        """Test that strong signals have high confidence."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton prices surge to record levels on strong demand")

        assert result.confidence > 0.7

    def test_confidence_low_for_weak_signal(self):
        """Test that weak signals have low confidence."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton prices stay the same")

        assert result.confidence < 0.5

    def test_polarity_from_textblob(self):
        """Test that polarity is returned from TextBlob."""
        scorer = KeywordScorer()
        result = scorer.score("Terrible news about cotton crash")

        assert result.polarity < 0

    def test_custom_keywords(self):
        """Test that custom keywords can be provided."""
        custom_bullish = {"skyrocket", "boom"}
        scorer = KeywordScorer(bullish_keywords=custom_bullish)
        result = scorer.score("Cotton prices boom today")

        assert result.label == SentimentLabel.BULLISH

    def test_empty_headline_handled(self):
        """Test empty headline doesn't crash."""
        scorer = KeywordScorer()
        result = scorer.score("")

        assert result.label in [SentimentLabel.NEUTRAL]

    def test_confidence_in_valid_range(self):
        """Test that confidence is always between 0 and 1."""
        scorer = KeywordScorer()
        test_headlines = [
            "Cotton surge",
            "Prices drop",
            "Market steady",
        ]
        for headline in test_headlines:
            result = scorer.score(headline)
            assert 0.0 <= result.confidence <= 1.0

    def test_matched_keywords_tracked(self):
        """Test that matched keywords are tracked."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton surge on strong demand and tight supply")

        matched = result.matched_keywords
        assert "surge" in matched
        assert "strong" in matched or "tight" in matched

    def test_multiple_bullish_keywords(self):
        """Test multiple bullish keywords accumulate score."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton surge and boom with record growth")

        assert result.label == SentimentLabel.BULLISH
        assert result.confidence > 0.5

    def test_multiple_bearish_keywords(self):
        """Test multiple bearish keywords accumulate score."""
        scorer = KeywordScorer()
        result = scorer.score("Cotton drop and crash due to oversupply and surplus")

        assert result.label == SentimentLabel.BEARISH
        assert result.confidence > 0.5

    def test_default_keywords_comprehensive(self):
        """Test that default keyword sets are not empty."""
        assert len(BULLISH_KEYWORDS) > 0
        assert len(BEARISH_KEYWORDS) > 0


class TestSentimentLabel:
    """Tests for SentimentLabel enum."""

    def test_bullish_value(self):
        """Test bullish enum value."""
        assert SentimentLabel.BULLISH.value == "bullish"

    def test_bearish_value(self):
        """Test bearish enum value."""
        assert SentimentLabel.BEARISH.value == "bearish"

    def test_neutral_value(self):
        """Test neutral enum value."""
        assert SentimentLabel.NEUTRAL.value == "neutral"


class TestSentimentResult:
    """Tests for SentimentResult dataclass."""

    def test_result_attributes(self):
        """Test all attributes are stored correctly."""
        result = SentimentResult(
            label=SentimentLabel.BULLISH,
            confidence=0.85,
            polarity=0.5,
            matched_keywords=["surge", "strong"],
        )

        assert result.label == SentimentLabel.BULLISH
        assert result.confidence == 0.85
        assert result.polarity == 0.5
        assert len(result.matched_keywords) == 2

    def test_default_matched_keywords(self):
        """Test default empty list for matched_keywords."""
        result = SentimentResult(
            label=SentimentLabel.NEUTRAL,
            confidence=0.5,
            polarity=0.0,
        )

        assert result.matched_keywords == []
