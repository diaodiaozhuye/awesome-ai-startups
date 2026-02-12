"""Extract bilingual (Chinese + English) keywords from product data."""

from __future__ import annotations

import re
from typing import Any


class KeywordExtractor:
    """Extract search keywords from product data for discovery and search.

    Generates keywords from multiple fields: name, description, tags,
    use_cases, category, sub_category. Outputs both Chinese and English
    keywords for bilingual search.
    """

    # Common stop words to exclude
    _EN_STOP_WORDS = frozenset(
        {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "it",
            "its",
            "this",
            "that",
            "these",
            "those",
            "i",
            "we",
            "you",
            "he",
            "she",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "our",
            "their",
            "what",
            "which",
            "who",
            "when",
            "where",
            "how",
            "not",
            "no",
            "can",
            "will",
            "just",
            "should",
            "now",
            "also",
            "than",
            "then",
            "very",
            "more",
            "most",
            "such",
            "each",
            "every",
            "all",
            "any",
            "has",
            "have",
            "had",
            "do",
            "does",
            "did",
        }
    )

    # AI/tech terms to always preserve (even if short)
    _PRESERVE_TERMS = frozenset(
        {
            "ai",
            "ml",
            "llm",
            "nlp",
            "gpt",
            "gpu",
            "tpu",
            "npu",
            "rag",
            "api",
            "sdk",
            "cli",
            "saas",
            "b2b",
            "b2c",
        }
    )

    def extract(self, product: dict[str, Any]) -> list[str]:
        """Extract bilingual keywords from a product dict.

        Returns deduplicated list of keywords (English + Chinese mixed).
        """
        keywords: list[str] = []
        seen: set[str] = set()

        def _add(term: str) -> None:
            normalized = term.strip().lower()
            if normalized and normalized not in seen and len(normalized) >= 2:
                seen.add(normalized)
                keywords.append(term.strip())

        # Product name (always include as-is)
        name = product.get("name", "")
        if name:
            _add(name)

        # Chinese name
        name_zh = product.get("name_zh")
        if name_zh:
            _add(name_zh)

        # Company name
        company = product.get("company", {})
        if company.get("name"):
            _add(company["name"])
        if company.get("name_zh"):
            _add(company["name_zh"])

        # Category and sub_category as keywords
        category = product.get("category", "")
        if category:
            # Convert slug to readable: "ai-model" -> "AI Model"
            _add(category.replace("-", " "))
        sub_cat = product.get("sub_category", "")
        if sub_cat:
            _add(sub_cat.replace("-", " "))

        # Tags
        for tag in product.get("tags", []):
            _add(tag.replace("-", " "))

        # Use cases
        for uc in product.get("use_cases", []):
            _add(uc)

        # Extract meaningful words from description
        description = product.get("description", "")
        if description:
            for word in self._extract_meaningful_words(description):
                _add(word)

        # Chinese description keywords
        desc_zh = product.get("description_zh", "")
        if desc_zh:
            for term in self._extract_chinese_terms(desc_zh):
                _add(term)

        # Modalities
        for mod in product.get("modalities", []):
            _add(mod)

        # Product type
        pt = product.get("product_type", "")
        if pt:
            _add(pt.replace("-", " "))

        return keywords

    def _extract_meaningful_words(self, text: str) -> list[str]:
        """Extract meaningful English terms from text."""
        # Split into words, filter stop words and short words
        words = re.findall(r"[A-Za-z][A-Za-z0-9-]+", text)
        result: list[str] = []
        for word in words:
            lower = word.lower()
            if lower in self._PRESERVE_TERMS or (
                lower not in self._EN_STOP_WORDS and len(word) >= 4
            ):
                result.append(word)
        return result[:20]  # Limit extracted words

    @staticmethod
    def _extract_chinese_terms(text: str) -> list[str]:
        """Extract Chinese terms (2+ char sequences) from text."""
        # Simple extraction: find Chinese character sequences
        chinese_sequences = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        return chinese_sequences[:15]  # Limit
