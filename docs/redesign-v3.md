# AI Product Data 重新设计方案 v3

> 状态：**草案** | 日期：2026-02-14
>
> 本文档是独立的新设计方案，不替代 `docs/design-plan.md`（现行设计）。
> 待实施验证后再合并。

## Context

当前系统存在三个核心问题：

1. **数据冗余**：`data/companies/`（106 文件）和 `data/products/`（223 文件）并存，公司信息在产品 JSON 中完整内嵌，`companies/` 是冗余的
2. **分类混乱**：Company schema 用 17 个分类，Product schema 用另外 10 个分类，两套体系不一致
3. **采集质量参差**：28 个 scraper 质量差异极大，ArXiv 抓论文不是产品，Job scraper 产出噪声多

本方案将数据模型统一为纯产品中心、合并分类体系并大幅扩展标签维度、重建采集管道引入 Discovery/Enrichment 两阶段架构和 LLM 辅助分类。

---

## Phase 1: 分类与标签体系

### 新主分类（11 个，互斥）

| ID | English | 中文 | 合并自 |
|----|---------|------|--------|
| `ai-foundation-model` | AI Foundation Model | AI 基础模型 | ai-model, llm-foundation-model |
| `ai-application` | AI Application | AI 应用 | ai-app, ai-assistant, ai-gaming, ai-other, ai-agent（面向用户的 agent） |
| `ai-creative-media` | AI Creative & Media | AI 创意与媒体 | ai-image-video, ai-audio-speech |
| `ai-dev-platform` | AI Dev Platform | AI 开发平台 | ai-dev-tool, ai-coding, ai-agent（agent 框架/平台） |
| `ai-infrastructure` | AI Infrastructure | AI 基础设施 | 不变 |
| `ai-data-platform` | AI Data Platform | AI 数据平台 | ai-data, ai-data-analytics |
| `ai-search-retrieval` | AI Search & Retrieval | AI 搜索与检索 | ai-search |
| `ai-hardware` | AI Hardware & Robotics | AI 硬件与机器人 | ai-hardware, ai-robotics, autonomous-vehicles |
| `ai-security-governance` | AI Security & Governance | AI 安全与治理 | ai-security, ai-security-defense |
| `ai-science-research` | AI for Science | AI 科学研究 | ai-science |
| `ai-enterprise-vertical` | AI Enterprise Vertical | AI 行业垂直 | ai-enterprise, ai-healthcare, ai-education, ai-finance |

**ai-agent 拆分规则**: 面向终端用户的 agent 产品（浏览器智能体、个人助手等）→ `ai-application`；agent 开发框架/多智能体平台 → `ai-dev-platform`。用 `agents` 标签统一标识。

### 多维标签体系（~114 个标签，7 维度，双语）

产品 JSON 中 `tags` 字段存 `id`（英文 slug），网站通过 `localized()` 查找 `name_zh` 展示中文。

**`data/tags.json` 新结构：**
```json
{
  "version": "2.0",
  "dimensions": {
    "technology": {
      "name": "Technology", "name_zh": "技术栈",
      "tags": [
        {"id": "transformer", "name": "Transformer", "name_zh": "Transformer 架构"},
        ...
      ]
    }
  }
}
```

#### technology — 技术栈（24 个）

| id | name | name_zh |
|----|------|---------|
| transformer | Transformer | Transformer 架构 |
| diffusion-model | Diffusion Model | 扩散模型 |
| rag | RAG | 检索增强生成 |
| multimodal | Multimodal | 多模态 |
| nlp | NLP | 自然语言处理 |
| computer-vision | Computer Vision | 计算机视觉 |
| reinforcement-learning | Reinforcement Learning | 强化学习 |
| fine-tuning | Fine-tuning | 模型微调 |
| embedding | Embedding | 向量嵌入 |
| speech-to-text | Speech to Text | 语音转文字 |
| text-to-image | Text to Image | 文生图 |
| text-to-video | Text to Video | 文生视频 |
| text-to-speech | Text to Speech | 文字转语音 |
| text-to-3d | Text to 3D | 文生3D |
| text-to-music | Text to Music | 文生音乐 |
| code-generation | Code Generation | 代码生成 |
| prompt-engineering | Prompt Engineering | 提示工程 |
| image-to-video | Image to Video | 图生视频 |
| graph-neural-network | Graph Neural Network | 图神经网络 |
| neuro-symbolic | Neuro-Symbolic | 神经符号 |
| moe | Mixture of Experts | 混合专家 |
| quantization | Quantization | 量化 |
| distillation | Distillation | 蒸馏 |
| federated-learning | Federated Learning | 联邦学习 |

#### use_case — 应用场景（30 个）

| id | name | name_zh |
|----|------|---------|
| chatbot | Chatbot | 聊天机器人 |
| copilot | Copilot | 编程助手 |
| writing-assistant | Writing Assistant | 写作助手 |
| data-analysis | Data Analysis | 数据分析 |
| content-creation | Content Creation | 内容创作 |
| customer-support | Customer Support | 客户服务 |
| search-engine | Search Engine | 搜索引擎 |
| workflow-automation | Workflow Automation | 工作流自动化 |
| marketing | Marketing | 营销 |
| translation | Translation | 翻译 |
| meeting-notes | Meeting Notes | 会议纪要 |
| design-creative | Design & Creative | 设计创意 |
| photo-editing | Photo Editing | 图片编辑 |
| video-editing | Video Editing | 视频编辑 |
| voice-assistant | Voice Assistant | 语音助手 |
| personal-assistant | Personal Assistant | 个人助手 |
| knowledge-base | Knowledge Base | 知识库 |
| research | Research | 研究 |
| testing-qa | Testing & QA | 测试与质量保证 |
| code-review | Code Review | 代码审查 |
| presentation | Presentation | 演示文稿 |
| email | Email | 邮件 |
| sales-crm | Sales & CRM | 销售与CRM |
| hr-recruiting | HR & Recruiting | 人力资源与招聘 |
| project-management | Project Management | 项目管理 |
| content-moderation | Content Moderation | 内容审核 |
| social-media | Social Media | 社交媒体 |
| legal-assist | Legal Assist | 法律辅助 |
| finance-accounting | Finance & Accounting | 财务会计 |
| education-tutoring | Education & Tutoring | 教育辅导 |

