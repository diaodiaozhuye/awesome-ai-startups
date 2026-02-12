# AI Product Data - 数据架构与采集策略设计 v2

## Context

重新设计 AI Product Data 项目的数据格式和采集流程。核心转变：**AI 产品是唯一核心实体**，公司和核心人员作为产品的内嵌属性存在，不单独建文件。同时引入数据源分层信任机制、发现驱动的爬取流程、AI 辅助数据补全、以及招聘信息采集。

---

## 一、核心数据架构：AI 产品为中心

### 1.1 目录结构

```
data/
  schema/
    product.schema.json       # 核心 schema
  products/                   # 每个 AI 产品一个 JSON 文件
    chatgpt.json
    claude.json
    cursor.json
    deepseek-chat.json
    ...
  archive/                    # 归档的非AI/废弃数据
  discovery_queue.json        # T4 发现的待丰富名单
  index.json                  # 生成：轻量产品列表供前端用
  stats.json                  # 生成：统计数据
  categories.json             # 分类定义（两级）
  tags.json                   # 标签定义
```

公司和人物不再有独立目录，全部内嵌在产品 JSON 中。

### 1.2 两级分类体系

**一级 category（~10 个大类）：**

| category | 说明 |
|----------|------|
| `ai-model` | 基础模型、开源模型 |
| `ai-app` | 面向终端用户的 AI 应用/SaaS |
| `ai-dev-tool` | 开发者工具、框架、SDK |
| `ai-infrastructure` | MLOps、推理平台、向量数据库 |
| `ai-hardware` | 芯片、加速器、边缘设备、机器人 |
| `ai-data` | 数据标注、数据集、数据管道 |
| `ai-agent` | 自主代理、Workflow 自动化 |
| `ai-search` | AI 搜索引擎 |
| `ai-security` | AI 安全、内容审核、对抗防御 |
| `ai-science` | AI for Science、药物发现、材料 |

**二级 sub_category（按大类细分）：**

- **ai-model**: `text-generation` / `image-generation` / `video-generation` / `audio-speech` / `code-generation` / `multimodal` / `embedding` / `3d-generation` / `music-generation`
- **ai-app**: `writing-copywriting` / `translation` / `customer-service` / `meeting-notes` / `design-creative` / `photo-editing` / `video-editing` / `presentation` / `email` / `sales-crm` / `marketing` / `hr-recruiting` / `legal` / `finance-accounting` / `healthcare-medical` / `education-tutoring` / `research` / `data-analysis` / `workflow-automation` / `voice-assistant` / `social-media` / `project-management` / `knowledge-base` / `content-moderation`
- **ai-dev-tool**: `coding-assistant` / `ai-framework` / `testing-qa` / `api-gateway` / `evaluation` / `fine-tuning` / `prompt-engineering` / `ai-deployment`
- **ai-infrastructure**: `inference-platform` / `vector-database` / `mlops` / `data-labeling` / `model-monitoring` / `compute-platform` / `feature-store`
- **ai-hardware**: `gpu-chip` / `inference-accelerator` / `edge-device` / `robot` / `autonomous-vehicle` / `sensor`
- **ai-agent**: `browser-agent` / `coding-agent` / `research-agent` / `personal-assistant` / `enterprise-agent` / `multi-agent-platform`

### 1.3 产品 JSON 完整字段定义

#### 产品身份

| 字段 | 类型 | 必填 | 说明 | 链接到 |
|------|------|------|------|--------|
| `slug` | string | 是 | 唯一标识，匹配文件名 | -- |
| `name` | string | 是 | 产品名称 | `product_url` |
| `name_zh` | string? | 否 | 中文名（英文品牌名不强行翻译，设为 null） | -- |
| `product_url` | uri | 是 | 产品官网/落地页 | 直接跳转 |
| `icon_url` | uri? | 否 | 产品图标（og:image / favicon） | -- |
| `description` | string | 是 | 英文简介（10-5000 字符） | -- |
| `description_zh` | string? | 否 | 中文简介（专业术语保留英文） | -- |
| `product_type` | enum | 是 | `llm / app / dev-tool / hardware / dataset / framework / api-service / other` | -- |
| `category` | enum | 是 | 一级分类 | -- |
| `sub_category` | string? | 否 | 二级细分场景 | -- |
| `tags` | string[] | 否 | 手动/AI 打的标签 | -- |
| `keywords` | string[] | 否 | 自动提取的中英文搜索关键词 | -- |

#### 公司信息（内嵌）

| 字段 | 类型 | 说明 | 链接到 |
|------|------|------|--------|
| `company.name` | string | 公司名 | `company.url` |
| `company.name_zh` | string? | 公司中文名（英文品牌不翻译） | -- |
| `company.url` | uri | 跳转链接（自动计算 fallback） | 直接跳转 |
| `company.website` | uri? | 公司官网 | -- |
| `company.wikipedia_url` | uri? | 维基百科页面 | -- |
| `company.logo_url` | uri? | 公司 Logo（Clearbit / og:image / favicon） | -- |
| `company.description` | string? | 公司简介 | -- |
| `company.founded_year` | int? | 成立年份（未知为 null） | -- |
| `company.headquarters` | object? | `{city?, country?, country_code?}` | -- |
| `company.funding` | object? | `{total_raised_usd?, last_round?, last_round_date?, valuation_usd?}` | -- |
| `company.employee_count_range` | string? | 如 `51-200` | -- |
| `company.social` | object? | `{linkedin?, crunchbase?, twitter?}` 各自可跳转 | 各自跳转 |

