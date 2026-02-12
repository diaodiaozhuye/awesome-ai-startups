"""Package registry scrapers for developer ecosystem adoption metrics.

T2 Open Web sources — enrich existing products with download/pull
statistics from PyPI, npm, and Docker Hub. These are enrichment-only
scrapers: they look up known package names rather than discovering new products.
"""

from __future__ import annotations

import logging
import time

import httpx

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PyPI
# ---------------------------------------------------------------------------

PYPI_JSON_API = "https://pypi.org/pypi/{package}/json"
PYPISTATS_API = "https://pypistats.org/api/packages/{package}/recent"

# Well-known AI packages to track
PYPI_AI_PACKAGES: list[dict[str, str]] = [
    {"package": "transformers", "product": "Transformers", "org": "Hugging Face"},
    {"package": "torch", "product": "PyTorch", "org": "Meta"},
    {"package": "tensorflow", "product": "TensorFlow", "org": "Google"},
    {"package": "langchain", "product": "LangChain", "org": "LangChain"},
    {"package": "openai", "product": "OpenAI Python SDK", "org": "OpenAI"},
    {"package": "anthropic", "product": "Anthropic Python SDK", "org": "Anthropic"},
    {"package": "diffusers", "product": "Diffusers", "org": "Hugging Face"},
    {"package": "datasets", "product": "HuggingFace Datasets", "org": "Hugging Face"},
    {
        "package": "sentence-transformers",
        "product": "Sentence Transformers",
        "org": "Hugging Face",
    },
    {"package": "gradio", "product": "Gradio", "org": "Hugging Face"},
    {"package": "streamlit", "product": "Streamlit", "org": "Snowflake"},
    {"package": "chromadb", "product": "ChromaDB", "org": "Chroma"},
    {"package": "pinecone-client", "product": "Pinecone", "org": "Pinecone"},
    {"package": "weaviate-client", "product": "Weaviate", "org": "Weaviate"},
    {"package": "qdrant-client", "product": "Qdrant", "org": "Qdrant"},
    {"package": "llama-index", "product": "LlamaIndex", "org": "LlamaIndex"},
    {"package": "vllm", "product": "vLLM", "org": "vLLM"},
    {"package": "mlflow", "product": "MLflow", "org": "Databricks"},
    {"package": "wandb", "product": "Weights & Biases", "org": "Weights & Biases"},
    {"package": "ray", "product": "Ray", "org": "Anyscale"},
    {"package": "ultralytics", "product": "Ultralytics YOLOv8", "org": "Ultralytics"},
    {"package": "keras", "product": "Keras", "org": "Google"},
    {"package": "fastai", "product": "fast.ai", "org": "fast.ai"},
    {"package": "spacy", "product": "spaCy", "org": "Explosion"},
    {"package": "huggingface-hub", "product": "HuggingFace Hub", "org": "Hugging Face"},
]


