# AI Product Data - 数据架构与爬虫策略重新设计

## Context

当前项目有严重的数据质量问题：62% 公司归类为 `ai-other`，72% 的 `founded_year` 是默认值 2026，47% 的国家字段被招聘爬虫数据污染（如 "WA2 weeks ago"）。同时，产品和人物数据嵌套在公司 JSON 中，无法独立管理。本计划将项目从单实体（Company）架构重构为三实体（Company + Product + Person）架构，引入数据源分层信任机制，并新增 AI 辅助数据补全能力。

---

## 一、新数据架构：三实体模型

### 1.1 目录结构

```
data/
  schema/
    company.schema.json       # 重写
    product.schema.json       # 新增
    person.schema.json        # 新增
  companies/                  # 迁移后的公司文件
  products/                   # 新增：独立产品/模型
  people/                     # 新增：独立人物
  archive/                    # 新增：归档的非AI公司
  discovery_queue.json        # 新增：T4发现的待丰富名单
  index.json / stats.json / categories.json / tags.json
```

### 1.2 Company Schema 关键变更

| 变更 | 原设计 | 新设计 |
|------|--------|--------|
| `founded_year` | 必填，默认当前年 | **可为 null**，未知即 null |
| `headquarters.city` | 必填 | **可为 null**，仅 country 必填 |
| `category` | 不可为空 | 保留 enum，但不再用 `ai-other` 作兜底 |
| `team` 对象 | 嵌套 founders 数组 | **移除**，改用 `person_slugs[]` 引用 |
| `products` 数组 | 嵌套产品数组 | **移除**，改用 `product_slugs[]` 引用 |
| `employee_count_range` | 嵌套在 team 内 | **提升到顶层** |
| 新增分类 | 17 个 | 新增 `ai-agent`, `ai-science`, `ai-hardware`（共 20 个） |
| `sub_categories` | 无 | 新增，允许多标签分类 |
| `meta.provenance` | 无 | **新增**：字段级溯源 `{field: {source, tier, confidence}}` |
| `meta.needs_review` | 无 | **新增**：AI 生成数据标记为待审核 |

### 1.3 Product Schema（新增）

```
必填：slug, name, description, company_slug, product_type
product_type 枚举：llm, image-model, video-model, audio-model, multimodal-model,
  code-model, embedding-model, agent-framework, developer-tool, saas-product,
  api-service, hardware, dataset, benchmark, open-source-library, other
model_details（可选）：architecture, parameter_count, context_window, modalities,
  huggingface_id, benchmarks, training_data_cutoff
pricing（可选）：model(free/freemium/paid/...), input/output_price_per_1m_tokens
```

### 1.4 Person Schema（新增）

```
必填：slug, name, description
roles[]：company_slug, title, is_founder, start_year, end_year, is_current
social：linkedin, twitter, github, google_scholar, personal_website
education[]：institution, degree, field, year
notable_for：简述此人为何值得收录
```

### 1.5 实体关联（通过 slug 引用）

```
Company.product_slugs[] --> Product.slug
Company.person_slugs[]  --> Person.slug
Product.company_slug    --> Company.slug
Person.roles[].company_slug --> Company.slug
```

---

## 二、数据源分层系统

| 层级 | 名称 | 信任度 | 合并优先级 | 需人工审核 | 用途 |
|------|------|--------|-----------|-----------|------|
| **T1** | 权威 API | 0.95 | 最高，可覆盖 T2-T4 | 否 | 结构化事实：融资、总部、成立年份 |
| **T2** | 开放 Web | 0.75 | 中等，可覆盖 T3-T4 | 否 | 描述、仓库、模型、开源状态 |
| **T3** | AI 生成 | 0.50 | 低，仅填空 | **是** | 分类、摘要、缺失字段推断 |
| **T4** | 辅助源 | 0.20 | 最低，仅发现 | 否 | 仅发现新公司名称 |

### T1 权威数据源