**company.url fallback 优先级**: `company.website` > `company.wikipedia_url` > `https://www.bing.com/search?q=公司名+AI`

#### 核心人员（内嵌数组）

| 字段 | 类型 | 说明 | 链接到 |
|------|------|------|--------|
| `key_people[].name` | string | 人名 | `profile_url` |
| `key_people[].title` | string | 职位 | -- |
| `key_people[].is_founder` | bool | 是否创始人 | -- |
| `key_people[].profile_url` | uri? | LinkedIn / 个人主页 / 智库 | 直接跳转 |

#### 技术规格

| 字段 | 类型 | 适用 | 说明 |
|------|------|------|------|
| `architecture` | string? | 模型 | 如 Transformer, Diffusion |
| `parameter_count` | string? | 模型 | 如 `70B`, `1.5T` |
| `context_window` | int? | 模型 | 最大 token 数 |
| `modalities` | string[] | 模型 | `text / image / audio / video / code / 3d` |
| `supported_languages` | string[] | 通用 | 支持的语言列表 |
| `training_data_cutoff` | date? | 模型 | 训练数据截止日期 |
| `platforms` | string[] | 通用 | `web / ios / android / api / desktop / cli / browser-extension` |
| `deployment_options` | string[] | 通用 | `cloud / on-premise / edge / hybrid` |
| `api_available` | bool? | 通用 | 是否提供 API |
| `api_docs_url` | uri? | 通用 | API 文档链接 -> 直接跳转 |

#### 开源信息与开发者生态

| 字段 | 类型 | 说明 | 链接到 |
|------|------|------|--------|
| `open_source` | bool? | 是否开源 | -- |
| `license` | string? | SPDX 标识 | -- |
| `repository_url` | uri? | 代码仓库 | GitHub/GitLab 跳转 |
| `github_stars` | int? | Star 数 | -- |
| `github_contributors` | int? | 贡献者数量 | -- |
| `github_last_commit` | date? | 最近提交日期（活跃度指标） | -- |
| `package_downloads` | object? | `{pypi_monthly?, npm_weekly?, docker_pulls?}` | -- |

#### 性能基准

| 字段 | 类型 | 说明 |
|------|------|------|
| `benchmarks` | object? | `{benchmark_name: score}` 如 `{"MMLU": 86.5}` |

#### 定价

| 字段 | 类型 | 说明 | 链接到 |
|------|------|------|--------|
| `pricing.model` | enum? | `free / freemium / paid / enterprise / open-source / usage-based` | -- |
| `pricing.has_free_tier` | bool? | 有无免费层 | -- |
| `pricing.input_price_per_1m_tokens` | number? | 输入价 | -- |
| `pricing.output_price_per_1m_tokens` | number? | 输出价 | -- |
| `pricing.url` | uri? | 定价页面 | 直接跳转 |

#### 市场定位

| 字段 | 类型 | 说明 |
|------|------|------|
| `target_audience` | string[] | `developers / enterprise / consumers / researchers / creators` |
| `use_cases` | string[] | 应用场景 |
| `integrations` | string[] | 集成的平台/工具 |

#### 产品关系

| 字段 | 类型 | 说明 |
|------|------|------|
| `competitors` | slug[] | 竞品 slug 列表 |
| `based_on` | slug[] | 上游依赖（如 ChatGPT 基于 GPT-4） |
| `used_by` | slug[] | 下游产品（如 GPT-4 被 Cursor 使用） |

#### 产品状态

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | enum | `active / beta / alpha / announced / deprecated / discontinued` |
| `release_date` | date? | 发布日期 |
| `last_update_date` | date? | 最近更新 |
| `version` | string? | 当前版本号 |

#### 社区与生态

| 字段 | 类型 | 链接到 |
|------|------|--------|
| `huggingface_url` | uri? | HuggingFace 页面 |
| `huggingface_downloads` | int? | -- |
| `discord_url` | uri? | Discord 社区 |
| `twitter` | string? | X/Twitter |
| `community_size` | string? | -- |
| `app_store` | object? | `{google_play_url?, apple_store_url?, rating?, downloads?, last_updated?}` |

#### 招聘信息

| 字段 | 类型 | 说明 | 链接到 |
|------|------|------|--------|
| `hiring.is_hiring` | bool | 是否在招聘 | -- |
| `hiring.total_positions` | int? | 岗位总数 | -- |
| `hiring.positions[]` | array | 岗位列表 | -- |
| `hiring.positions[].title` | string | 岗位名称 | -- |
| `hiring.positions[].location` | string | 工作地点 | -- |
| `hiring.positions[].url` | uri | 招聘链接 | 直接跳转 |
| `hiring.positions[].source` | string | 来源平台 | -- |
| `hiring.tech_stack` | string[] | 从 JD 中提取的技术栈 | -- |
| `hiring.last_checked` | date | 最近检查时间 | -- |

