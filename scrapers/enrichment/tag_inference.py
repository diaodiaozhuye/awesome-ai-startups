"""Rule-based tag inference engine for AI product data.

Zero-cost, no LLM calls. Infers tags from product fields (description, name,
category, sub_category, structured fields) using keyword matching and heuristics.
Designed to run after TieredMerger and before optional LLM enrichment.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TAGS_FILE = _REPO_ROOT / "data" / "tags.json"

# Maximum tags per product to avoid noise
MAX_TAGS = 20


def _load_valid_tag_ids(tags_file: Path = _TAGS_FILE) -> set[str]:
    """Load all valid tag IDs from the dimensional tags.json."""
    data = json.loads(tags_file.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for dim in data["dimensions"].values():
        for tag in dim["tags"]:
            ids.add(tag["id"])
    return ids


# ── Keyword → tag mappings (searched in description + name) ──────────────────

# Each entry: regex pattern → list of tag IDs to infer.
# Patterns are case-insensitive and match word boundaries where practical.
_TEXT_KEYWORD_RULES: list[tuple[str, list[str]]] = [
    # Technology
    (r"\btransformer\b", ["transformer"]),
    (r"\bdiffusion\b", ["diffusion-model"]),
    (r"\b(?:retrieval.augmented|rag)\b", ["rag"]),
    (r"\bmultimodal\b", ["multimodal"]),
    (r"\bnlp\b|\bnatural language\b", ["nlp"]),
    (
        r"\bcomputer vision\b|\bimage recognition\b|\bobject detection\b",
        ["computer-vision"],
    ),
    (r"\breinforcement learning\b", ["reinforcement-learning"]),
    (r"\bfine.?tun(?:e|ing)\b", ["fine-tuning"]),
    (r"\bembedding(?:s)?\b|\bvector(?:s)?\b", ["embedding"]),
    (
        r"\bspeech.to.text\b|\bspeech recognition\b|\btranscri(?:be|ption)\b|\basr\b",
        ["speech-to-text"],
    ),
    (r"\btext.to.image\b|\bimage generat(?:e|ion|or)\b", ["text-to-image"]),
    (r"\btext.to.video\b|\bvideo generat(?:e|ion|or)\b", ["text-to-video"]),
    (r"\btext.to.speech\b|\btts\b|\bvoice (?:generat|synthe|clon)", ["text-to-speech"]),
    (r"\btext.to.3d\b|\b3d generat(?:e|ion)\b", ["text-to-3d"]),
    (r"\btext.to.music\b|\bmusic generat(?:e|ion)\b", ["text-to-music"]),
    (
        r"\bcode generat(?:e|ion|or)\b|\bcoding assist\b|\bcode complet(?:e|ion)\b",
        ["code-generation"],
    ),
    (r"\bprompt engineer(?:ing)?\b", ["prompt-engineering"]),
    (r"\bimage.to.video\b", ["image-to-video"]),
    (r"\bgraph neural\b|\bgnn\b", ["graph-neural-network"]),
    (r"\bneuro.symbolic\b", ["neuro-symbolic"]),
    (r"\bmixture.of.experts\b|\bmoe\b", ["moe"]),
    (r"\bquantiz(?:e|ation)\b", ["quantization"]),
    (r"\bdistill(?:ation|ed)\b", ["distillation"]),
    (r"\bfederated learning\b", ["federated-learning"]),
    # Use Case
    (r"\bchatbot\b|\bchat bot\b|\bchat assistant\b|\bconversational ai\b", ["chatbot"]),
    (
        r"\bcopilot\b|\bcoding assistant\b|\bcode assistant\b|\bpair program",
        ["copilot"],
    ),
    (
        r"\bwriting assist\b|\bai writ(?:e|er|ing)\b|\bcopywriting\b",
        ["writing-assistant"],
    ),
    (r"\bdata analy(?:sis|tics)\b|\bdata visual", ["data-analysis"]),
    (r"\bcontent creat(?:e|ion|or)\b", ["content-creation"]),
    (r"\bcustomer (?:support|service)\b|\bhelpdesk\b", ["customer-support"]),
    (r"\bsearch engine\b|\bai search\b", ["search-engine"]),
    (r"\bworkflow automat(?:e|ion)\b|\bprocess automat", ["workflow-automation"]),
    (r"\bmarketing\b|\bad (?:generat|creat|campaign)", ["marketing"]),
    (r"\btranslat(?:e|ion|or)\b", ["translation"]),
    (r"\bmeeting (?:note|summar|transcript)\b", ["meeting-notes"]),
    (r"\bdesign\b.*\b(?:ai|tool|creative)\b|\bai.*\bdesign\b", ["design-creative"]),
    (r"\bphoto edit(?:ing|or)\b|\bimage edit(?:ing|or)\b", ["photo-editing"]),
    (r"\bvideo edit(?:ing|or)\b", ["video-editing"]),
    (r"\bvoice assistant\b", ["voice-assistant"]),
    (r"\bpersonal assistant\b", ["personal-assistant"]),
    (r"\bknowledge (?:base|graph|manag)\b", ["knowledge-base"]),
    (r"\bresearch (?:tool|assist|platform)\b|\bscientific research\b", ["research"]),
    (r"\btesting\b.*\bqa\b|\btest automat\b|\bquality assurance\b", ["testing-qa"]),
    (r"\bcode review\b", ["code-review"]),
    (r"\bpresentation\b|\bslide(?:s)?\b", ["presentation"]),
    (r"\bemail\b.*\b(?:ai|assist|generat|automat)\b", ["email"]),
    (
        r"\bsales\b.*\bcrm\b|\bcrm\b.*\bsales\b|\bsales (?:assist|automat|tool)\b",
        ["sales-crm"],
    ),
    (r"\b(?:hr|recruit|hiring|talent)\b", ["hr-recruiting"]),
    (r"\bproject manag\b", ["project-management"]),
    (r"\bcontent moderat\b", ["content-moderation"]),
    (r"\bsocial media\b", ["social-media"]),
    (r"\blegal\b.*\b(?:ai|assist|tool)\b", ["legal-assist"]),
    (r"\bfinance\b|\baccounting\b|\bfinancial\b", ["finance-accounting"]),
    (
        r"\beducat(?:e|ion|ional)\b|\btutoring\b|\blearning platform\b",
        ["education-tutoring"],
    ),
    # Domain
    (r"\bhealthcare\b|\bmedical\b|\bhealth\b.*\bai\b", ["healthcare"]),
    (r"\bdrug discover\b|\bpharma(?:ceut)?\b", ["drug-discovery"]),
    (r"\bmedical imag\b|\bradiology\b|\bdiagnostic imag", ["medical-imaging"]),
    (r"\bprotein (?:fold|struct|predict)\b|\balphafold\b", ["protein-folding"]),
    (r"\btrading\b|\bstock\b|\bfintech\b", ["trading"]),
    (r"\brisk (?:assess|manag)\b", ["risk-assessment"]),
    (r"\bfraud detect\b", ["fraud-detection"]),
    (r"\bgaming\b|\bgame\b.*\bai\b|\bai.*\bgame\b", ["gaming"]),
    (r"\bdefense\b|\bmilitary\b", ["defense"]),
    (r"\bclimate\b|\benergy\b|\bsustainab\b|\bcarbon\b", ["climate-energy"]),
    (r"\bmaterials? science\b", ["materials-science"]),
    (r"\bclinical trial\b", ["clinical-trials"]),
    (
        r"\bautonomous vehicl\b|\bself.driving\b|\bautonomous driv\b",
        ["autonomous-vehicles", "self-driving"],
    ),
    (r"\brobot(?:ic)?s?\b", ["robotics"]),
    (r"\bhumanoid\b", ["humanoid-robot"]),
    (r"\bdrone\b|\buav\b", ["drone"]),
    # Business model (from description clues)
    (r"\bopen.?source\b", ["open-source"]),
    (r"\bapi\b.*\b(?:service|platform|access)\b|\brest api\b", ["api-service"]),
    (r"\bsaas\b", ["saas"]),
    (r"\bfree(?:mium| tier| plan)\b", ["freemium"]),
    (r"\bself.hosted\b|\bon.premise\b", ["self-hosted"]),
    (r"\bcloud.native\b", ["cloud-native"]),
    # Audience
    (r"\bfor developer\b|\bdeveloper tool\b|\bdev tool\b", ["developers"]),
    (r"\bdata scien(?:ce|tist)\b|\bmachine learning engineer\b", ["data-scientists"]),
    (r"\benterprise\b", ["enterprises"]),
    (r"\bresearcher\b|\bacademi\b", ["researchers"]),
    (r"\bcreator\b|\bartist\b", ["creators"]),
    # Technical
    (r"\breal.time\b", ["real-time"]),
    (r"\blow.latency\b", ["low-latency"]),
    (r"\bon.device\b", ["on-device"]),
    (r"\bedge ai\b|\bedge (?:comput|deploy)\b", ["edge-ai"]),
    (r"\bmobile app\b|\bios\b.*\bandroid\b|\bandroid\b.*\bios\b", ["mobile-app"]),
    (r"\bdesktop app\b|\belectron\b|\bnative app\b", ["desktop-app"]),
    (r"\bbrowser extension\b|\bchrome extension\b", ["browser-extension"]),
    (r"\bsdk\b", ["sdk"]),
    (r"\bcli\b|\bcommand.line\b", ["cli-tool"]),
]

# Compiled regex patterns (case insensitive)
_COMPILED_RULES: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(pat, re.IGNORECASE), tags) for pat, tags in _TEXT_KEYWORD_RULES
]

# ── Category → baseline tags ─────────────────────────────────────────────────

_CATEGORY_TAGS: dict[str, list[str]] = {
    "ai-foundation-model": ["nlp", "researchers"],
    "ai-application": ["consumers"],
    "ai-creative-media": ["creators", "content-creation"],
    "ai-dev-platform": ["developers"],
    "ai-infrastructure": ["developers", "enterprises"],
    "ai-data-platform": ["data-analysis", "data-scientists"],
    "ai-search-retrieval": ["search-engine"],
    "ai-hardware": ["robotics"],
    "ai-security-governance": ["enterprises"],
    "ai-science-research": ["researchers", "research"],
    "ai-enterprise-vertical": ["enterprises", "b2b"],
}

# ── Sub-category → tag mappings ──────────────────────────────────────────────

_SUBCAT_TAGS: dict[str, list[str]] = {
    "text-generation": ["nlp", "chatbot"],
    "image-generation": ["text-to-image", "diffusion-model"],
    "video-generation": ["text-to-video"],
    "audio-speech": ["text-to-speech"],
    "music-generation": ["text-to-music"],
    "3d-generation": ["text-to-3d"],
    "coding-assistant": ["code-generation", "copilot", "developers"],
    "multi-agent-platform": ["developers"],
    "healthcare-medical": ["healthcare"],
    "education-tutoring": ["education", "education-tutoring"],
    "finance-accounting": ["finance", "finance-accounting"],
    "legal": ["legal", "legal-assist"],
    "research-paper": ["research", "researchers"],
    "data-labeling": ["data-scientists"],
    "model-serving": ["api-service", "developers"],
    "vector-database": ["embedding", "developers"],
}

# ── product_type → audience tags ─────────────────────────────────────────────

_PRODUCT_TYPE_TAGS: dict[str, list[str]] = {
    "app": ["consumers"],
    "model": ["researchers", "developers"],
    "library": ["developers", "sdk"],
    "framework": ["developers"],
    "platform": ["enterprises"],
    "api": ["developers", "api-service", "api-platform"],
    "dataset": ["researchers", "data-scientists"],
}

# ── Platform → technical tags ────────────────────────────────────────────────

_PLATFORM_TAGS: dict[str, str] = {
    "ios": "mobile-app",
    "android": "mobile-app",
    "web": "saas",
    "desktop": "desktop-app",
    "browser-extension": "browser-extension",
    "api": "api-platform",
    "cli": "cli-tool",
}


class TagInferenceEngine:
    """Rule-based tag inference engine. Zero LLM cost.

    Usage:
        engine = TagInferenceEngine()
        new_tags = engine.infer(product_dict)
    """

    def __init__(self, tags_file: Path = _TAGS_FILE) -> None:
        self._valid_tags = _load_valid_tag_ids(tags_file)

    def infer(self, product: dict[str, Any]) -> list[str]:
        """Infer tags for a product. Returns deduplicated, validated tag list."""
        existing = set(product.get("tags", []))
        inferred: list[str] = list(existing)
        seen = set(existing)

        def _add(tag_id: str) -> None:
            if tag_id in self._valid_tags and tag_id not in seen:
                inferred.append(tag_id)
                seen.add(tag_id)

        def _add_many(tag_ids: list[str]) -> None:
            for t in tag_ids:
                _add(t)

        # 1. Text keyword matching (description + name)
        text = self._build_search_text(product)
        for pattern, tags in _COMPILED_RULES:
            if pattern.search(text):
                _add_many(tags)

        # 2. Category-based tags
        cat = product.get("category", "")
        if cat in _CATEGORY_TAGS:
            _add_many(_CATEGORY_TAGS[cat])

        # 3. Sub-category based tags
        sub = product.get("sub_category", "")
        if sub and sub in _SUBCAT_TAGS:
            _add_many(_SUBCAT_TAGS[sub])

        # 4. product_type based tags
        ptype = product.get("product_type", "")
        if ptype in _PRODUCT_TYPE_TAGS:
            _add_many(_PRODUCT_TYPE_TAGS[ptype])

        # 5. Structured field inference
        self._infer_from_structured(product, _add)

        # 6. Platform-based tags
        for platform in product.get("platforms", []):
            plat_lower = platform.lower()
            for key, tag in _PLATFORM_TAGS.items():
                if key in plat_lower:
                    _add(tag)

        # 7. Mutual exclusion: if structured field says closed-source, remove open-source
        #    (text keyword matching can false-positive on descriptions mentioning "open source")
        if product.get("open_source") is False and "closed-source" in seen:
            inferred = [t for t in inferred if t != "open-source"]

        # Cap at MAX_TAGS
        return inferred[:MAX_TAGS]

    @staticmethod
    def _build_search_text(product: dict[str, Any]) -> str:
        """Concatenate searchable text fields."""
        parts = [
            product.get("name", ""),
            product.get("description", ""),
            product.get("description_zh", ""),
            product.get("name_zh", ""),
        ]
        # Include keywords if present
        for kw in product.get("keywords", []):
            parts.append(kw)
        return " ".join(p for p in parts if p)

    @staticmethod
    def _infer_from_structured(product: dict[str, Any], add: Any) -> None:
        """Infer tags from structured fields (non-text)."""
        # open_source
        if product.get("open_source") is True:
            add("open-source")
        elif product.get("open_source") is False:
            add("closed-source")

        # Repository URL present implies open source orientation
        if product.get("repository_url"):
            add("open-source")

        # api_available
        if product.get("api_available") is True:
            add("api-service")

        # Pricing model
        pricing = product.get("pricing") or {}
        pricing_model = pricing.get("model", "")
        if pricing_model == "freemium":
            add("freemium")
        elif pricing_model == "open-source":
            add("open-source")
        elif pricing_model == "usage-based":
            add("usage-based")
        elif pricing_model == "enterprise":
            add("enterprise")

        # Architecture
        arch = (product.get("architecture") or "").lower()
        if "transformer" in arch:
            add("transformer")
        if "moe" in arch or "mixture" in arch:
            add("moe")
        if "diffusion" in arch:
            add("diffusion-model")
        if "cnn" in arch or "convolut" in arch:
            add("computer-vision")

        # Modalities → multimodal
        modalities = product.get("modalities", [])
        if len(modalities) > 1:
            add("multimodal")

        # Country → special tags
        country = product.get("company", {}).get("headquarters", {}).get("country", "")
        country_map = {
            "China": "china",
            "United States": "us",
            "Japan": "japan",
            "South Korea": "korea",
        }
        if country in country_map:
            add(country_map[country])

        european = {
            "United Kingdom",
            "Germany",
            "France",
            "Sweden",
            "Norway",
            "Finland",
            "Denmark",
            "Netherlands",
            "Belgium",
            "Switzerland",
            "Austria",
            "Italy",
            "Spain",
            "Portugal",
            "Ireland",
            "Poland",
            "Czech Republic",
            "Romania",
            "Hungary",
            "Estonia",
            "Latvia",
            "Lithuania",
        }
        if country in european:
            add("europe")

        # Funding valuation → unicorn/decacorn
        valuation = (
            product.get("company", {}).get("funding", {}).get("valuation_usd", 0) or 0
        )
        if valuation >= 10_000_000_000:
            add("decacorn")
        elif valuation >= 1_000_000_000:
            add("unicorn")

        # YC-backed detection
        sources = product.get("sources", [])
        for src in sources:
            if isinstance(src, dict) and "ycombinator" in (src.get("url", "") or ""):
                add("yc-backed")
                break
