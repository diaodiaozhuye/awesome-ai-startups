# AI 公司目录

[![Daily Scrape](https://github.com/ai-company-directory/ai-company-directory/actions/workflows/daily-scrape.yml/badge.svg)](https://github.com/ai-company-directory/ai-company-directory/actions/workflows/daily-scrape.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[English](README.md) | 中文

一个**开源、Git 原生的数据仓库**，追踪全球 AI 创业公司和企业。

- **数据即代码**：每个公司是 `data/companies/` 中的一个 JSON 文件，Git 版本控制，完整历史记录
- **自动更新**：Python 爬虫通过 GitHub Actions 每日运行，发现新公司并丰富已有数据
- **静态网站**：Next.js 静态站点用于本地或自定义部署，支持搜索、筛选、对比和数据分析
- **社区驱动**：通过 Pull Request 添加公司或数据源

## 快速开始

### 浏览数据

**在线访问**：[awesome-ai-startups.vercel.app](https://awesome-ai-startups.vercel.app/zh)

或本地运行网站：

```bash
cd website
npm install
npm run dev
```

或直接浏览 [`data/companies/`](data/companies/) 中的 JSON 文件。

### 使用 CLI

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


## 数据模式

每个公司 JSON 文件遵循 [`data/schema/company.schema.json`](data/schema/company.schema.json) 中定义的模式。

核心字段：`slug`、`name`、`description`、`website`、`category`、`founded_year`、`headquarters`、`funding`、`team`、`social`、`products`、`tags`、`open_source`、`status`。

## 收录的 28 家种子公司

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

## 贡献

请查看 [CONTRIBUTING_ZH.md](CONTRIBUTING_ZH.md) 了解如何：
- 通过 PR 添加新公司
- 添加新爬虫数据源
- 改进网站
- 报告数据问题

## 许可证

MIT 许可证。详见 [LICENSE](LICENSE)。

数据来源于公开信息。公司标志和商标归各自所有者所有。