#### 数据来源（原始链接数组）

```json
"sources": [
  {"url": "https://...", "source_name": "official_website", "scraped_at": "2026-02-12"},
  {"url": "https://...", "source_name": "crunchbase", "scraped_at": "2026-02-10"}
]
```

#### 元数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `meta.added_date` | date | 首次收录 |
| `meta.last_updated` | date | 最近更新 |
| `meta.data_quality_score` | 0-1 | 数据完整度评分 |
| `meta.needs_review` | bool | AI 生成数据待人工审核 |
| `meta.provenance` | object | 字段级溯源 `{field: {source, tier, confidence}}` |

### 1.4 翻译规则

- 产品名本身是英文品牌（DeepSeek, Cursor, MiniMax）-> `name_zh = null`，不强行翻译
- 仅有官方中文名时才填（文心一言、通义千问、豆包）
- `description_zh` 中的专业术语保留英文（LLM, Transformer, Token）
- `category` / `sub_category` 全部使用英文 slug，前端展示层做本地化映射

---

## 二、数据源分层系统

| 层级 | 名称 | 信任度 | 合并优先级 | 需人工审核 | 用途 |
|------|------|--------|-----------|-----------|------|
| **T1** | 权威 API | 0.95 | 最高，可覆盖 T2-T4 | 否 | 结构化事实：总部、成立年份、创始人 |
| **T2** | 开放 Web | 0.75 | 中等，可覆盖 T3-T4 | 否 | 描述、模型信息、定价、开源状态 |
| **T3** | AI 生成 | 0.50 | 低，仅填空 | **是** | 分类、摘要、关键词、缺失字段推断 |
| **T4** | 辅助源 | 0.20 | 仅发现+招聘 | 否 | 发现新产品名称 + 采集招聘信息 |

### 数据源难度矩阵与技术方案

采用**混合策略**：免费 API 的数据源用免费方案，Hard 数据源通过 Firecrawl MCP 采集。

| 数据源 | 难度 | 决策 | 技术方案 | 认证 | 可靠字段 |
|--------|------|------|---------|------|---------|
| **T1 权威** | | | | | |
| Wikipedia/Wikidata | Easy | **使用** | SPARQL + httpx（免费） | 无 | company.founded_year, headquarters, key_people, wikipedia_url |
| Crunchbase (网页版) | Medium | **使用** | **Firecrawl**（绕过付费 API） | 无 | company.funding, founded_year, headquarters, employees, investors |
| **T2 开放 Web** | | | | | |
| HuggingFace | Easy | **使用** | `huggingface_hub` SDK（免费） | Token（可选） | architecture, parameter_count, context_window, benchmarks, license, downloads |
| Y Combinator | Easy-Med | **使用** | httpx + Algolia API（免费） | 无 | company.*, product_url, founded_year |
| Product Hunt | Medium | **使用** | httpx + GraphQL API（免费） | OAuth Token | name, description, product_url, key_people, tags |
| ArXiv | Easy | **使用** | `arxiv` Python 库（免费） | 无 | 论文元数据（标题、作者、摘要、发布日期） |
| Papers with Code | Medium | **使用** | **Firecrawl**（Cloudflare 防护） | 无 | benchmarks, paper links |
| 公司/产品官网 | Medium | **选择性** | httpx -> **Firecrawl** fallback | 无 | description, pricing, icon_url, api_docs_url, platforms |
| TechCrunch | Medium-Hard | **尝试** | **Firecrawl**（强 Cloudflare） | 无 | company.funding（融资新闻） |
| **T2 产品目录** | | | | | |
| There's An AI For That | Medium | **使用** | **Firecrawl** | 无 | 产品发现（14000+ AI 产品）、name, description, category, product_url |
| Toolify.ai | Medium | **使用** | **Firecrawl** | 无 | 产品发现、流量排名、分类 |
| AI集 (aiji.com) | Easy | **使用** | httpx（免费） | 无 | 中文 AI 产品发现、name, description, category |
| **T2 应用商店** | | | | | |
| Google Play | Easy | **使用** | google-play-scraper（免费） | 无 | 下载量、评分、更新频率、platforms |
| Apple App Store | Easy | **使用** | app-store-scraper（免费） | 无 | 下载量、评分、更新频率、platforms |
| **T2 开发者生态** | | | | | |
| PyPI | Easy | **使用** | 公开 JSON API（免费） | 无 | 包下载量（开发工具采用度指标） |
| npm | Easy | **使用** | 公开 Registry API（免费） | 无 | 包周下载量（JS/TS 工具采用度指标） |
| Docker Hub | Easy | **使用** | 公开 API（免费） | 无 | 镜像拉取量（AI 基础设施产品指标） |
| **T2 模型评测** | | | | | |
| LMSYS Chatbot Arena | Easy | **使用** | HuggingFace Dataset API（免费） | 无 | benchmarks（Elo 评分，最权威 LLM 排行） |
| OpenRouter | Easy | **使用** | 公开 API（免费） | 无 | pricing（模型定价）、可用性、调用统计 |
| Artificial Analysis | Medium | **使用** | **Firecrawl** | 无 | benchmarks（速度、价格、质量对比） |
| **T2 中文科技媒体** | | | | | |
| 36Kr | Medium | **使用** | **Firecrawl** | 无 | company.funding（中国 AI 融资新闻）、产品发现 |
| **T4 招聘** | | | | | |
| Indeed | Easy-Med | **使用** | **Firecrawl**（绕过 $3/次 API） | 无 | hiring.positions[], company_name |
| AI Jobs (aijobs.net) | Easy-Med | **使用** | httpx（免费） | 无 | hiring.positions[], company_name |
| Boss 直聘 | Med-Hard | **使用** | Scrapy + 代理池 | 无 | hiring.positions[], tech_stack, company_name |
| 猎聘 | Medium | **使用** | Scrapy + 代理池 | 无 | hiring.positions[], company_name |
| 拉勾 | Medium | **低优先** | Scrapy + 代理池 | 无 | hiring.positions[]（最强反爬中文站） |
| **已移除** | | | | | |
| LinkedIn Jobs | V.Hard | **移除** | -- | -- | Firecrawl 对 LinkedIn 效果差 + ToS 法律风险 |
| Glassdoor | Hard | **移除** | -- | -- | 登录墙后数据，Firecrawl 无法解决登录态 |
| IT桔子 | Hard | **移除** | -- | -- | 登录墙 + 付费数据，爬取成本高于价值 |

