"""AI/ML job keyword matching for job site scrapers."""

from __future__ import annotations

import json
from pathlib import Path

_KEYWORDS_FILE = Path(__file__).resolve().parent / "data" / "job_keywords.json"


def _load_keywords() -> dict[str, dict[str, list[str] | dict[str, list[str]]]]:
    """Load keyword config from JSON, falling back to built-in defaults."""
    if _KEYWORDS_FILE.exists():
        return json.loads(_KEYWORDS_FILE.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    return _default_keywords()


def _default_keywords() -> dict[str, dict[str, list[str] | dict[str, list[str]]]]:
    """Built-in fallback keywords when config file is missing."""
    return {
        "en": {
            "search": [
                "Machine Learning Engineer",
                "AI Researcher",
                "Deep Learning Engineer",
                "NLP Engineer",
                "LLM Engineer",
                "Computer Vision Engineer",
                "Generative AI Engineer",
            ],
            "match": [
                "machine learning",
                "artificial intelligence",
                "deep learning",
                "nlp",
                "llm",
                "computer vision",
                "neural network",
                "generative ai",
                "autonomous",
                "robotics",
            ],
            "categories": {
                "llm-foundation-model": ["llm", "large language model", "gpt"],
                "ai-robotics": ["robotics", "autonomous", "self-driving"],
                "ai-image-video": ["computer vision", "image generation", "diffusion"],
            },
        },
        "zh": {
            "search": [
                # Core AI roles
                "AI工程师",
                "人工智能工程师",
                "算法工程师",
                "机器学习工程师",
                "深度学习工程师",
                "大模型工程师",
                "LLM工程师",
                "人工智能研究员",
                # NLP / CV / Speech
                "NLP工程师",
                "自然语言处理",
                "计算机视觉工程师",
                "语音识别工程师",
                # Emerging roles
                "AIGC",
                "智能体开发",
                "AI Agent",
                "多模态",
                "具身智能",
                # Infrastructure
                "MLOps",
                "AI平台工程师",
                "推理优化",
                # Industry-specific
                "自动驾驶算法",
                "AI芯片",
                "机器人算法",
                "AI安全",
            ],
            "match": [
                "机器学习",
                "人工智能",
                "深度学习",
                "算法",
                "大模型",
                "自然语言处理",
                "计算机视觉",
                "语音识别",
                "aigc",
                "智能体",
                "多模态",
                "具身智能",
                "自动驾驶",
                "推理优化",
            ],
            "categories": {
                "llm-foundation-model": ["大模型", "语言模型", "llm"],
                "ai-robotics": ["机器人", "自动驾驶", "具身智能"],
                "ai-image-video": ["计算机视觉", "图像生成", "视频生成"],
                "ai-infrastructure": ["mlops", "推理优化", "ai平台", "ai芯片"],
            },
        },
    }


class JobKeywordMatcher:
    """Match job titles and descriptions against AI/ML keywords.

    Supports English and Chinese keyword sets loaded from a JSON config file.
    Used by all job-site scrapers to identify AI-relevant job listings and
    infer company categories.
    """

    def __init__(self) -> None:
        self._keywords = _load_keywords()

    def get_search_keywords(self, language: str = "en") -> list[str]:
        """Return search query keywords for a given language.

        These are the terms used to query job search APIs/pages.
        """
        lang_data = self._keywords.get(language, {})
        result = lang_data.get("search", [])
        return result if isinstance(result, list) else []

    def matches_ai_job(self, title: str, description: str = "") -> bool:
        """Check whether a job title or description contains AI/ML keywords.

        Checks both English and Chinese match keywords so a single call
        works regardless of language.
        """
        text = f"{title} {description}".lower()

        for lang_data in self._keywords.values():
            match_keywords = lang_data.get("match", [])
            if isinstance(match_keywords, list):
                for kw in match_keywords:
                    if kw.lower() in text:
                        return True
        return False

    def extract_category(self, title: str, description: str = "") -> str | None:
        """Infer the most likely company category from job text.

        Returns a category slug (e.g. ``"llm-foundation-model"``) or ``None``
        if no category can be determined.
        """
        text = f"{title} {description}".lower()

        for lang_data in self._keywords.values():
            categories = lang_data.get("categories", {})
            if isinstance(categories, dict):
                for category, keywords in categories.items():
                    if isinstance(keywords, list):
                        for kw in keywords:
                            if kw.lower() in text:
                                return category
        return None