#### domain — 行业领域（20 个）

| id | name | name_zh |
|----|------|---------|
| healthcare | Healthcare | 医疗健康 |
| drug-discovery | Drug Discovery | 药物发现 |
| medical-imaging | Medical Imaging | 医学影像 |
| protein-folding | Protein Folding | 蛋白质折叠 |
| finance | Finance | 金融 |
| trading | Trading | 交易 |
| risk-assessment | Risk Assessment | 风险评估 |
| fraud-detection | Fraud Detection | 欺诈检测 |
| legal | Legal | 法律 |
| education | Education | 教育 |
| gaming | Gaming | 游戏 |
| defense | Defense | 国防 |
| climate-energy | Climate & Energy | 气候与能源 |
| materials-science | Materials Science | 材料科学 |
| clinical-trials | Clinical Trials | 临床试验 |
| autonomous-vehicles | Autonomous Vehicles | 自动驾驶 |
| robotics | Robotics | 机器人 |
| self-driving | Self-Driving | 无人驾驶 |
| humanoid-robot | Humanoid Robot | 人形机器人 |
| drone | Drone | 无人机 |

#### business_model — 商业模式（11 个）

| id | name | name_zh |
|----|------|---------|
| open-source | Open Source | 开源 |
| api-service | API Service | API 服务 |
| saas | SaaS | SaaS 云服务 |
| freemium | Freemium | 免费增值 |
| usage-based | Usage Based | 按量计费 |
| enterprise | Enterprise | 企业版 |
| self-hosted | Self-Hosted | 私有部署 |
| cloud-native | Cloud Native | 云原生 |
| closed-source | Closed Source | 闭源 |
| b2b | B2B | 面向企业 |
| b2c | B2C | 面向消费者 |

#### audience — 目标受众（8 个）

| id | name | name_zh |
|----|------|---------|
| developers | Developers | 开发者 |
| data-scientists | Data Scientists | 数据科学家 |
| enterprises | Enterprises | 企业用户 |
| consumers | Consumers | 普通用户 |
| researchers | Researchers | 研究人员 |
| creators | Creators | 创作者 |
| marketers | Marketers | 营销人员 |
| students | Students | 学生 |

#### technical — 技术特性（11 个）

| id | name | name_zh |
|----|------|---------|
| real-time | Real-time | 实时 |
| low-latency | Low Latency | 低延迟 |
| high-throughput | High Throughput | 高吞吐 |
| on-device | On-Device | 端侧运行 |
| edge-ai | Edge AI | 边缘AI |
| mobile-app | Mobile App | 移动应用 |
| desktop-app | Desktop App | 桌面应用 |
| browser-extension | Browser Extension | 浏览器扩展 |
| api-platform | API Platform | API 平台 |
| sdk | SDK | 开发套件 |
| cli-tool | CLI Tool | 命令行工具 |

#### special — 特殊标识（10 个）

| id | name | name_zh |
|----|------|---------|
| unicorn | Unicorn | 独角兽 |
| decacorn | Decacorn | 超级独角兽 |
| yc-backed | YC-Backed | YC 孵化 |
| china | China | 中国 |
| us | United States | 美国 |
| europe | Europe | 欧洲 |
| japan | Japan | 日本 |
| korea | Korea | 韩国 |
| trending | Trending | 热门 |
| newly-launched | Newly Launched | 新上线 |

### Sub-category 迁移

现有 `categories.json` 中的 `sub_categories`（如 text-generation, image-generation, coding-assistant）迁移到标签维度中。产品 JSON 上的 `sub_category` 字段保留但不再用于前端过滤。

### 涉及文件

- `data/categories.json` — 替换为 11 个新分类（去掉 sub_categories）
- `data/tags.json` — 替换为维度化双语结构
- `data/schema/product.schema.json` — 更新 category enum 为 11 个值
- `data/schema/company.schema.json` — **删除**

---

## Phase 2: 删除 companies 数据 + 迁移分类/标签

产品 JSON 已内嵌公司信息，`data/companies/` 是冗余数据，直接删除。

### 步骤

1. **删除** `data/companies/` 整个目录
2. **删除** `data/schema/company.schema.json`
3. **迁移脚本** `scripts/migrate_categories.py`（轻量）：
   - 遍历 223 个产品 JSON
   - 用映射表将旧 category 值替换为新的 11 分类
   - 自动推断标签（从已有字段：open_source, architecture, modalities, pricing, country 等）
   - 写回产品 JSON
4. **验证** `aiscrape validate`
5. **重新生成** `aiscrape generate-stats`

### 涉及文件

- DELETE: `data/companies/` 目录
- DELETE: `data/schema/company.schema.json`
- NEW: `scripts/migrate_categories.py`（分类迁移 + 标签推断）
- MODIFY: 223 个 `data/products/*.json`（category + tags 字段）

---

## Phase 3: 采集管道重建

### 新架构：Discovery + Enrichment 两阶段