**技术方案分配：**
- **免费方案**（httpx / SDK / 专用库）：Wikidata, HuggingFace, YC, ArXiv, Product Hunt, AI Jobs, PyPI, npm, Docker Hub, LMSYS, OpenRouter, AI集, Google Play, App Store
- **Firecrawl MCP**：Crunchbase 网页版, Papers with Code, TechCrunch, Indeed, 官网 fallback, There's An AI For That, Toolify.ai, Artificial Analysis, 36Kr
- **Scrapy + 代理池**：Boss 直聘, 猎聘, 拉勾（中国站需中国代理节点）

### 实施优先级

**Phase 1（高 ROI，免费方案）：**
- Wikipedia/Wikidata（验证+丰富公司数据）
- HuggingFace（AI 模型/数据集，核心数据源）
- Y Combinator（AI 创业公司）
- ArXiv（论文+研究方向发现）
- LMSYS Chatbot Arena（LLM 排行榜，通过 HuggingFace Dataset API）

**Phase 2（中等 ROI，免费+Firecrawl 混合）：**
- Product Hunt（产品发现，免费 GraphQL）
- Crunchbase 网页版（Firecrawl，融资数据）
- AI Jobs（招聘发现，免费 httpx）
- 公司/产品官网（httpx -> Firecrawl fallback）
- PyPI / npm / Docker Hub（包下载量，全部免费 API）
- OpenRouter（模型定价与可用性，免费 API）

**Phase 3（产品目录 + 应用商店，批量发现）：**
- There's An AI For That（Firecrawl，14000+ 产品批量发现）
- Toolify.ai（Firecrawl，流量排名）
- AI集 aiji.com（httpx，中文产品目录）
- Google Play + App Store（专用库，移动端 AI 应用数据）

**Phase 4（媒体 + 评测扩展）：**
- Papers with Code（Firecrawl，benchmark 数据）
- TechCrunch（Firecrawl，融资新闻）
- Artificial Analysis（Firecrawl，模型速度/价格对比）
- 36Kr（Firecrawl，中国 AI 融资新闻）
- Indeed（Firecrawl，国际招聘）

**Phase 5（中国市场，Scrapy + 代理）：**
- Boss 直聘（中等难度，数据好）
- 猎聘（中等难度）
- 拉勾（最低优先，反爬最强）

### T3 AI 辅助补全

| 能力 | 输入 | 输出 | 模型 |
|------|------|------|------|
| 分类推断 | name + description | category + sub_category | Claude Haiku |
| 描述生成 | name + 官网内容 | description (en+zh) | Claude Sonnet |
| 关键词提取 | name + description + tags + use_cases | keywords[]（中英双语） | Claude Haiku |
| 标签提取 | description + product_type | tags[] | Claude Haiku |
| 翻译 | description (en) | description_zh（品牌名保留英文） | Claude Haiku |

所有 T3 数据自动设置 `needs_review=true`，永远不覆盖 T1/T2 数据。

### 技术栈