class PyPIScraper(BaseScraper):
    """Scrape PyPI for AI package download statistics.

    Uses the public PyPI JSON API and pypistats API to fetch
    monthly download counts for known AI/ML Python packages.
    """

    @property
    def source_name(self) -> str:
        return "pypi"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Fetch download stats for known AI packages from PyPI."""
        client = create_http_client(timeout=15)
        products: list[ScrapedProduct] = []

        try:
            for pkg_info in PYPI_AI_PACKAGES[:limit]:
                product = self._fetch_package(client, pkg_info)
                if product:
                    products.append(product)
                time.sleep(DEFAULT_REQUEST_DELAY)
        finally:
            client.close()

        return products

    def _fetch_package(
        self,
        client: httpx.Client,
        pkg_info: dict[str, str],
    ) -> ScrapedProduct | None:
        """Fetch metadata and download stats for a single PyPI package."""
        package = pkg_info["package"]

        # Fetch package metadata
        try:
            meta_resp = client.get(PYPI_JSON_API.format(package=package))
            if not meta_resp.is_success:
                logger.debug(
                    "PyPI metadata %s: HTTP %s", package, meta_resp.status_code
                )
                return None

            meta = meta_resp.json()
            info = meta.get("info", {})
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, OSError) as exc:
            logger.debug("PyPI metadata %s: request failed: %s", package, exc)
            return None

        # Fetch recent download stats
        monthly_downloads: int | None = None
        try:
            time.sleep(1)  # Be gentle with pypistats
            stats_resp = client.get(PYPISTATS_API.format(package=package))
            if stats_resp.is_success:
                stats = stats_resp.json()
                monthly_downloads = stats.get("data", {}).get("last_month")
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, OSError):
            logger.debug("PyPI download stats unavailable for %s", package)
            # Downloads are optional enrichment data

        description = info.get("summary") or info.get("description", "")[:200]
        homepage = info.get("home_page") or info.get("project_url") or ""
        repo_url = _extract_repo_url(info.get("project_urls") or {})
        license_name = info.get("license") or ""

        extra: dict[str, str] = {"pypi_package": package}
        if monthly_downloads is not None:
            extra["pypi_monthly_downloads"] = str(monthly_downloads)

        return ScrapedProduct(
            name=pkg_info["product"],
            source="pypi",
            source_url=f"https://pypi.org/project/{package}/",
            source_tier=SourceTier.T2_OPEN_WEB,
            product_url=homepage or f"https://pypi.org/project/{package}/",
            description=description,
            product_type="framework",
            category="ai-dev-tool",
            sub_category="ai-framework",
            tags=("python", "open-source"),
            company_name=pkg_info.get("org"),
            open_source=True,
            license=license_name or None,
            repository_url=repo_url,
            platforms=("api", "cli"),
            status="active",
            extra=extra,
        )


# ---------------------------------------------------------------------------
# npm
# ---------------------------------------------------------------------------

NPM_REGISTRY_URL = "https://registry.npmjs.org/{package}"
NPM_DOWNLOADS_URL = "https://api.npmjs.org/downloads/point/last-week/{package}"

NPM_AI_PACKAGES: list[dict[str, str]] = [
    {"package": "openai", "product": "OpenAI Node SDK", "org": "OpenAI"},
    {
        "package": "@anthropic-ai/sdk",
        "product": "Anthropic Node SDK",
        "org": "Anthropic",
    },
    {"package": "langchain", "product": "LangChain.js", "org": "LangChain"},
    {
        "package": "@huggingface/inference",
        "product": "HuggingFace Inference JS",
        "org": "Hugging Face",
    },
    {"package": "llamaindex", "product": "LlamaIndex.TS", "org": "LlamaIndex"},
    {"package": "ai", "product": "Vercel AI SDK", "org": "Vercel"},
    {"package": "@tensorflow/tfjs", "product": "TensorFlow.js", "org": "Google"},
    {"package": "onnxruntime-web", "product": "ONNX Runtime Web", "org": "Microsoft"},
    {"package": "replicate", "product": "Replicate Node SDK", "org": "Replicate"},
    {
        "package": "@pinecone-database/pinecone",
        "product": "Pinecone Node SDK",
        "org": "Pinecone",
    },
    {"package": "chromadb", "product": "ChromaDB JS", "org": "Chroma"},
    {"package": "cohere-ai", "product": "Cohere Node SDK", "org": "Cohere"},
]


class NpmScraper(BaseScraper):
    """Scrape npm registry for AI package weekly download statistics."""

    @property
    def source_name(self) -> str:
        return "npm"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Fetch download stats for known AI packages from npm."""
        client = create_http_client(timeout=15)
        products: list[ScrapedProduct] = []

        try:
            for pkg_info in NPM_AI_PACKAGES[:limit]:
                product = self._fetch_package(client, pkg_info)
                if product:
                    products.append(product)
                time.sleep(DEFAULT_REQUEST_DELAY)
        finally:
            client.close()

        return products

    def _fetch_package(
        self,
        client: httpx.Client,
        pkg_info: dict[str, str],
    ) -> ScrapedProduct | None:
        """Fetch metadata and download stats for a single npm package."""
        package = pkg_info["package"]

        try:
            meta_resp = client.get(NPM_REGISTRY_URL.format(package=package))
            if not meta_resp.is_success:
                return None
            meta = meta_resp.json()
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, OSError) as exc:
            logger.debug("npm metadata %s: request failed: %s", package, exc)
            return None

        # Weekly downloads
        weekly_downloads: int | None = None
        try:
            time.sleep(1)
            dl_resp = client.get(NPM_DOWNLOADS_URL.format(package=package))
            if dl_resp.is_success:
                weekly_downloads = dl_resp.json().get("downloads")
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, OSError):
            logger.debug("npm download stats unavailable for %s", package)

        description = meta.get("description", "")
        homepage = meta.get("homepage") or ""
        repo = meta.get("repository", {})
        repo_url = repo.get("url", "") if isinstance(repo, dict) else ""
        if repo_url.startswith("git+"):
            repo_url = repo_url[4:]
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        license_name = meta.get("license") or ""

        extra: dict[str, str] = {"npm_package": package}
        if weekly_downloads is not None:
            extra["npm_weekly_downloads"] = str(weekly_downloads)

        return ScrapedProduct(
            name=pkg_info["product"],
            source="npm",
            source_url=f"https://www.npmjs.com/package/{package}",
            source_tier=SourceTier.T2_OPEN_WEB,
            product_url=homepage or f"https://www.npmjs.com/package/{package}",
            description=description,
            product_type="framework",
            category="ai-dev-tool",
            sub_category="ai-framework",
            tags=("javascript", "open-source"),
            company_name=pkg_info.get("org"),
            open_source=True,
            license=license_name or None,
            repository_url=repo_url or None,
            platforms=("api", "web"),
            status="active",
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Docker Hub
# ---------------------------------------------------------------------------

DOCKERHUB_API = "https://hub.docker.com/v2/repositories/{namespace}/{repo}/"

DOCKER_AI_IMAGES: list[dict[str, str]] = [
    {"namespace": "vllm", "repo": "vllm-openai", "product": "vLLM", "org": "vLLM"},
    {"namespace": "ollama", "repo": "ollama", "product": "Ollama", "org": "Ollama"},
    {
        "namespace": "huggingface",
        "repo": "text-generation-inference",
        "product": "TGI",
        "org": "Hugging Face",
    },
    {"namespace": "chromadb", "repo": "chroma", "product": "ChromaDB", "org": "Chroma"},
    {"namespace": "qdrant", "repo": "qdrant", "product": "Qdrant", "org": "Qdrant"},
    {"namespace": "milvusdb", "repo": "milvus", "product": "Milvus", "org": "Zilliz"},
    {
        "namespace": "weaviate",
        "repo": "weaviate",
        "product": "Weaviate",
        "org": "Weaviate",
    },
    {"namespace": "pytorch", "repo": "pytorch", "product": "PyTorch", "org": "Meta"},
    {
        "namespace": "tensorflow",
        "repo": "tensorflow",
        "product": "TensorFlow",
        "org": "Google",
    },
    {
        "namespace": "nvidia",
        "repo": "tritonserver",
        "product": "Triton Inference Server",
        "org": "NVIDIA",
    },
    {"namespace": "localai", "repo": "localai", "product": "LocalAI", "org": "LocalAI"},
]


class DockerHubScraper(BaseScraper):
    """Scrape Docker Hub for AI container image pull statistics."""

    @property
    def source_name(self) -> str:
        return "dockerhub"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Fetch pull counts for known AI Docker images."""
        client = create_http_client(timeout=15)
        products: list[ScrapedProduct] = []

        try:
            for img_info in DOCKER_AI_IMAGES[:limit]:
                product = self._fetch_image(client, img_info)
                if product:
                    products.append(product)
                time.sleep(DEFAULT_REQUEST_DELAY)
        finally:
            client.close()

        return products

    def _fetch_image(
        self,
        client: httpx.Client,
        img_info: dict[str, str],
    ) -> ScrapedProduct | None:
        """Fetch metadata for a single Docker Hub image."""
        namespace = img_info["namespace"]
        repo = img_info["repo"]

        try:
            resp = client.get(DOCKERHUB_API.format(namespace=namespace, repo=repo))
            if not resp.is_success:
                return None
            data = resp.json()
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, OSError) as exc:
            logger.debug(
                "Docker Hub metadata %s/%s: request failed: %s", namespace, repo, exc
            )
            return None

        pull_count = data.get("pull_count", 0)
        star_count = data.get("star_count", 0)
        description = data.get("description") or data.get("full_description", "")[:200]

        extra: dict[str, str] = {
            "docker_image": f"{namespace}/{repo}",
            "docker_pulls": str(pull_count),
            "docker_stars": str(star_count),
        }

        return ScrapedProduct(
            name=img_info["product"],
            source="dockerhub",
            source_url=f"https://hub.docker.com/r/{namespace}/{repo}",
            source_tier=SourceTier.T2_OPEN_WEB,
            product_url=f"https://hub.docker.com/r/{namespace}/{repo}",
            description=description,
            product_type="framework",
            category="ai-infrastructure",
            sub_category="inference-platform",
            tags=("docker", "open-source", "infrastructure"),
            company_name=img_info.get("org"),
            open_source=True,
            platforms=("api", "cli", "desktop"),
            status="active",
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_repo_url(project_urls: dict[str, str]) -> str | None:
    """Extract repository URL from PyPI project_urls dict."""
    for key in ("Source", "Source Code", "Repository", "GitHub", "Homepage"):
        url = project_urls.get(key, "")
        if url and ("github.com" in url or "gitlab.com" in url):
            return url
    return None
