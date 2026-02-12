"""Papers with Code scraper via Firecrawl.

T2 Open Web — scrapes benchmark leaderboards and SOTA tables from
paperswithcode.com. Cloudflare-protected, requires Firecrawl.
Enriches existing products with benchmark scores and paper links.
"""

from __future__ import annotations

import logging
import re

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)

_BASE_URL = "https://paperswithcode.com"

# Key benchmark leaderboard pages to scrape
_BENCHMARK_PAGES = [
    "/sota/language-modelling-on-wikitext-103",
    "/sota/question-answering-on-squad20",
    "/sota/machine-translation-on-wmt2014-english-german",
    "/sota/image-classification-on-imagenet",
    "/sota/object-detection-on-coco",
    "/sota/text-generation-on-mmlu",
    "/sota/multi-task-language-understanding-on-mmlu",
    "/sota/code-generation-on-humaneval",
    "/sota/math-word-problem-solving-on-gsm8k",
    "/sota/common-sense-reasoning-on-hellaswag",
    "/sota/reading-comprehension-on-arc-challenge",
    "/sota/visual-question-answering-on-vqa-v2",
    "/sota/text-to-image-generation-on-coco",
    "/sota/speech-recognition-on-librispeech-test-clean",
]

# Pattern: leaderboard table rows — model name, score, paper link
_TABLE_ROW_PATTERN = re.compile(
    r"\|\s*\[?([^\]|]{2,80})\]?"
    r"(?:\((/paper/[^\s)]+)\))?"
    r"\s*\|"
    r"\s*([0-9]+\.?[0-9]*)\s*\|",
    re.MULTILINE,
)

# Alternative: markdown heading + model entries
_MODEL_ENTRY_PATTERN = re.compile(
    r"(?:^|\n)\d+\.\s+"
    r"\[?([^\]\n]{2,80})\]?"
    r"(?:\((https?://[^\s)]+)\))?"
    r"[^\n]*?"
    r"(\d+\.?\d*)\s*$",
    re.MULTILINE,
)

# Map benchmark page slugs to benchmark names
_BENCHMARK_NAMES: dict[str, str] = {
    "language-modelling-on-wikitext-103": "WikiText-103_Perplexity",
    "question-answering-on-squad20": "SQuAD2.0_F1",
    "machine-translation-on-wmt2014-english-german": "WMT14_en-de_BLEU",
    "image-classification-on-imagenet": "ImageNet_Top1",
    "object-detection-on-coco": "COCO_mAP",
    "text-generation-on-mmlu": "MMLU",
    "multi-task-language-understanding-on-mmlu": "MMLU",
    "code-generation-on-humaneval": "HumanEval_pass@1",
    "math-word-problem-solving-on-gsm8k": "GSM8K",
    "common-sense-reasoning-on-hellaswag": "HellaSwag",
    "reading-comprehension-on-arc-challenge": "ARC-Challenge",
    "visual-question-answering-on-vqa-v2": "VQA-v2",
    "text-to-image-generation-on-coco": "COCO_FID",
    "speech-recognition-on-librispeech-test-clean": "LibriSpeech_WER",
}

# Known model name → organization mapping
_MODEL_ORG_MAP: dict[str, str] = {
    "gpt": "OpenAI",
    "claude": "Anthropic",
    "gemini": "Google DeepMind",
    "llama": "Meta",
    "mistral": "Mistral AI",
    "qwen": "Alibaba",
    "deepseek": "DeepSeek",
    "phi": "Microsoft",
    "yi": "01.AI",
    "command": "Cohere",
    "falcon": "Technology Innovation Institute",
    "palm": "Google",
    "chinchilla": "DeepMind",
    "bloom": "BigScience",
    "stable diffusion": "Stability AI",
    "dall-e": "OpenAI",
    "whisper": "OpenAI",
}