```
阶段1: 发现 (Discovery)              阶段2: 富化 (Enrichment)
"有哪些 AI 产品？"                   "这个产品的详情是什么？"

ProductHunt   ──┐                    Wikidata    ──┐
GitHub        ──┤→ DiscoveredProduct  Crunchbase  ──┤→ ScrapedProduct
Toolify       ──┤   (名字+URL+来源)   HuggingFace ──┤   (70+ 字段)
AIBot/AiNav   ──┘                    OpenRouter   ──┘
                      │                              │
                      ▼                              ▼
                 Deduplicator                   TieredMerger
                      │                       (每字段写 provenance)
                      ▼                              │
                 创建新产品骨架                  更新已有产品
                      │                              │
                      └──────────┬───────────────────┘
                                 ▼
                       TagInferenceEngine (规则引擎，零成本)
                                 ▼
                       ┌─── LLM analyze_product ───┐
                       │  噪声过滤 / 质量评估 /     │
                       │  问题检测 / 去重提示        │
                       └────────────┬───────────────┘
                          │         │         │
                       reject    accept    enrich/review
                       (跳过)    (无需改)      │
                                               ▼
                                 ┌─── LLM enrich_product ───┐
                                 │  纯 delta 输出            │
                                 │  推断型 + 事实型字段       │
                                 │  per-field 置信度         │
                                 └────────────┬─────────────┘
                                              ▼
                                   置信度过滤 (推断≥0.5 / 事实≥0.9)
                                              ▼
                                   名称→Slug 解析 (competitors, based_on)
                                              ▼
                                   TieredMerger (T3, 只填空字段)
                                              ▼
                                        SchemaValidator
                                     + provenance 覆盖率检查
                                              ▼
                                      写入 data/products/
```

### 三种 Scraper 角色

```python
class DiscoveryScraper(BaseScraper):
    """只负责发现新产品，不做深度抓取。"""
    def discover(self, limit) -> list[DiscoveredProduct]: ...

class EnrichmentScraper(BaseScraper):
    """只负责给已有产品补充信息。"""
    def enrich(self, slug, existing) -> ScrapedProduct | None: ...

class UnifiedScraper(BaseScraper):
    """既能发现也能富化。"""
    # 继续使用 scrape() 方法
```

### Scraper 花名册（20 个，从 28 个精简）

**保留（20 个）：**

| Scraper | 新角色 | 理由 |
|---------|--------|------|
| ProductHunt | DiscoveryScraper | 只能拿到名字+链接 |
| GitHub | DiscoveryScraper | 发现开源项目 |
| Toolify | DiscoveryScraper | AI 目录，擅长发现 |
| AIBot | DiscoveryScraper | 中文 AI 目录 |
| AiNav | DiscoveryScraper | 中文 AI 导航 |
| YCombinator | DiscoveryScraper | YC 公司列表 |
| TechCrunch | DiscoveryScraper | 新闻发现 |
| Wikidata | EnrichmentScraper | 权威数据补充 |
| Crunchbase | EnrichmentScraper | 融资数据补充 |
| PyPI/NPM/DockerHub | EnrichmentScraper | 包下载量补充 |
| AppStore/GooglePlay | EnrichmentScraper | 应用商店数据补充 |
| HuggingFace | UnifiedScraper | 发现+详细模型卡 |
| LMSYS | UnifiedScraper | 发现+评分 |
| OpenRouter | UnifiedScraper | 发现+价格 |
| ArtificialAnalysis | UnifiedScraper | 发现+benchmark |
| PapersWithCode | UnifiedScraper | 发现+评测 |
| TAA (TheresAnAI) | UnifiedScraper | 发现+分类 |

**删除（8 个注册 + 3 个未注册文件）：**

| Scraper | 注册状态 | 删除理由 |
|---------|---------|---------|
| indeed | 已注册 | Job 站，噪声大，只写 hiring.* |
| aijobs | 已注册 | 同上 |
| zhipin | 已注册 | 同上 |
| lagou | 已注册 | 同上 |
| liepin | 已注册 | 同上 |
| arxiv | 已注册 | 抓论文不是产品 |
| 36kr | 已注册 | 数据稀疏，ROI 低 |
| company_website | 已注册 | 依赖 Firecrawl API，效果不稳 |
| linkedin_jobs | 未注册 | 死代码，从未注册到 ALL_SCRAPERS |
| glassdoor | 未注册 | 同上 |
| aiji | 未注册 | 同上 |

### Tag Inference Engine（规则引擎）

新模块 `scrapers/enrichment/tag_inference.py`：

- 加载 `data/tags.json` 维度化标签词表
- 根据产品已有字段自动推断标签：
  - `open_source: true` → `open-source`
  - `architecture` 含 "transformer" → `transformer`
  - `modalities` 多于 1 个 → `multimodal`
  - `pricing.model: "freemium"` → `freemium`
  - `company.headquarters.country == "China"` → `china`
  - `company.funding.valuation_usd >= 1B` → `unicorn`
- 在 TieredMerger 之后、LLM 之前执行
- 确保每个产品 3-20 个标签
- 零成本，纯规则逻辑

### LLM Enrichment System（预算制 LLM 调用）

**月预算：$5** → 使用 **Claude Haiku**（`claude-haiku-4-5`），启用 prompt caching，~$0.002/次，~55 次/天。

新模块：
- `scrapers/enrichment/llm_classifier.py` — LLM 调用核心（prompt 构建 + tool schema + 后处理）
- `scrapers/enrichment/llm_scheduler.py` — 每日预算分配调度器

#### 3.1 字段认知分类

LLM 可以输出所有字段，但按认知类型分为两类，适用不同的置信度门槛：

**推断型字段** — 基于产品上下文进行分类、推理、翻译（置信度 ≥ 0.5 即接受）：

```
category, product_type, tags, description, description_zh, name_zh,
pricing_model, has_free_tier, modalities, architecture, open_source,
api_available, status, competitor_names, based_on_names
```

**事实型字段** — 客观存在的可查验信息（置信度 ≥ 0.9 才接受）：

```
repository_url, api_docs_url, key_people, company_founded_year,
company_headquarters_city, company_headquarters_country,
company_total_raised_usd, company_last_round,
company_employee_count_range, release_date
```

核心原则：**LLM 擅长分类和推理，不擅长事实记忆**。对于知名产品（OpenAI、DeepSeek），LLM 能准确输出创始人和融资信息（自报置信度高，通过门槛）；对于小众产品，LLM 会自然给出低置信度，被过滤掉。

#### 3.2 输出规则：纯 Delta