```python
# 核心采集
httpx                # API 请求（T1/T2 免费数据源）
firecrawl-py         # Firecrawl SDK（Hard 数据源，反爬绕过）
scrapy               # 招聘网站爬取（T4 中国站，需代理）

# 数据源专用 SDK
huggingface_hub      # HuggingFace 模型/数据集
arxiv                # ArXiv 论文
SPARQLWrapper        # Wikidata SPARQL 查询
PyGithub             # GitHub API（stars, contributors, license）
google-play-scraper  # Google Play 应用数据
app-store-scraper    # Apple App Store 应用数据

# 工具
tenacity             # 指数退避重试
ratelimit            # 速率限制装饰器
structlog            # 结构化日志
```

### 已移除数据源及原因

| 数据源 | 移除原因 |
|--------|---------|
| LinkedIn Jobs | ToS 明确禁止爬取，有法律诉讼先例，Firecrawl 对 LinkedIn 效果差 |
| Glassdoor | 登录墙后数据，Firecrawl 无法解决登录态问题 |

---

## 三、采集思维流程

### 阶段一：发现（Discovery）

目标：尽可能多地发现 AI 产品的"名字"，追求广度。

**搜索关键词矩阵**（存放在 `scrapers/data/search_keywords.json`，按平台分组）：

核心词（英文）：
- `AI`, `artificial intelligence`, `machine learning`, `ML`
- `deep learning`, `LLM`, `large language model`
- `generative AI`, `GenAI`, `GPT`, `transformer`

技术方向词：
- `computer vision`, `NLP`, `natural language processing`
- `speech recognition`, `TTS`, `text-to-speech`
- `diffusion model`, `reinforcement learning`
- `neural network`, `embedding`, `vector search`
- `RAG`, `retrieval augmented`

应用场景词：
- `chatbot`, `copilot`, `assistant`
- `autonomous`, `self-driving`, `robotics`
- `code generation`, `code completion`
- `image generation`, `text-to-image`
- `video generation`, `text-to-video`
- `content generation`, `recommendation system`

行业词：
- `MLOps`, `AIOps`, `AI infrastructure`
- `AI chip`, `AI accelerator`, `GPU`, `TPU`, `NPU`
- `edge AI`, `AI safety`, `AI alignment`, `AI agent`, `agentic`

中文关键词：
- `人工智能`, `大模型`, `大语言模型`
- `深度学习`, `机器学习`, `神经网络`
- `AIGC`, `AI生成`, `智能体`, `Agent`
- `自动驾驶`, `智能驾驶`, `具身智能`, `机器人`
- `算法`, `智能`, `智能化`

每个平台使用最适合的关键词子集：

```
多渠道并行扫描（使用关键词矩阵）
  == 产品目录站（批量发现，最高效） ==
  There's An AI    -> 14000+ AI 产品目录 -> 直接得到产品名 + 描述 + 分类 + URL
  Toolify.ai       -> AI 工具排行 -> 产品名 + 流量排名
  AI集 (aiji.com)  -> 中文 AI 产品目录 -> 国产 AI 产品发现

  == 垂直平台 ==
  Product Hunt     -> 搜关键词矩阵 -> 直接得到产品名 + 产品官网
  HuggingFace      -> 热门模型排行 -> 直接得到模型名 + 所属组织
  Y Combinator     -> AI/ML 标签公司 -> 得到公司名 -> 进入公司官网找产品
  Google Play/App Store -> 搜 AI 关键词 -> 移动端 AI 应用

  == 媒体/新闻 ==
  TechCrunch RSS   -> AI/ML 融资新闻 -> 提到的公司/产品名
  36Kr             -> 中国 AI 融资新闻 -> 国产 AI 公司/产品

  == 评测/排行 ==
  LMSYS Arena      -> LLM 排行榜 -> 所有参与评测的模型名
  OpenRouter       -> 可用模型列表 -> 模型名 + 所属组织

  == 招聘（T4 仅发现 + 招聘） ==
  Indeed           -> 搜关键词矩阵 -> 得到公司名
  AI Jobs          -> 同上
  Boss直聘/猎聘/拉勾 -> 中文关键词矩阵（中国市场）

  == 知识库 ==
  Wikidata SPARQL  -> AI 相关实体查询 -> 得到公司名 + 产品名
```

产出：`discovery_queue.json` -- 待处理的产品名列表。

### 阶段二：定位（Locate）

目标：拿到产品名后，找到它的"官方阵地"，像蜘蛛网一样扩散到所有相关页面。

```
拿到产品名 "Cursor"
  1. 搜索产品官网
       Bing 搜索 "Cursor AI" -> 找到 cursor.com
  2. 找到公司信息
       官网 About 页 -> 公司名 "Anysphere"
       Crunchbase 搜 "Anysphere" -> 融资、总部、创始人
       Wikipedia 搜 -> 如有则获取 wikipedia_url
  3. 定位所有可采集页面
       cursor.com              -> 产品描述、功能、定价
       cursor.com/pricing      -> 定价详情
       cursor.com/docs         -> API 文档链接
       linkedin.com/company/   -> 员工规模、核心人员、招聘信息
       crunchbase.com/org/     -> 融资轮次、估值
       producthunt.com/posts/  -> 社区评价
       huggingface.co/...      -> 模型信息（如有）
  4. 记录所有源 URL -> 存入 sources[] 数组
```