| 数据源 | 技术方案 | 认证 | 可靠字段 | 实体类型 |
|--------|---------|------|---------|---------|
| Crunchbase API | httpx REST | API Key (免费200次/天) | funding, founded_year, HQ, employees, investors | Company |
| Wikipedia/Wikidata | httpx SPARQL + REST | 无 | founded_year, HQ, founders, status | Company, Person |

### T2 开放 Web 数据源

| 数据源 | 技术方案 | 认证 | 可靠字段 | 实体类型 |
|--------|---------|------|---------|---------|
| GitHub API | httpx REST | Token (可选) | repos, open_source, license, description | Company, Product |
| HuggingFace API | httpx REST | Token (可选) | model cards, parameters, benchmarks, license | Product |
| Papers with Code | httpx REST | 无 | benchmarks, paper links | Product |
| Y Combinator | httpx Algolia | 无 | name, description, website, HQ, founded_year | Company |
| Product Hunt | httpx GraphQL | Token | name, description, products, makers | Company, Product, Person |
| 公司官网 | httpx -> Playwright fallback | 无 | description, team, products, pricing | Company, Product, Person |
| TechCrunch RSS | httpx + feedparser | 无 | funding announcements, launches | Company |

### T3 AI 辅助补全

| 能力 | 输入 | 输出 | 模型 | 成本控制 |
|------|------|------|------|---------|
| 分类推断 | 公司名+描述 | category + sub_categories | Claude Haiku | Batch API, ~$0.001/条 |
| 描述生成 | 公司名+官网内容 | description (en+zh) | Claude Sonnet | 仅空描述 |
| 标签提取 | 描述+产品名 | tags[] | Claude Haiku | Batch API |
| 翻译 | description (en) | description_zh | Claude Haiku | Batch API |

**所有 T3 数据自动设置 `needs_review=true`，永远不覆盖 T1/T2 数据。**

### T4 辅助源（招聘网站降级）

7 个招聘爬虫（LinkedIn Jobs, Indeed, Glassdoor, AI Jobs, 智联, 拉勾, 猎聘）全部简化：
- **不再**产出 `ScrapedCompany`
- **仅**产出 `DiscoveredName(name, source)` — 只提取公司名称
- 发现的名称写入 `discovery_queue.json`，等待 T1/T2 丰富

---

## 三、技术方案

### 3.1 混合爬取策略

```
API 数据源（T1/T2 大部分）-> httpx (async)
  - Crunchbase, GitHub, HuggingFace, Papers with Code, YC, PH
  - 统一速率限制、重试、缓存

动态页面（T2 官网爬取）-> httpx 优先，Playwright fallback
  - 先用 httpx 请求，如遇 403/验证码 -> 切换 Playwright stealth
  - 尊重 robots.txt，3秒/请求/域名
  - 代理池轮换（配置在 scrapers/config.py）

RSS 订阅（TechCrunch）-> httpx + feedparser

SPARQL（Wikidata）-> httpx + SPARQLWrapper
```

### 3.2 分层合并规则（TieredMerger）

```
规则 1: 高层级（T1）数据可覆盖低层级（T2-T4）数据
规则 2: 同层级数据：保留已有值（先到先得）
规则 3: T3（AI）数据仅填充空字段，永不覆盖
规则 4: T4 数据不参与合并（仅发现名称）
规则 5: 每次字段写入记录溯源（source, tier, confidence, updated_at）
```

### 3.3 新增核心模块

| 文件 | 职责 |
|------|------|
| `scrapers/base.py` | 重写：ScrapedCompany/Product/Person + DiscoveredName + SourceTier |
| `scrapers/enrichment/merger.py` | 重写：TieredMerger，分层优先级合并+溯源 |
| `scrapers/enrichment/llm_enricher.py` | 新增：LLM 批量丰富引擎（Anthropic Batch API） |
| `scrapers/enrichment/quality_scorer.py` | 新增：加权字段完整度+来源层级评分 |
| `scrapers/enrichment/entity_linker.py` | 新增：跨实体 slug 引用解析 |
| `scrapers/enrichment/normalizer.py` | 扩展：PlausibilityValidator 拒绝脏数据 |
| `scrapers/validation/integrity_validator.py` | 新增：跨实体引用完整性检查 |
| `scrapers/sources/wikidata.py` | 新增：Wikidata T1 爬虫 |
| `scrapers/sources/huggingface.py` | 新增：HuggingFace T2 爬虫 |
| `scrapers/sources/papers_with_code.py` | 新增：Papers with Code T2 爬虫 |
| `scrapers/sources/company_website.py` | 新增：官网爬取 T2（httpx + Playwright） |