LLM 只输出需要**新增或修正**的字段，不回显已有且正确的数据。这确保：
- 输出中的每个字段 = "LLM 提供的新数据"，无歧义
- provenance 系统直接记录为 `source: "llm-enrichment", tier: 3`
- 不会意外把 T1/T2 的 provenance 覆盖为 T3

#### 3.3 Provenance 溯源（必须完整）

每个有值的字段必须有 `meta.provenance` 条目。审查数据时通过 `tier` 字段区分来源：

| tier | 来源 | 含义 |
|------|------|------|
| 1 | Wikidata, Crunchbase | 权威数据源爬取 |
| 2 | HuggingFace, ainav, app_store 等 | 网站/目录爬取 |
| 3 | llm-enrichment | **LLM 推断或补充** |
| 4 | job scrapers | 辅助来源 |

Provenance 仅后台审查用，不在网站前端展示。`aiscrape validate` 新增检查：有值无 provenance 视为数据缺陷。

#### 3.4 Tool Schema：`enrich_product` + `analyze_product`

使用 Anthropic `tool_use`（非自由 JSON），`enum` 约束分类和标签值。

**Tool 1: `enrich_product`** — 补充/修正所有字段

```python
ENRICH_TOOL = {
    "name": "enrich_product",
    "description": "为 AI 产品补充所有可能的信息。推断型字段基于推理填写，事实型字段仅在确认真实时填写。",
    "input_schema": {
        "type": "object",
        "required": ["field_confidences"],
        "properties": {
            # --- 推断型字段 ---
            "category":        {"type": "string", "enum": CATEGORIES_11},
            "product_type":    {"type": "string", "enum": PRODUCT_TYPES_8},
            "tags":            {"type": "array", "items": {"type": "string", "enum": ALL_TAG_IDS}},
            "description":     {"type": "string"},
            "description_zh":  {"type": "string"},
            "name_zh":         {"type": "string"},
            "pricing_model":   {"type": "string", "enum": PRICING_MODELS},
            "has_free_tier":   {"type": "boolean"},
            "open_source":     {"type": "boolean"},
            "api_available":   {"type": "boolean"},
            "status":          {"type": "string", "enum": STATUSES},
            "modalities":      {"type": "array", "items": {"type": "string"}},
            "architecture":    {"type": "string"},
            "competitor_names": {
                "type": "array", "items": {"type": "string"},
                "description": "竞品产品名称（非 slug），后处理自动解析为 slug",
            },
            "based_on_names": {
                "type": "array", "items": {"type": "string"},
                "description": "基于哪些产品/模型（名称，非 slug）",
            },
            # --- 事实型字段（LLM 确信时才填） ---
            "repository_url":               {"type": "string"},
            "api_docs_url":                 {"type": "string"},
            "key_people":                   {"type": "array", "items": {"type": "object", ...}},
            "company_founded_year":         {"type": "integer"},
            "company_headquarters_city":    {"type": "string"},
            "company_headquarters_country": {"type": "string"},
            "company_total_raised_usd":     {"type": "number"},
            "company_last_round":           {"type": "string", "enum": FUNDING_ROUNDS},
            "company_employee_count_range": {"type": "string", "enum": EMPLOYEE_RANGES},
            "release_date":                 {"type": "string"},
            # --- 元信息 ---
            "field_confidences": {
                "type": "object",
                "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
                "description": "每个已输出字段的置信度。键=字段名，值=0-1。",
            },
        },
    },
}
```

**Tool 2: `analyze_product`** — 数据质量评估与管道决策

```python
ANALYZE_TOOL = {
    "name": "analyze_product",
    "description": "评估产品数据质量，检测问题，辅助管道决策。",
    "input_schema": {
        "type": "object",
        "required": ["is_ai_product", "quality_score", "verdict"],
        "properties": {
            "is_ai_product":     {"type": "boolean", "description": "是否为真正的 AI 产品（过滤噪声）"},
            "quality_score":     {"type": "number", "minimum": 0, "maximum": 1},
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field":    {"type": "string"},
                        "issue":    {"type": "string"},
                        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    },
                },
            },
            "possible_duplicates": {"type": "array", "items": {"type": "string"}},
            "verdict":   {"type": "string", "enum": ["accept", "enrich", "review", "reject"]},
            "reasoning": {"type": "string"},
        },
    },
}
```

#### 3.5 System Prompt（所有调用共享，可缓存）

```
你是 AI 产品数据专家。你的任务是对产品条目进行分类、补全和翻译。

## 输出规则（最重要）

你只输出需要【新增】或【修正】的字段。已有且正确的字段不要输出。

每个字段属于两种认知类型之一：

### 推断型字段 — 可以基于推理输出
category, product_type, tags, description, description_zh, name_zh,
pricing_model, has_free_tier, modalities, architecture, open_source,
api_available, status, competitor_names, based_on_names

规则：基于产品名称、描述、URL 等上下文进行合理推理即可。

### 事实型字段 — 必须确认真实存在才可输出
repository_url, api_docs_url, key_people, company_founded_year,
company_headquarters_*, company_total_raised_usd, company_last_round,
company_employee_count_range, release_date

规则：
- 只有在确定信息真实、准确、可被第三方验证时才输出
- 如果只是"印象中大概是"但不确定具体值，必须省略
- 宁可留空让 scraper 后续补充，也不要输出未经确认的事实

## 分类体系（11 个，互斥）
[11 个分类定义 + 易混淆情况消歧]

## 标签词表（按维度，~114 个）
[7 个维度的完整标签 ID 列表]
```

#### 3.6 User Prompt（按产品状态变化，三种策略）

User prompt 控制 LLM 的行为模式。Tool schema 保持不变，通过 prompt 措辞适配不同场景：

**策略 A：新产品**（analyze → enrich 两步，或单次双 tool 调用）