例如：在 LinkedIn 上发现一家公司招 AI 工程师 -> 查官网 -> 发现有 3 个 AI 产品 -> 每个产品建一个 JSON -> 每个 JSON 的 sources 里都记录最初的 LinkedIn 链接。

### 阶段三：采集（Scrape）

目标：从每个源页面提取对应字段，每个字段打上溯源标签。

```
产品官网（T2, httpx -> Playwright fallback）
  og:image / favicon     -> icon_url, company.logo_url
  meta description       -> description
  /pricing 页面           -> pricing.*
  /about 页面             -> company.description, key_people
  /docs 页面              -> api_docs_url
  结构化数据 JSON-LD      -> 多字段

Crunchbase API（T1, httpx）
  funding_rounds          -> company.funding.*
  founded_on              -> company.founded_year
  headquarters            -> company.headquarters.*
  num_employees_enum      -> company.employee_count_range
  founders                -> key_people[]

HuggingFace API（T2, httpx）
  model card              -> architecture, parameter_count, context_window
  downloads               -> huggingface_downloads
  license                 -> license
  tags                    -> modalities, tags
  eval results            -> benchmarks

Wikipedia/Wikidata（T1, httpx SPARQL）
  inception date          -> company.founded_year（验证/补充）
  headquarters location   -> company.headquarters（验证/补充）
  founders                -> key_people（验证/补充）
  article URL             -> company.wikipedia_url

Product Hunt（T2, httpx GraphQL）
  tagline                 -> description（备选）
  makers                  -> key_people[]
  topics                  -> tags
  thumbnail               -> icon_url（备选）

PyPI / npm / Docker Hub（T2, httpx）
  download stats          -> package_downloads.{pypi_monthly, npm_weekly, docker_pulls}

Google Play / App Store（T2, 专用库）
  rating                  -> app_store.rating
  downloads/installs      -> app_store.downloads
  store URL               -> app_store.{google_play_url, apple_store_url}
  last updated            -> app_store.last_updated

LMSYS Chatbot Arena（T2, HuggingFace Dataset API）
  elo rating              -> benchmarks.LMSYS_Elo
  ranking                 -> benchmarks 补充

OpenRouter（T2, httpx）
  pricing                 -> pricing.{input/output_price_per_1m_tokens}
  context length          -> context_window（验证/补充）

There's An AI For That / Toolify.ai（T2, Firecrawl）
  product listing         -> 触发新一轮"定位"流程（批量发现）
  category/tags           -> category, sub_category, tags（参考值）

36Kr（T2, Firecrawl）
  funding news            -> company.funding（中国市场）
  company info            -> company.*

招聘网站（T4）
  company_name            -> 触发新一轮"定位"流程
  job listings            -> hiring.positions[]
  JD 内容                 -> hiring.tech_stack（自动提取）
```

### 阶段四：去重与合并（Deduplicate & Merge）

目标：判断是新产品还是已有产品，新数据合并到旧数据。

```
采到一个产品 "Cursor IDE"
  Step 1: slug 匹配
    slugify("Cursor IDE") -> "cursor-ide"
    检查 data/products/cursor-ide.json 或 cursor.json
  Step 2: URL 匹配
    product_url = "cursor.com"
    遍历所有已有产品的 product_url
  Step 3: 名称模糊匹配
    "Cursor IDE" vs 已有 "Cursor" -> 相似度 0.88 > 阈值 0.85
  判定：已有产品 -> 执行合并
```

合并规则（分层覆盖）：
- T1 数据可覆盖 T2-T4 数据
- 同层级保留已有值（先到先得）
- T3 仅填充空字段，永不覆盖
- T4 不参与字段合并（仅发现+招聘）
- 每次字段写入记录溯源

### 阶段五：AI 补全（Enrich）

目标：用 LLM 填充采集不到的字段。

```
找出 data_quality_score < 0.5 的产品
  缺 category/sub_category -> Claude Haiku 推断，标记 needs_review
  缺 keywords             -> Claude Haiku 提取中英文关键词
  缺 description_zh       -> Claude Haiku 翻译（品牌名保留英文）
  缺 use_cases            -> 根据描述推断
```

### 阶段六：校验（Validate）

```
1. Schema 校验    -> 每个 JSON 符合 product.schema.json
2. 完整性校验    -> company.url 不为空（至少有 Bing fallback）
3. 引用校验      -> competitors/based_on/used_by 的 slug 都存在
4. 合理性校验    -> founded_year 不是默认值，country 不含脏数据
5. 重新计算      -> data_quality_score
6. 生成          -> index.json + stats.json
```

---

## 四、技术方案

### 4.0 爬取核心原则：慢而稳

**不追求速度，追求稳定和数据质量。** 所有爬取任务以"礼貌爬虫"为基本准则。

