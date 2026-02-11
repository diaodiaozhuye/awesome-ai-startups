"""Tests for the JobKeywordMatcher."""

from __future__ import annotations

import pytest

from scrapers.keyword_matcher import JobKeywordMatcher


@pytest.fixture
def matcher() -> JobKeywordMatcher:
    return JobKeywordMatcher()


class TestGetSearchKeywords:
    def test_returns_english_keywords(self, matcher: JobKeywordMatcher) -> None:
        keywords = matcher.get_search_keywords("en")
        assert len(keywords) > 0
        assert any("Machine Learning" in kw for kw in keywords)

    def test_returns_chinese_keywords(self, matcher: JobKeywordMatcher) -> None:
        keywords = matcher.get_search_keywords("zh")
        assert len(keywords) > 0
        assert any("机器学习" in kw for kw in keywords)

    def test_unknown_language_returns_empty(self, matcher: JobKeywordMatcher) -> None:
        keywords = matcher.get_search_keywords("fr")
        assert keywords == []


class TestMatchesAIJob:
    def test_matches_ml_engineer(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("Senior Machine Learning Engineer") is True

    def test_matches_ai_researcher(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("AI Research Scientist") is True

    def test_matches_llm(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("LLM Engineer") is True

    def test_matches_deep_learning(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("Deep Learning Engineer") is True

    def test_matches_from_description(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job(
            "Software Engineer", "Working on computer vision models"
        ) is True

    def test_no_match_for_unrelated_job(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("Marketing Manager") is False

    def test_no_match_for_empty(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("") is False

    def test_matches_chinese_keyword(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("高级算法工程师") is True

    def test_matches_chinese_deep_learning(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("深度学习研究员") is True

    def test_case_insensitive(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.matches_ai_job("MACHINE LEARNING ENGINEER") is True


class TestExtractCategory:
    def test_extracts_llm_category(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.extract_category("LLM Engineer") == "llm-foundation-model"

    def test_extracts_robotics_category(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.extract_category("Robotics Engineer") == "ai-robotics"

    def test_extracts_vision_category(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.extract_category("Computer Vision Researcher") == "ai-image-video"

    def test_extracts_from_description(self, matcher: JobKeywordMatcher) -> None:
        category = matcher.extract_category(
            "Engineer", "Working on speech recognition systems"
        )
        assert category == "ai-audio-speech"

    def test_returns_none_for_generic(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.extract_category("Software Engineer") is None

    def test_extracts_chinese_llm(self, matcher: JobKeywordMatcher) -> None:
        assert matcher.extract_category("大模型工程师") == "llm-foundation-model"

    def test_extracts_chinese_robotics(self, matcher: JobKeywordMatcher) -> None:
        category = matcher.extract_category("", "自动驾驶算法")
        assert category in ("ai-robotics", "autonomous-vehicles")