```
评估并补充以下新产品：

产品名: AI Chatbot - Nova
URL: https://apps.apple.com/...
描述: Nova is a revolutionary AI chatbot...  [已有]
分类: [缺失]
标签: [缺失]
中文名: [缺失]
```

**策略 B：低质量产品**（直接 enrich，列出缺失字段）

```
为以下产品补充缺失字段：

产品名: Cursor Editor
URL: https://cursor.com  [已有]
分类: ai-dev-tool  [已有]
标签: code-generation, copilot, developer-tools, b2c  [已有]
中文描述: [缺失]
pricing_model: [缺失]
modalities: [缺失]
```

**策略 C：定期刷新**（analyze 先行，按 issues 决定是否 enrich）

```
审核以下产品的数据准确性：

产品名: DeepSeek-V3
分类: ai-app  [已有]
product_type: app  [已有]
描述: Chinese artificial intelligence company  [已有]
标签: generative-ai, nlp, transformer, open-source, china, ai对话聊天  [已有]
开源: 是  [已有]
仓库: https://github.com/deepseek-ai  [已有]
```

#### 3.7 后处理

**置信度过滤：**
```python
FACTUAL_FIELDS = {"repository_url", "api_docs_url", "key_people", ...}
INFERENCE_FIELDS = {"category", "tags", "description", ...}

for field, value in tool_result.items():
    conf = field_confidences.get(field, 0.0)
    if field in FACTUAL_FIELDS and conf < 0.9:
        drop(field)       # 事实型：高门槛
    elif field in INFERENCE_FIELDS and conf < 0.5:
        drop(field)       # 推断型：较低门槛
```

**名称→Slug 解析：** `competitor_names` 和 `based_on_names` 中的产品名称通过 fuzzy match 对照 `index.json` 解析为数据库 slug，匹配度 < 0.85 的丢弃。

**TieredMerger 集成：** 所有通过过滤的字段封装为 `ScrapedProduct(source="llm-enrichment", source_tier=T3)`，喂给 TieredMerger。T3 数据只填充空字段，不覆盖已有 T1/T2 数据。

#### 3.8 调度器（每日预算分配）

**每日预算：55 次调用**，按优先级分配：

| 优先级 | 占比 | 策略 | 说明 |
|--------|------|------|------|
| 1. 新产品 | ~40% | 策略 A | analyze + enrich，全套补充 |
| 2. 低质量产品 | ~40% | 策略 B | 只 enrich 缺失字段 |
| 3. 轮转刷新 | ~20% | 策略 C | analyze 检测问题，按需 enrich |

**每日产出效率（55 次调用 → ~42 产品/天）：**

| 策略 | 分配 (次/天) | 每产品调用数 | 产品/天 |
|------|------------|------------|--------|
| A: 新产品 | 22 | 2 (analyze+enrich) | 11 |
| B: 低质量 | 22 | 1 (enrich only) | 22 |
| C: 定期刷新 | 11 | 1~2 (analyze, 按需 enrich) | ~9 |

**优雅降级**：没有 `ANTHROPIC_API_KEY` → 跳过 LLM 步骤，仅用规则引擎。

**追踪**：`meta.llm_enrichment` 记录 `last_run`、`model`、`task_type`、`fields_updated`。

#### 3.9 成本分析

**模型：Claude Haiku 4.5**（`claude-haiku-4-5-20251001`），定价参考 [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing)。

**定价：**

| 项目 | 价格 |
|------|------|
| 基础输入 | $1.00 / MTok |
| 5min 缓存写入 | $1.25 / MTok |
| 缓存命中 | $0.10 / MTok |
| 输出 | $5.00 / MTok |
| Batch 输入 | $0.50 / MTok |
| Batch 输出 | $2.50 / MTok |
| Tool use 系统开销 | 346 tokens / 次 |

**Token 估算（per call）：**

| 组成部分 | Token 数 | 缓存状态 |
|---------|---------|---------|
| System prompt（角色 + 规则 + 11 分类 + 消歧） | ~1,200 | 可缓存 |
| Tool schema（enrich 含 ~114 enum + analyze） | ~800 | 可缓存 |
| Tool use 系统隐含开销 | 346 | 可缓存 |
| **可缓存总计** | **~2,346** | |
| User prompt（产品上下文 + 字段状态） | ~300 | 不可缓存 |
| **LLM 输出**（analyze ~150 / enrich ~300 / 平均） | **~250** | — |

**方案对比（月预算 $5）：**

| 方案 | 月费 | vs 预算 | 适用场景 |
|------|------|---------|---------|
| **Prompt Caching（推荐）** | **$3.03** | 60.6% | CI 集中运行，5min 内完成所有调用 |
| 无缓存 | $6.43 | 128.6% (超预算) | — |
| Batch API | $3.22 | 64.4% | 异步场景（不适合 CI 串行流水线） |

**推荐方案详细计算（Prompt Caching）：**

```
首次调用（cache write）:
  2,346 tokens × $1.25/MTok + 300 × $1.00/MTok + 250 × $5.00/MTok = $0.00448

后续 54 次（cache read）:
  (2,346 × $0.10/MTok + 300 × $1.00/MTok + 250 × $5.00/MTok) × 54 = $0.09639

每日合计: $0.101
每月合计: $0.101 × 30 = $3.03
每产品成本: ~$0.0024
```

**预算余量：** $5 预算下可支撑最多 ~92 次/天（约 70 产品/天），当前 55 次/天用了 60% 预算，为产品增长留有余量。

### 新 CLI 命令

```bash
aiscrape discover --source github,producthunt --limit 200   # 发现阶段
aiscrape enrich --sources wikidata,crunchbase                # 富化阶段
aiscrape scrape --source huggingface --limit 50              # 一体化（兼容旧方式）
aiscrape llm-enrich --budget 55                              # LLM 分类与补全（默认每日预算）
aiscrape llm-enrich --budget 55 --model claude-sonnet-4-5    # 指定模型
```

### Daily Scrape CI 流程

