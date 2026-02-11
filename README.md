# AI Company Directory

[![Daily Scrape](https://github.com/ai-company-directory/ai-company-directory/actions/workflows/daily-scrape.yml/badge.svg)](https://github.com/ai-company-directory/ai-company-directory/actions/workflows/daily-scrape.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

<details>
<summary>中文</summary>

## AI 公司目录

一个**开源、Git 原生的数据仓库**，追踪全球 AI 创业公司和企业。

- **数据即代码**：每个公司是 `data/companies/` 中的一个 JSON 文件，Git 版本控制，完整历史记录
- **自动更新**：Python 爬虫通过 GitHub Actions 每日运行，发现新公司并丰富已有数据
- **静态网站**：Next.js 静态站点用于本地或自定义部署，支持搜索、筛选、对比和数据分析
- **社区驱动**：通过 Pull Request 添加公司或数据源

### 快速开始

#### 浏览数据

本地运行网站：

```bash
cd website
npm install
npm run dev
```

或直接浏览 [`data/companies/`](data/companies/) 中的 JSON 文件。

#### 使用 CLI

```bash
# 安装
pip install -e .

# 校验所有公司数据
aiscrape validate

# 查看单个公司
aiscrape show openai

# 生成统计数据和索引
aiscrape generate-stats

# 运行爬虫（干跑模式）
aiscrape scrape --source github --dry-run

# 运行所有爬虫
aiscrape scrape --source all --limit 50
```

#### 构建网站

```bash
cd website
npm install
npm run build    # 静态导出到 out/
npx serve out    # 本地预览
```

### 数据模式

每个公司 JSON 文件遵循 [`data/schema/company.schema.json`](data/schema/company.schema.json) 中定义的模式。

核心字段：`slug`、`name`、`description`、`website`、`category`、`founded_year`、`headquarters`、`funding`、`team`、`social`、`products`、`tags`、`open_source`、`status`。

### 收录的 28 家种子公司

| 分类 | 公司 |
|------|------|
| 大语言模型 | OpenAI, Anthropic, Mistral AI, DeepSeek, 智谱 AI, Cohere, 百川智能 |
| AI 编程 | GitHub Copilot, Cursor, Replit |
| AI 图像/视频 | Midjourney, Runway, Stability AI, Pika |
| AI 语音 | ElevenLabs |
| AI 搜索 | Perplexity AI |
| AI 机器人 | Figure AI, 1X Technologies |
| AI 基础设施 | Hugging Face |
| AI 数据 | Databricks, Scale AI |
| AI 助手 | Inflection AI, Character.AI, 月之暗面 |
| AI 企业 | Jasper AI |
| 自动驾驶 | Waymo |
| AI 安全 | Shield AI |
| AI 医疗 | Recursion |

### 贡献

请查看 [CONTRIBUTING_ZH.md](CONTRIBUTING_ZH.md) 了解如何：
- 通过 PR 添加新公司
- 添加新爬虫数据源
- 改进网站
- 报告数据问题

### 许可证

MIT 许可证。详见 [LICENSE](LICENSE)。

数据来源于公开信息。公司标志和商标归各自所有者所有。

</details>

An **open-source, Git-native data repository** tracking AI startups and companies worldwide.

- **Data as Code**: Each company is a JSON file in `data/companies/`, version-controlled with full Git history
- **Automated Updates**: Python scrapers run daily via GitHub Actions, discovering new companies and enriching existing data
- **Static Website**: Next.js static site for local or custom-hosted use with search, filtering, comparison, and analytics
- **Community-Driven**: Add companies or data sources via Pull Requests

## Quick Start

### Browse the Data

Run the website locally:

```bash
cd website
npm install
npm run dev
```

Or browse the raw JSON files in [`data/companies/`](data/companies/).

### Use the CLI

```bash
# Install
pip install -e .

# Validate all company data
aiscrape validate

# View a company
aiscrape show openai

# Generate stats and index
aiscrape generate-stats

# Run scrapers (dry run)
aiscrape scrape --source github --dry-run

# Run all scrapers
aiscrape scrape --source all --limit 50
```

### Build the Website

```bash
cd website
npm install
npm run build    # Static export to out/
npx serve out    # Preview locally
```

## Project Structure

```
ai-company-directory/
├── data/
│   ├── companies/          # One JSON file per company (28 seed companies)
│   ├── schema/             # JSON Schema definition
│   ├── categories.json     # Category taxonomy (EN/ZH)
│   ├── tags.json           # Tag list
│   ├── index.json          # [Auto-generated] Lightweight company index
│   └── stats.json          # [Auto-generated] Aggregated statistics
├── scrapers/               # Python scraper framework
│   ├── sources/            # GitHub, Y Combinator, Product Hunt, etc.
│   ├── enrichment/         # Normalize, deduplicate, merge
│   ├── validation/         # JSON Schema validation
│   └── generators/         # Generate index.json and stats.json
├── website/                # Next.js static site (SSG)
├── tests/                  # pytest test suite
├── .github/workflows/      # CI/CD pipelines
└── scripts/                # Utility scripts
```

## Data Schema

Each company JSON file follows the schema defined in [`data/schema/company.schema.json`](data/schema/company.schema.json).

Key fields: `slug`, `name`, `description`, `website`, `category`, `founded_year`, `headquarters`, `funding`, `team`, `social`, `products`, `tags`, `open_source`, `status`.

## Scraper Architecture

```
[Source Scrapers] -> ScrapedCompany list
       |
[Normalizer] -> Standardize names/URLs/countries
       |
[Deduplicator] -> Match against existing data
       |
[Merger] -> Non-destructive merge (never overwrites manual edits)
       |
[Validator] -> JSON Schema check
       |
[Write to data/companies/*.json]
```

Available sources:
| Source | Status | API |
|--------|--------|-----|
| GitHub Trending | Active | REST API |
| Y Combinator | Active | Algolia API |
| Product Hunt | Active | GraphQL API |
| Crunchbase | Stub | REST API |
| TechCrunch | Stub | RSS |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new companies via PR
- Adding new scraper sources
- Improving the website
- Reporting data issues

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Data | JSON flat files + JSON Schema |
| Scrapers | Python 3.11 + httpx + BeautifulSoup |
| CLI | Click |
| Website | Next.js 15 + React 19 + TypeScript |
| Styling | Tailwind CSS |
| Search | Fuse.js (client-side) |
| Charts | Recharts |
| CI/CD | GitHub Actions |
| Hosting | Local / Custom Hosting |

## License

MIT License. See [LICENSE](LICENSE).

Data is sourced from publicly available information. Company logos and trademarks belong to their respective owners.