```
速率控制（全局默认）：
  单域名请求间隔    >= 5 秒（非必要不低于此值）
  并发连接数        = 1（串行请求，不做并发）
  每日爬取上限      按数据源分配（见下表）
  遇到 429/503      指数退避，最长等待 5 分钟后重试
  连续失败 3 次     跳过该目标，记录日志，下次调度再试

每日爬取配额建议：
  Firecrawl 数据源   ~100 页/天（月 3,000 页 / 30 天）
  免费 API 数据源    ~500 请求/天（远低于各 API 限额）
  Scrapy 中国站      ~200 页/天（配合长延迟 5-10 秒）

调度策略：
  使用 cron 每日定时运行，不需要实时爬取
  每次运行处理一批数据源，轮换执行
  新产品发现 vs 已有数据更新 分开调度
  全量爬取（如 TAAFT 14000+）可分 2-3 周完成
```

这种策略的好处：
- 几乎不会被封禁，大部分站点甚至不需要代理
- Firecrawl Hobby $16/月完全够用
- 数据积累是渐进式的，每天增长一点
- 出问题容易定位和修复（串行日志清晰）

### 4.1 混合爬取策略

```
官方 SDK（T1/T2 首选）-> huggingface_hub, arxiv, SPARQLWrapper
  HuggingFace, ArXiv, Wikidata
  SDK 内置速率管理和重试

免费 API 数据源（T2）-> httpx (async)
  YC (Algolia), Product Hunt (GraphQL), OpenRouter, LMSYS (HF Dataset)
  PyPI JSON API, npm Registry API, Docker Hub API
  AI集 (aiji.com)
  统一速率限制、重试、缓存

应用商店（T2）-> 专用库
  Google Play (google-play-scraper), App Store (app-store-scraper)
  按关键词批量搜索 AI 应用

Firecrawl MCP（T1/T2 反爬站点）-> firecrawl-py
  Crunchbase, Papers with Code, TechCrunch, Indeed
  There's An AI For That, Toolify.ai, Artificial Analysis, 36Kr
  公司/产品官网 fallback（httpx 失败时）

动态页面（T2 官网）-> httpx 优先，Firecrawl fallback
  先用 httpx，遇 403/验证码 -> 切 Firecrawl
  尊重 robots.txt，3秒/请求/域名

招聘网站（T4 中国）-> Scrapy（慢速模式，代理可选）
  Boss 直聘, 猎聘, 拉勾
  串行请求 + 5-10秒延迟 + User-Agent 轮换
  慢速模式下大部分场景不需要代理池

招聘网站（T4 国际）-> httpx
  AI Jobs (aijobs.net)
  2-5秒延迟，检查 robots.txt
```

### 4.2 分层合并规则（TieredMerger）

```
规则 1: T1 数据可覆盖 T2-T4 数据
规则 2: 同层级数据保留已有值（先到先得）
规则 3: T3 仅填充空字段，永不覆盖
规则 4: T4 仅贡献 hiring.* 和发现名称
规则 5: 每次字段写入记录溯源（source, tier, confidence, updated_at）
```

### 4.3 核心模块

| 文件 | 职责 |
|------|------|
| `scrapers/base.py` | 重写：ScrapedProduct + DiscoveredName + SourceTier |
| `scrapers/enrichment/merger.py` | 重写：TieredMerger，分层合并+溯源 |
| `scrapers/enrichment/llm_enricher.py` | 新增：LLM 批量补全（Anthropic Batch API） |
| `scrapers/enrichment/quality_scorer.py` | 新增：加权字段完整度评分 |
| `scrapers/enrichment/keyword_extractor.py` | 新增：中英文关键词自动提取 |
| `scrapers/enrichment/normalizer.py` | 扩展：PlausibilityValidator 拒绝脏数据 |
| `scrapers/enrichment/icon_fetcher.py` | 新增：产品/公司 icon 采集 |
| `scrapers/validation/schema_validator.py` | 重写：验证产品 schema |
| `scrapers/validation/integrity_validator.py` | 新增：跨产品引用完整性检查 |
| `scrapers/sources/wikidata.py` | 新增：Wikidata T1（SPARQL + REST） |
| `scrapers/sources/huggingface.py` | 新增：HuggingFace T2（huggingface_hub SDK） |
| `scrapers/sources/arxiv_scraper.py` | 新增：ArXiv T2（arxiv Python 库） |
| `scrapers/sources/crunchbase.py` | 重写：Crunchbase T1（Firecrawl 网页版） |
| `scrapers/sources/papers_with_code.py` | 新增：Papers with Code T2（Firecrawl） |
| `scrapers/sources/techcrunch.py` | 重写：TechCrunch T2（Firecrawl） |
| `scrapers/sources/company_website.py` | 新增：官网爬取 T2（httpx -> Firecrawl fallback） |
| `scrapers/sources/indeed.py` | 重写：Indeed T4（Firecrawl，发现+招聘） |
| `scrapers/sources/aijobs.py` | 重写：AI Jobs T4（httpx，发现+招聘） |
| `scrapers/sources/zhipin.py` | 重写：Boss 直聘 T4（Scrapy + 代理） |
| `scrapers/sources/liepin.py` | 重写：猎聘 T4（Scrapy + 代理） |
| `scrapers/sources/theresanai.py` | 新增：There's An AI For That T2（Firecrawl 批量发现） |
| `scrapers/sources/toolify.py` | 新增：Toolify.ai T2（Firecrawl 排行） |
| `scrapers/sources/aiji.py` | 新增：AI集 T2（httpx，中文产品目录） |
| `scrapers/sources/lmsys.py` | 新增：LMSYS Chatbot Arena T2（HuggingFace Dataset API） |
| `scrapers/sources/openrouter.py` | 新增：OpenRouter T2（公开 API） |
| `scrapers/sources/artificial_analysis.py` | 新增：Artificial Analysis T2（Firecrawl） |
| `scrapers/sources/app_stores.py` | 新增：Google Play + App Store T2（专用库） |
| `scrapers/sources/package_registries.py` | 新增：PyPI/npm/Docker Hub T2（公开 API） |
| `scrapers/sources/36kr.py` | 新增：36Kr T2（Firecrawl，中国科技媒体） |
| `scrapers/utils/firecrawl_client.py` | 新增：Firecrawl MCP 统一客户端封装 |