```yaml
- Discovery phase (discover scrapers)
- Unified scrape (huggingface, lmsys, etc.)
- Enrichment phase (wikidata, crunchbase)
- LLM enrichment (如有 ANTHROPIC_API_KEY)
- Validate + generate-stats
- Commit + push
```

### 涉及文件

- `scrapers/base.py` — 新增 DiscoveredProduct, DiscoveryScraper, EnrichmentScraper
- `scrapers/sources/__init__.py` — 更新注册表（移除 8 个，重构角色）
- DELETE: 11 个 scraper 文件（indeed.py, aijobs.py, zhipin.py, lagou.py, liepin.py, linkedin_jobs.py, glassdoor.py, aiji.py, arxiv_scraper.py, kr36.py, company_website.py）
- REFACTOR: 20 个保留的 scraper 文件（更新类继承为 DiscoveryScraper/EnrichmentScraper/UnifiedScraper）
- NEW: `scrapers/enrichment/tag_inference.py`（规则标签引擎）
- NEW: `scrapers/enrichment/llm_classifier.py`（LLM 核心：tool schema 定义 + prompt 构建 + 置信度过滤 + 名称→slug 解析）
- NEW: `scrapers/enrichment/llm_scheduler.py`（每日预算调度 + 优先级队列）
- MODIFY: `scrapers/enrichment/llm_enricher.py` — 重构为调用 llm_classifier 的薄封装，或合并删除
- `scrapers/cli.py` — 新增 discover, llm-enrich 命令
- `scrapers/enrichment/normalizer.py` — 更新分类验证为 11 个新分类
- `scrapers/enrichment/merger.py` — 集成 TagInferenceEngine + 确保所有字段写入 provenance
- `scrapers/validation/schema_validator.py` — 新增 provenance 覆盖率检查（有值无 provenance = 缺陷）
- `scrapers/config.py` — 移除 job scraper 配置，新增 LLM 预算配置
- `data/schema/product.schema.json` — 新增 `meta.llm_enrichment`

---

## Phase 4: 生成器与前端

### 4.1 生成器更新

#### IndexGenerator (`scrapers/generators/index_generator.py`)

当前 `INDEX_FIELDS` 将 `company.*` 嵌套字段展平到 index（如 `company.name` → `company_name`），此逻辑保持不变。

变更：

| 字段 | 变更 |
|------|------|
| `category` | 值域从 10 个旧分类 → 11 个新分类（随产品 JSON 变化，无需代码改动） |
| `sub_category` | **从 INDEX_FIELDS 中移除**（迁移到 tags） |
| `tags` | 已在 INDEX_FIELDS 中，无需改动 |
| 排序 | 不变（`total_raised_usd` 降序 → `name` 升序） |

#### StatsGenerator (`scrapers/generators/stats_generator.py`)

| 统计维度 | 当前 | 变更 |
|---------|------|------|
| `by_category` | 10 个旧分类 | → 11 个新分类（自动随数据变化） |
| `by_product_type` | 8 种，108 个 "other" | **删除**（数据质量差，分析价值低） |
| `by_sub_category` | ~20 种 | **删除**（已迁移到 tags 维度） |
| `by_country` | 不变 | 不变 |
| `by_status` | 不变 | 不变 |
| `by_tag_dimension` | 无 | **新增**：7 个维度各自 top 标签及计数 |
| `funding_leaderboard` | 不变 | 不变 |
| `open_source_count` | 不变 | 不变 |
| `recently_added` | 不变 | 不变 |

新增 `by_tag_dimension` 输出格式：

```json
{
  "by_tag_dimension": {
    "technology": [{"tag": "transformer", "count": 45}, {"tag": "rag", "count": 32}],
    "use_case": [{"tag": "chatbot", "count": 38}, {"tag": "copilot", "count": 25}],
    "domain": [{"tag": "healthcare", "count": 12}],
    "business_model": [{"tag": "saas", "count": 67}, {"tag": "open-source", "count": 50}],
    "audience": [{"tag": "developers", "count": 89}],
    "technical": [{"tag": "api-platform", "count": 55}],
    "special": [{"tag": "unicorn", "count": 15}, {"tag": "china", "count": 30}]
  }
}
```

### 4.2 TypeScript 类型更新 (`website/src/lib/types.ts`)

```typescript
// 旧 Category（包含 sub_categories）
interface Category {
  id: string; name: string; name_zh: string; icon: string;
  sub_categories: { id: string; name: string; name_zh: string }[];
}

// 新 Category（去掉 sub_categories）
interface Category {
  id: string; name: string; name_zh: string; icon: string;
}

// 新增 Tag 相关类型
interface Tag {
  id: string; name: string; name_zh: string;
}

interface TagDimension {
  name: string; name_zh: string;
  tags: Tag[];
}

interface TagsData {
  version: string;
  dimensions: Record<string, TagDimension>;
}

// Stats 更新
interface Stats {
  // 保留: by_category, by_country, by_status, funding_leaderboard, etc.
  // 删除: by_product_type, by_sub_category
  by_tag_dimension: Record<string, { tag: string; count: number }[]>;  // 新增
}
```

### 4.3 数据层更新

#### `website/src/lib/data.ts`

- **新增** `getTags(): Promise<TagsData>` — 加载 `data/tags.json`
- 其余函数不变（`getAllProducts`, `getProductBySlug`, `getStats`, `getAllSlugs`, `getCategories`）
- 注：data.ts 不直接加载 `data/companies/`，Phase 2 删除 companies 目录后无需改动 data.ts

#### `website/src/lib/search.ts`

Fuse.js 搜索键更新：

| 键 | 权重 | 变更 |
|----|------|------|
| name | 2.0 | 不变 |
| name_zh | 1.5 | 不变 |
| company_name | 1.0 | 不变 |
| description | 1.0 | 不变 |
| description_zh | 0.8 | 不变 |
| category | 1.0 | 不变 |
| product_type | 0.8 | 不变 |
| ~~sub_category~~ | ~~0.7~~ | **删除** |
| tags | 0.8 | 不变（已有） |
| country | 0.5 | 不变 |
| city | 0.5 | 不变 |

