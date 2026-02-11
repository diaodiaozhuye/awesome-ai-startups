# 贡献指南

感谢你对 AI 产品数据项目的关注！

## 贡献方式

### 1. 添加新公司

最简单的贡献方式！在 `data/companies/` 中创建新的 JSON 文件：

1. Fork 本仓库
2. 创建新文件 `data/companies/<slug>.json`（slug = 小写字母 + 连字符）
3. 遵循 `data/schema/company.schema.json` 中的模式
4. 运行 `aiscrape validate` 检查文件
5. 运行 `aiscrape generate-stats` 更新索引和统计
6. 提交 Pull Request

**最少必填字段：**
```json
{
  "slug": "your-company",
  "name": "Your Company",
  "description": "公司简介（至少 10 个字符）。",
  "website": "https://your-company.com",
  "category": "ai-other",
  "founded_year": 2024,
  "headquarters": {
    "city": "北京",
    "country": "China"
  }
}
```

### 2. 更新现有数据

发现过时或错误的数据？编辑相关 JSON 文件并提交 PR。

- 只修改你有可靠来源的字段
- 将来源 URL 添加到 `meta.sources` 数组
- 不要删除现有数据，除非明确有误

### 3. 添加新爬虫数据源

1. 在 `scrapers/sources/` 中创建新文件
2. 继承 `BaseScraper` 并实现 `source_name` 和 `scrape()` 方法
3. 在 `scrapers/sources/__init__.py` 中注册
4. 在 `tests/` 中添加测试
5. 提交 PR

### 4. 改进网站

网站位于 `website/` 目录，使用 Next.js + TypeScript + Tailwind。

```bash
cd website
npm install
npm run dev    # 开发服务器
npm run build  # 生产构建
```

### 5. 报告问题

使用 issue 模板报告：
- 数据错误或过时信息
- 网站 Bug
- 功能请求

## 开发环境

```bash
# 克隆
git clone https://github.com/diaodiaozhuye/awesome-ai-startups.git
cd awesome-ai-startups

# Python 环境
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 校验数据
aiscrape validate

# 网站开发
cd website && npm install && npm run dev
```

## 代码规范

- **Python**：PEP 8，类型注解，ruff 检查
- **TypeScript**：ESLint + Next.js 默认规则
- **数据**：必须通过 JSON Schema 校验
- **提交**：约定式提交（feat:, fix:, chore:, docs:）

感谢你帮助构建最全面的开源 AI 产品数据集！