---

## 五、迁移策略

### Step 1: 数据清洗
- 清理损坏的国家字段、默认年份、ai-other 分类、空 website

### Step 2: 转换为产品 JSON
- 从原 106 个公司文件中，提取有明确产品的转为 `data/products/<slug>.json`
- 公司信息内嵌到对应产品中
- 创始人信息内嵌到 key_people
- 无明确产品的公司暂存 archive

### Step 3: AI 补全
- 对转换后的产品数据运行 LLM 补全分类、关键词、描述

### Step 4: 校验与生成
- 全量 schema 校验 + 引用校验
- 生成 index.json + stats.json

---

## 六、新增依赖

```toml
# 核心采集
httpx>=0.27            # API 请求（免费数据源）
firecrawl-py>=1.0      # Firecrawl SDK（Hard 数据源：Crunchbase/PapersWithCode/TechCrunch/Indeed/TAAFT/Toolify/36Kr/官网fallback）
scrapy>=2.11           # 招聘网站爬取（T4 中国站，需代理）
lxml>=5.0              # HTML 解析

# 数据源专用 SDK
huggingface_hub>=0.20  # HuggingFace 模型/数据集
arxiv>=2.1             # ArXiv 论文
SPARQLWrapper>=2.0     # Wikidata SPARQL
google-play-scraper>=1.2  # Google Play 应用数据
app-store-scraper>=0.3    # Apple App Store 应用数据

# AI 补全
anthropic>=0.30        # T3 LLM 补全（Batch API）

# 工具
tenacity>=8.2          # 指数退避重试
structlog>=24.0        # 结构化日志
```

Firecrawl 用量预估（Standard $83/月 = 50,000 credits）：
- Crunchbase: ~200 页/月（已有公司更新 + 新发现）
- Papers with Code: ~100 页/月（benchmark 更新）
- TechCrunch: ~300 页/月（融资新闻）
- Indeed: ~500 页/月（招聘信息）
- 官网 fallback: ~500 页/月（httpx 失败时使用）
- There's An AI For That: ~500 页/月（产品目录批量爬取）
- Toolify.ai: ~200 页/月（排行榜）
- Artificial Analysis: ~100 页/月（模型评测数据）
- 36Kr: ~200 页/月（中国融资新闻）
- 总计 ~2,600 页/月，Hobby $16/月（3,000 页）仍可覆盖
- 如产品目录初次全量爬取（TAAFT 14000+），建议首月升级 Standard 或分批爬取

---

## 七、验证方式

1. `aiscrape validate` -- 验证所有产品 JSON + 引用完整性
2. `pytest tests/ -v --cov=scrapers` -- 80%+ 覆盖率
3. `ruff check scrapers/ && mypy scrapers/` -- 代码质量
4. 迁移后对比：分类合理性、数据完整度提升
5. 网站 `npm run build` -- 静态导出正常

---

## 八、成功标准

- [ ] AI 产品为核心实体，公司/人员内嵌
- [ ] 每个可链接字段带 URL（公司名 -> 官网/维基/Bing）
- [ ] 采集原始链接存入 sources[] 数组
- [ ] 两级分类体系覆盖所有 AI 产品场景
- [ ] 跨源去重 + 分层合并防止低质数据覆盖
- [ ] 发现驱动爬取流程（线索 -> 定位 -> 采集 -> 合并）
- [ ] 中英文关键词自动提取
- [ ] 产品/公司 icon 自动采集
- [ ] 招聘信息内嵌（岗位、技术栈）
- [ ] 中文品牌英文名不强行翻译
- [ ] 开发者生态指标采集（包下载量, 应用商店评分）
- [ ] 产品目录站批量发现（TAAFT/Toolify/AI集）
- [ ] LLM 排行榜数据集成（LMSYS Elo, OpenRouter pricing）
- [ ] 测试覆盖率 >= 80%