### 4.4 组件更新

#### ProductGrid.tsx — 分类筛选

- 分类 tab 从 10 个旧分类 → 11 个新分类
- tab 显示用 `localized(category, locale, "name")` 保持双语
- 保持 `useMemo` + `Map` 做 O(1) category lookup

#### ProductCard.tsx — 标签 chips

现有：显示 category badge + product_type + open_source badge

新增：显示前 3 个 tags 作为小型 chips（需通过 `tags.json` 的 `localized()` 查找双语名称）

#### ProductDetail.tsx — 标签按维度分组

现有：tags 作为平铺 badge 列表 + 显示 sub_category

变更：
- 按 7 个维度分组展示标签，每组带维度标题
- 移除 `sub_category` 展示
- 维度标题用 `localized(dimension, locale, "name")` 双语显示

#### FilterPanel.tsx — 标签维度筛选（搜索页）

新增可折叠的标签维度筛选器：
- 每个维度一个折叠区块（Technology, Use Case, Domain...）
- 区块内为 checkbox 列表
- 选中标签作为 AND 过滤条件
- 筛选状态记录到 URL search params

#### Analytics 组件

| 组件 | 变更 |
|------|------|
| CategoryDistribution.tsx | 饼图从 10 → 11 个分类，更新颜色 palette |
| FundingChart.tsx | 不变 |
| GeographyMap.tsx | 不变 |
| **NEW: TagCloud.tsx**（可选） | 标签热度气泡图，数据来自 `stats.by_tag_dimension` |

### 4.5 i18n 更新

分类名和标签名从数据文件（`categories.json`、`tags.json`）通过 `localized()` 获取，i18n 字典只需新增 UI 文本：

#### `en.json` / `zh.json` 新增 key

```json
{
  "product": {
    "tags_by_dimension": "Tags",
    "...existing keys..."
  },
  "search": {
    "filter_tags": "Filter by Tags",
    "...existing keys..."
  },
  "analytics": {
    "tag_chart": "Tag Distribution",
    "...existing keys..."
  }
}
```

#### `dict.ts`

`Dictionary` 接口新增对应 key 的类型定义。

### 4.6 CI/CD 更新

#### `.github/workflows/daily-scrape.yml`

```yaml
steps:
  - name: Discovery phase
    run: aiscrape discover --source github,producthunt,toolify --limit 200

  - name: Unified scrape
    run: aiscrape scrape --source huggingface,lmsys,openrouter --limit 50

  - name: Enrichment phase
    run: aiscrape enrich --sources wikidata,crunchbase

  - name: LLM enrichment
    if: env.ANTHROPIC_API_KEY != ''
    run: aiscrape llm-enrich --budget 55

  - name: Validate and generate
    run: |
      aiscrape validate
      aiscrape generate-stats
```

#### `.github/workflows/validate-pr.yml`

新增检查：
- `data/companies/` 目录不存在（Phase 2 后）
- 所有产品 category ∈ 11 个新分类
- ruff + mypy + website build

### 涉及文件

**生成器：**
- `scrapers/generators/index_generator.py` — 移除 `sub_category` 从 INDEX_FIELDS
- `scrapers/generators/stats_generator.py` — 删除 `by_product_type`/`by_sub_category`，新增 `by_tag_dimension`

**前端类型与数据层：**
- `website/src/lib/types.ts` — 更新 Category（去掉 sub_categories），新增 Tag/TagDimension/TagsData，更新 Stats
- `website/src/lib/data.ts` — 新增 `getTags()` 函数
- `website/src/lib/search.ts` — 移除 `sub_category` 搜索键
- `website/src/lib/dict.ts` — 新增标签相关 UI key 类型

**组件：**
- `website/src/components/product/ProductGrid.tsx` — 分类 tab 更新为 11 个
- `website/src/components/product/ProductCard.tsx` — 新增 tag chips
- `website/src/components/product/ProductDetail.tsx` — 标签按维度分组，移除 sub_category
- `website/src/components/search/FilterPanel.tsx` — 新增标签维度筛选器
- `website/src/components/analytics/CategoryDistribution.tsx` — 更新为 11 分类
- NEW（可选）: `website/src/components/analytics/TagCloud.tsx` — 标签热度图

**i18n：**
- `website/src/i18n/en.json` — 新增标签相关 UI 文本
- `website/src/i18n/zh.json` — 同上中文版

**CI/CD：**
- `.github/workflows/daily-scrape.yml` — 新增 discover + llm-enrich 步骤
- `.github/workflows/validate-pr.yml` — 新增 companies 目录为空 + 分类范围检查

---

## Phase 5: 验证与验收

### 5.1 数据验证

| # | 验证项 | 命令/方法 | 预期结果 |
|---|--------|----------|---------|
| 1 | Schema 合规 | `aiscrape validate` | 223 个产品全部 OK |
| 2 | 分类范围 | schema enum 自动检查 | 所有 category ∈ 11 个新分类 |
| 3 | 标签范围 | 脚本检查 tags ∈ tags.json | 所有 tag ID ∈ ~114 个合法标签 |
| 4 | 标签覆盖 | 脚本统计 | 每产品 3-20 个标签，平均 ≥ 5 |
| 5 | Provenance 覆盖 | `aiscrape validate` 新检查 | 有值字段 provenance 覆盖率 ≥ 90% |
| 6 | 引用完整性 | IntegrityValidator | competitors/based_on slug 全部有效 |
| 7 | companies 目录 | 手动确认 | `data/companies/` 已删除 |

### 5.2 生成器验证