---

## 四、迁移策略（5 步，无数据丢失）

### Step 1: 数据清洗 (`scrapers/migration/data_cleanup.py`)
- 国家字段包含 "ago"/"Actively Hiring" -> 设为 null
- `founded_year == 2026` -> 设为 null
- `category == "ai-other"` 且 `quality_score == 0.4` -> 设为 null
- 非 AI 公司 -> 移至 `data/archive/`
- `website == ""` -> 设为 null

### Step 2: Schema 迁移 (`scrapers/migration/migrate_v1_to_v2.py`)
- 106 个公司文件映射到新 schema
- 移除 `team` 和 `products` 嵌套结构
- 添加 `product_slugs[]`, `person_slugs[]`, `meta.provenance`

### Step 3: 提取产品 (`scrapers/migration/extract_products.py`)
- 从公司的 `products[]` 数组提取为 `data/products/<slug>.json`
- 预估 ~30 个初始产品

### Step 4: 提取人物 (`scrapers/migration/extract_people.py`)
- 从公司的 `team.founders[]` 提取为 `data/people/<slug>.json`
- 跨公司去重（同一人在多家公司则合并 roles）
- 预估 ~40 个初始人物

### Step 5: 更新引用 (`EntityLinker`)
- Company 添加 `product_slugs`, `person_slugs`
- 双向引用完整性校验

---

## 五、实施阶段

| 阶段 | 内容 | 关键文件 |
|------|------|---------|
| **Phase 1** | 新 Schema + 目录结构 + 迁移脚本 | `data/schema/*.json`, `scrapers/migration/` |
| **Phase 2** | 核心管道重构（base, merger, scorer, linker） | `scrapers/base.py`, `scrapers/enrichment/` |
| **Phase 3** | 新爬虫 + 升级旧爬虫 + 降级招聘爬虫 | `scrapers/sources/` |
| **Phase 4** | AI 补全引擎 | `scrapers/enrichment/llm_enricher.py` |
| **Phase 5** | 网站集成（产品页、人物页） | `website/src/` |
| **Phase 6** | CI/CD 更新 | `.github/workflows/` |

---

## 六、新增依赖

```toml
# pyproject.toml 新增
anthropic>=0.30        # T3 LLM 丰富
playwright>=1.40       # 官网动态爬取
lxml>=5.0              # HTML 解析
feedparser>=6.0        # TechCrunch RSS
SPARQLWrapper>=2.0     # Wikidata SPARQL
```

---

## 七、验证方式

1. `aiscrape validate` — 验证三种实体类型 + 跨实体引用完整性
2. `pytest tests/ -v --cov=scrapers` — 80%+ 覆盖率
3. `ruff check scrapers/ && mypy scrapers/` — 代码质量
4. 迁移后对比：`ai-other` 占比从 62% 降至 <15%，损坏数据清零
5. 网站 `npm run build` — 确认静态导出正常

---

## 八、成功标准

- [ ] 三实体独立存储（Company, Product, Person）
- [ ] 106 家公司无损迁移到新 schema
- [ ] 嵌套产品/人物提取为独立文件
- [ ] `ai-other` 占比从 62% 降至 <15%（通过 LLM 分类）
- [ ] 损坏的国家字段全部清理
- [ ] 招聘爬虫仅产出 DiscoveredName
- [ ] 字段级溯源追踪
- [ ] 分层合并防止低质数据覆盖高质数据
- [ ] 至少 3 个新权威数据源上线
- [ ] 测试覆盖率 >= 80%