class PapersWithCodeScraper(BaseScraper):
    """Scrape Papers with Code for benchmark leaderboard data.

    Iterates key benchmark pages via Firecrawl, extracting model names,
    scores, and paper links. Produces ScrapedProduct entries enriched
    with benchmark data in the extra field.
    """

    @property
    def source_name(self) -> str:
        return "papers_with_code"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape benchmark leaderboards for model data."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient
        except ImportError:
            logger.info("Firecrawl not available, skipping Papers with Code.")
            return []

        fc = FirecrawlClient()
        # Accumulate benchmarks per model
        model_data: dict[str, dict] = (
            {}
        )  # name_lower -> {name, benchmarks, paper_url, org}

        try:
            for page_path in _BENCHMARK_PAGES:
                if fc.remaining_quota <= 0:
                    logger.warning("Firecrawl quota exhausted during PWC scrape.")
                    break

                bench_slug = page_path.rsplit("/", 1)[-1]
                bench_name = _BENCHMARK_NAMES.get(bench_slug, bench_slug)
                url = f"{_BASE_URL}{page_path}"

                logger.debug("PWC: scraping %s", bench_slug)
                result = fc.scrape_url(url, formats=["markdown"], wait_for=3000)

                if not result.success:
                    logger.debug("PWC %s failed: %s", bench_slug, result.error)
                    continue

                entries = self._parse_leaderboard(result.markdown, bench_name)

                for model_name, score, paper_url in entries:
                    key = model_name.lower().strip()
                    if key not in model_data:
                        model_data[key] = {
                            "name": model_name,
                            "benchmarks": {},
                            "paper_url": paper_url,
                            "org": _guess_org(model_name),
                        }
                    model_data[key]["benchmarks"][bench_name] = score
                    if paper_url and not model_data[key]["paper_url"]:
                        model_data[key]["paper_url"] = paper_url

        finally:
            fc.close()

        # Convert to ScrapedProduct list
        products: list[ScrapedProduct] = []
        for data in model_data.values():
            if len(products) >= limit:
                break

            extra: dict[str, str] = {}
            for bname, bscore in data["benchmarks"].items():
                extra[f"benchmark_{bname}"] = bscore
            if data["paper_url"]:
                paper_full = data["paper_url"]
                if not paper_full.startswith("http"):
                    paper_full = f"{_BASE_URL}{paper_full}"
                extra["paper_url"] = paper_full

            products.append(
                ScrapedProduct(
                    name=data["name"],
                    source=self.source_name,
                    source_url=f"{_BASE_URL}/",
                    source_tier=SourceTier.T2_OPEN_WEB,
                    product_type="llm",
                    category="ai-model",
                    company_name=data["org"],
                    status="active",
                    extra=extra,
                )
            )

        logger.info("PWC: discovered %d models with benchmarks", len(products))
        return products

    def _parse_leaderboard(
        self, markdown: str, bench_name: str
    ) -> list[tuple[str, str, str]]:
        """Parse a leaderboard page for (model_name, score, paper_url) tuples."""
        if not markdown or len(markdown) < 100:
            return []

        entries: list[tuple[str, str, str]] = []
        seen: set[str] = set()

        for match in _TABLE_ROW_PATTERN.finditer(markdown):
            name = match.group(1).strip()
            paper_url = (match.group(2) or "").strip()
            score = match.group(3).strip()

            key = name.lower()
            if key in seen or len(name) < 2:
                continue
            seen.add(key)
            entries.append((name, score, paper_url))

        if len(entries) < 3:
            for match in _MODEL_ENTRY_PATTERN.finditer(markdown):
                name = match.group(1).strip()
                paper_url = (match.group(2) or "").strip()
                score = match.group(3).strip()

                key = name.lower()
                if key in seen or len(name) < 2:
                    continue
                seen.add(key)
                entries.append((name, score, paper_url))

        return entries


def _guess_org(model_name: str) -> str | None:
    """Guess the organization from a model name."""
    name_lower = model_name.lower()
    for prefix, org in _MODEL_ORG_MAP.items():
        if prefix in name_lower:
            return org
    return None