| # | 验证项 | 命令 | 预期结果 |
|---|--------|------|---------|
| 1 | 重建 index + stats | `aiscrape generate-stats` | 成功，无 error |
| 2 | index.json 分类 | 脚本检查 | 所有 category ∈ 11 个新分类 |
| 3 | index.json 标签 | 脚本检查 | tags 字段非空率 ≥ 80% |
| 4 | stats 分类维度 | 人工核对 | `by_category` 恰好 11 个条目 |
| 5 | stats 标签维度 | 人工核对 | `by_tag_dimension` 有 7 个维度 |
| 6 | stats 清理 | 人工核对 | 无 `by_product_type`、无 `by_sub_category` |

### 5.3 前端构建

| # | 验证项 | 命令 | 预期结果 |
|---|--------|------|---------|
| 1 | TypeScript 编译 | `cd website && npx tsc --noEmit` | 0 errors |
| 2 | ESLint | `cd website && npm run lint` | 0 warnings |
| 3 | 静态导出 | `cd website && npm run build` | `out/` 目录生成成功 |
| 4 | 路由完整 | 检查 `out/` 目录 | `/en/`、`/zh/`、`/en/products/*/`、`/en/search/`、`/en/analytics/` 全部存在 |

### 5.4 人工验证

| # | 验证项 | 方法 | 关注点 |
|---|--------|------|--------|
| 1 | 融资 Top 20 | 浏览产品详情 | 公司信息完整，funding 准确 |
| 2 | 中国产品 ×10 | 浏览产品详情 | `name_zh` + `description_zh` + `china` 标签 |
| 3 | 开源产品 ×10 | 浏览产品详情 | `open-source` 标签 + `repository_url` 有效 |
| 4 | 首页 | 浏览器访问 | 11 分类 tab 正确，产品卡片显示 tag chips |
| 5 | 搜索页 | 输入 "chatbot" | 搜索结果正确，标签维度筛选器可用 |
| 6 | 分析页 | 浏览器访问 | 饼图 11 分类，标签热度图（如有）有数据 |
| 7 | EN/ZH 切换 | 切换语言 | 分类名、标签名、维度名双语正确 |
| 8 | Provenance 抽查 | 随机 5 产品 JSON | LLM 字段 tier=3，爬虫字段 tier=1/2 |

### 5.5 CI/CD 验证

| # | 验证项 | 方法 | 预期结果 |
|---|--------|------|---------|
| 1 | validate-pr | 提交测试 PR | schema + lint + build 全部通过 |
| 2 | daily-scrape | 手动触发一次 | discover → scrape → enrich → llm-enrich → validate → commit 成功 |
| 3 | LLM 降级 | 移除 ANTHROPIC_API_KEY | 跳过 llm-enrich，其余正常完成 |

---

## 实施顺序

| 步骤 | 阶段 | 依赖 | 工作量 | 涉及文件 | 里程碑 |
|------|------|------|--------|---------|--------|
| 1 | Phase 1: categories + tags + schema | 无 | 小 | 4 文件 | 新分类体系生效 |
| 2 | Phase 2: 删除 companies + 迁移分类 | Step 1 | 小 | ~225 文件 | 数据层统一 |
| 3 | Phase 3a: scraper 基类重构 | 无 | 中 | base.py, \_\_init\_\_.py | 新抽象就绪 |
| 4 | Phase 3b: 删除 11 个 + 重构 20 个 scraper | Step 3 | 中 | 31 文件 | Scraper 精简完成 |
| 5 | Phase 3c: 标签推断引擎 | Step 1 | 小 | 1 新 + merger.py | 零成本标签自动化 |
| 6 | Phase 3d: LLM enrichment system | Step 1, 3 | 中 | 3 新 + cli.py, config.py | LLM 管道就绪 |
| 7 | Phase 4a: 生成器更新 | Step 1, 2 | 小 | 2 文件 | index + stats 反映新体系 |
| 8 | Phase 4b: 前端类型 + 数据层 | Step 7 | 小 | 4 文件 | 类型安全 |
| 9 | Phase 4c: 组件 + 搜索 + 分析 | Step 8 | 中 | 6~7 文件 | 用户可见变化 |
| 10 | Phase 4d: i18n + CI/CD | Step 9 | 小 | 4 文件 | 多语言 + 自动化 |
| 11 | Phase 5: 验证与验收 | Step 1-10 | 小 | — | 全面交付 |

**关键路径**：Step 1 → 2 → 7 → 8 → 9 → 10 → 11

**并行机会**：
- Step 3/4（scraper 重构）与 Step 7/8/9（前端）可并行——两者仅共享 Step 1 的分类/标签定义
- Step 5（标签引擎）与 Step 4（scraper 精简）可并行
- Step 6（LLM）在 Step 1+3 完成后即可开始，与前端并行开发

**推荐执行序列**：1 → 2 → {3, 5, 7} 并行 → {4, 6, 8} → 9 → 10 → 11

每步可独立提交和验证。

---

## 跨阶段一致性校验

下表列出各阶段的关键数据点引用，确保跨阶段一致：

| 数据点 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|--------|---------|---------|---------|---------|---------|
| 主分类 | 定义 11 个 | 迁移旧→新 | tool enum=11 | tab=11, 饼图=11 | 验证 ∈ 11 |
| 标签 | 定义 ~114 (7 维度) | 脚本推断初始标签 | tool enum=~114 | chips + 筛选 + 分组展示 | 验证 ∈ ~114 |
| 产品数 | — | 223 文件迁移 | 223+ 处理 | 全量渲染 | 223 全部 OK |
| Scraper | — | — | 28→20 (删 11) | — | — |
| LLM 调用 | — | — | 55 次/天 | — | CI 验证 |
| 月 LLM 成本 | — | — | $3.03 (缓存) | — | — |
| sub_category | 迁移→tags | 字段保留值清空 | 不处理 | 前端移除展示 | — |
| Provenance | — | — | 必须完整, tier 1-4 | 不在前端展示 | 覆盖 ≥ 90% |
| companies/ | — | 删除目录 | — | 无加载代码 | 确认已删除 |
| by_product_type | — | — | — | stats 中删除 | 确认已删除 |
