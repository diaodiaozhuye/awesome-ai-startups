#!/usr/bin/env python3
"""Generate seed data for 28 AI companies.

Usage:
    python scripts/seed_data.py
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

COMPANIES_DIR = Path(__file__).resolve().parent.parent / "data" / "companies"

TODAY = date.today().isoformat()

SEED_COMPANIES: list[dict] = [
    # --- LLM / Foundation Model ---
    {
        "slug": "openai",
        "name": "OpenAI",
        "name_zh": "OpenAI",
        "description": "OpenAI is an AI research and deployment company that builds general-purpose AI systems. Creator of GPT-4, ChatGPT, and DALL-E.",
        "description_zh": "OpenAI 是一家 AI 研究与部署公司，构建通用人工智能系统。GPT-4、ChatGPT 和 DALL-E 的创造者。",
        "website": "https://openai.com",
        "category": "llm-foundation-model",
        "tags": ["generative-ai", "nlp", "transformer", "multimodal", "api-platform", "chatbot"],
        "founded_year": 2015,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 11300000000,
            "last_round": "growth",
            "last_round_date": "2024-10-02",
            "valuation_usd": 157000000000,
            "investors": ["Microsoft", "Thrive Capital", "Khosla Ventures", "SoftBank"]
        },
        "team": {
            "employee_count_range": "1001-5000",
            "founders": [
                {"name": "Sam Altman", "title": "CEO"},
                {"name": "Greg Brockman", "title": "President"},
                {"name": "Ilya Sutskever", "title": "Co-founder"}
            ]
        },
        "social": {
            "github": "https://github.com/openai",
            "twitter": "@OpenAI",
            "linkedin": "https://linkedin.com/company/openai",
            "crunchbase": "https://www.crunchbase.com/organization/openai"
        },
        "products": [
            {"name": "ChatGPT", "description": "Conversational AI assistant", "url": "https://chat.openai.com"},
            {"name": "GPT-4", "description": "Large multimodal model", "url": "https://openai.com/gpt-4"},
            {"name": "DALL-E", "description": "Text-to-image generation", "url": "https://openai.com/dall-e-3"},
            {"name": "Sora", "description": "Text-to-video generation", "url": "https://openai.com/sora"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "anthropic",
        "name": "Anthropic",
        "name_zh": "Anthropic",
        "description": "Anthropic is an AI safety company building reliable, interpretable, and steerable AI systems. Creator of the Claude family of AI assistants.",
        "description_zh": "Anthropic 是一家 AI 安全公司，致力于构建可靠、可解释、可控的 AI 系统。Claude 系列 AI 助手的创造者。",
        "website": "https://www.anthropic.com",
        "category": "llm-foundation-model",
        "tags": ["generative-ai", "nlp", "transformer", "api-platform", "chatbot", "b2b"],
        "founded_year": 2021,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 7300000000,
            "last_round": "series-d",
            "last_round_date": "2024-03-27",
            "valuation_usd": 18400000000,
            "investors": ["Google", "Amazon", "Spark Capital", "Salesforce Ventures"]
        },
        "team": {
            "employee_count_range": "501-1000",
            "founders": [
                {"name": "Dario Amodei", "title": "CEO"},
                {"name": "Daniela Amodei", "title": "President"}
            ]
        },
        "social": {
            "github": "https://github.com/anthropics",
            "twitter": "@AnthropicAI",
            "linkedin": "https://linkedin.com/company/anthropicresearch",
            "crunchbase": "https://www.crunchbase.com/organization/anthropic"
        },
        "products": [
            {"name": "Claude", "description": "AI assistant for work and conversation", "url": "https://claude.ai"},
            {"name": "Claude API", "description": "API for building with Claude models", "url": "https://docs.anthropic.com"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "mistral-ai",
        "name": "Mistral AI",
        "name_zh": "Mistral AI",
        "description": "Mistral AI is a French AI company building open and portable generative AI models. Known for efficient, open-weight models.",
        "description_zh": "Mistral AI 是一家法国 AI 公司，构建开放和便携的生成式 AI 模型。以高效开源模型闻名。",
        "website": "https://mistral.ai",
        "category": "llm-foundation-model",
        "tags": ["generative-ai", "nlp", "transformer", "open-source", "api-platform", "europe"],
        "founded_year": 2023,
        "headquarters": {"city": "Paris", "country": "France", "country_code": "FR"},
        "funding": {
            "total_raised_usd": 2000000000,
            "last_round": "series-b",
            "last_round_date": "2024-06-11",
            "valuation_usd": 6000000000,
            "investors": ["Andreessen Horowitz", "General Catalyst", "Lightspeed Venture Partners"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [
                {"name": "Arthur Mensch", "title": "CEO"},
                {"name": "Timothee Lacroix", "title": "CTO"},
                {"name": "Guillaume Lample", "title": "Chief Scientist"}
            ]
        },
        "social": {
            "github": "https://github.com/mistralai",
            "twitter": "@MistralAI",
            "linkedin": "https://linkedin.com/company/mistral-ai",
            "crunchbase": "https://www.crunchbase.com/organization/mistral-ai"
        },
        "products": [
            {"name": "Mistral Large", "description": "Flagship large language model", "url": "https://mistral.ai"},
            {"name": "Le Chat", "description": "Conversational AI assistant", "url": "https://chat.mistral.ai"}
        ],
        "open_source": True,
        "status": "active",
    },
    {
        "slug": "deepseek",
        "name": "DeepSeek",
        "name_zh": "深度求索",
        "description": "DeepSeek is a Chinese AI company focused on building powerful open-source large language models for research and applications.",
        "description_zh": "深度求索是一家中国 AI 公司，专注于构建强大的开源大语言模型，服务于研究和应用。",
        "website": "https://www.deepseek.com",
        "category": "llm-foundation-model",
        "tags": ["generative-ai", "nlp", "transformer", "open-source", "china"],
        "founded_year": 2023,
        "headquarters": {"city": "Hangzhou", "country": "China", "country_code": "CN"},
        "funding": {
            "total_raised_usd": 0,
            "last_round": "unknown"
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [{"name": "Liang Wenfeng", "title": "CEO"}]
        },
        "social": {
            "github": "https://github.com/deepseek-ai",
            "twitter": "@deepseek_ai"
        },
        "products": [
            {"name": "DeepSeek-V3", "description": "Open-source large language model", "url": "https://www.deepseek.com"},
            {"name": "DeepSeek Coder", "description": "Code generation model", "url": "https://github.com/deepseek-ai/DeepSeek-Coder"}
        ],
        "open_source": True,
        "status": "active",
    },
    {
        "slug": "zhipu-ai",
        "name": "Zhipu AI",
        "name_zh": "智谱 AI",
        "description": "Zhipu AI is a Chinese AI company building large language models and cognitive intelligence technology, spun out of Tsinghua University.",
        "description_zh": "智谱 AI 是一家源自清华大学的中国 AI 公司，致力于构建大语言模型和认知智能技术。",
        "website": "https://www.zhipuai.cn",
        "category": "llm-foundation-model",
        "tags": ["generative-ai", "nlp", "transformer", "api-platform", "china"],
        "founded_year": 2019,
        "headquarters": {"city": "Beijing", "country": "China", "country_code": "CN"},
        "funding": {
            "total_raised_usd": 400000000,
            "last_round": "series-b",
            "investors": ["Hillhouse Capital", "Lenovo Capital"]
        },
        "team": {
            "employee_count_range": "201-500",
            "founders": [{"name": "Zhang Peng", "title": "CEO"}]
        },
        "social": {
            "github": "https://github.com/THUDM",
            "twitter": "@thaboramureri"
        },
        "products": [
            {"name": "GLM-4", "description": "Large language model", "url": "https://open.bigmodel.cn"},
            {"name": "ChatGLM", "description": "Open-source conversational model", "url": "https://github.com/THUDM/ChatGLM-6B"}
        ],
        "open_source": True,
        "status": "active",
    },
    {
        "slug": "cohere",
        "name": "Cohere",
        "name_zh": "Cohere",
        "description": "Cohere builds enterprise-grade large language models and RAG solutions. Focused on making NLP accessible for business applications.",
        "description_zh": "Cohere 构建企业级大语言模型和 RAG 解决方案。专注于让 NLP 服务于商业应用。",
        "website": "https://cohere.com",
        "category": "llm-foundation-model",
        "tags": ["generative-ai", "nlp", "transformer", "api-platform", "b2b", "rag"],
        "founded_year": 2019,
        "headquarters": {"city": "Toronto", "country": "Canada", "country_code": "CA"},
        "funding": {
            "total_raised_usd": 970000000,
            "last_round": "series-d",
            "last_round_date": "2024-07-22",
            "valuation_usd": 5500000000,
            "investors": ["PSP Investments", "Nvidia", "Salesforce Ventures", "Cisco Investments"]
        },
        "team": {
            "employee_count_range": "201-500",
            "founders": [
                {"name": "Aidan Gomez", "title": "CEO"},
                {"name": "Ivan Zhang", "title": "Co-founder"},
                {"name": "Nick Frosst", "title": "Co-founder"}
            ]
        },
        "social": {
            "github": "https://github.com/cohere-ai",
            "twitter": "@CohereAI",
            "linkedin": "https://linkedin.com/company/cohere-ai",
            "crunchbase": "https://www.crunchbase.com/organization/cohere-2"
        },
        "products": [
            {"name": "Command", "description": "Enterprise LLM for business", "url": "https://cohere.com/command"},
            {"name": "Embed", "description": "Text embedding model", "url": "https://cohere.com/embed"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Coding ---
    {
        "slug": "github-copilot",
        "name": "GitHub Copilot",
        "name_zh": "GitHub Copilot",
        "description": "GitHub Copilot is an AI pair programmer developed by GitHub and OpenAI that provides code suggestions directly in the editor.",
        "description_zh": "GitHub Copilot 是由 GitHub 和 OpenAI 开发的 AI 编程助手，在编辑器中直接提供代码建议。",
        "website": "https://github.com/features/copilot",
        "category": "ai-coding",
        "tags": ["code-generation", "copilot", "developer-tools"],
        "founded_year": 2021,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "team": {"employee_count_range": "51-200"},
        "social": {
            "github": "https://github.com/github/copilot-docs",
            "twitter": "@GitHubCopilot"
        },
        "products": [
            {"name": "GitHub Copilot", "description": "AI pair programmer", "url": "https://github.com/features/copilot"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "cursor",
        "name": "Cursor",
        "name_zh": "Cursor",
        "description": "Cursor is an AI-native code editor built to make programming with AI effortless, featuring intelligent code completion and chat.",
        "description_zh": "Cursor 是一款 AI 原生代码编辑器，旨在让 AI 编程变得轻松，具有智能代码补全和对话功能。",
        "website": "https://cursor.com",
        "category": "ai-coding",
        "tags": ["code-generation", "copilot", "developer-tools", "b2c"],
        "founded_year": 2022,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 400000000,
            "last_round": "series-b",
            "valuation_usd": 2500000000,
            "investors": ["Andreessen Horowitz", "Thrive Capital"]
        },
        "team": {
            "employee_count_range": "11-50",
            "founders": [
                {"name": "Michael Truell", "title": "CEO"},
                {"name": "Sualeh Asif", "title": "Co-founder"},
                {"name": "Arvid Lunnemark", "title": "Co-founder"},
                {"name": "Aman Sanger", "title": "Co-founder"}
            ]
        },
        "social": {
            "twitter": "@cursor_ai",
            "linkedin": "https://linkedin.com/company/cursor-ai"
        },
        "products": [
            {"name": "Cursor Editor", "description": "AI-native code editor", "url": "https://cursor.com"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "replit",
        "name": "Replit",
        "name_zh": "Replit",
        "description": "Replit is a collaborative coding platform with AI-powered features that enables anyone to build software directly in the browser.",
        "description_zh": "Replit 是一个协作编程平台，具有 AI 驱动的功能，让任何人都能直接在浏览器中构建软件。",
        "website": "https://replit.com",
        "category": "ai-coding",
        "tags": ["code-generation", "developer-tools", "b2c", "saas"],
        "founded_year": 2016,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 222000000,
            "last_round": "series-b",
            "valuation_usd": 1160000000,
            "investors": ["Andreessen Horowitz", "Khosla Ventures", "Coatue"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [{"name": "Amjad Masad", "title": "CEO"}]
        },
        "social": {
            "github": "https://github.com/replit",
            "twitter": "@Replit",
            "linkedin": "https://linkedin.com/company/replit",
            "crunchbase": "https://www.crunchbase.com/organization/replit"
        },
        "products": [
            {"name": "Replit Agent", "description": "AI-powered software builder", "url": "https://replit.com"},
            {"name": "Ghostwriter", "description": "AI code assistant", "url": "https://replit.com/ai"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Image & Video ---
    {
        "slug": "midjourney",
        "name": "Midjourney",
        "name_zh": "Midjourney",
        "description": "Midjourney is an independent research lab producing an AI program that creates images from textual descriptions.",
        "description_zh": "Midjourney 是一个独立研究实验室，开发根据文字描述生成图像的 AI 程序。",
        "website": "https://www.midjourney.com",
        "category": "ai-image-video",
        "tags": ["generative-ai", "text-to-image", "diffusion-model", "b2c"],
        "founded_year": 2021,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "team": {
            "employee_count_range": "11-50",
            "founders": [{"name": "David Holz", "title": "CEO"}]
        },
        "social": {"twitter": "@midaborney"},
        "products": [
            {"name": "Midjourney", "description": "AI image generation from text prompts", "url": "https://www.midjourney.com"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "runway",
        "name": "Runway",
        "name_zh": "Runway",
        "description": "Runway is an applied AI research company building the next generation of creative tools powered by machine learning.",
        "description_zh": "Runway 是一家应用 AI 研究公司，构建下一代由机器学习驱动的创意工具。",
        "website": "https://runwayml.com",
        "category": "ai-image-video",
        "tags": ["generative-ai", "text-to-video", "text-to-image", "content-creation"],
        "founded_year": 2018,
        "headquarters": {"city": "New York", "state": "New York", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 237000000,
            "last_round": "series-c",
            "last_round_date": "2023-06-29",
            "valuation_usd": 1500000000,
            "investors": ["Google", "Nvidia", "Salesforce Ventures", "Felicis Ventures"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [
                {"name": "Cristobal Valenzuela", "title": "CEO"},
                {"name": "Alejandro Matamala", "title": "Co-founder"},
                {"name": "Anastasis Germanidis", "title": "Co-founder"}
            ]
        },
        "social": {
            "github": "https://github.com/runwayml",
            "twitter": "@runaborayml",
            "linkedin": "https://linkedin.com/company/runwayml",
            "crunchbase": "https://www.crunchbase.com/organization/runway-ai"
        },
        "products": [
            {"name": "Gen-3 Alpha", "description": "AI video generation model", "url": "https://runwayml.com"},
            {"name": "Runway Studio", "description": "AI-powered video editing tools", "url": "https://runwayml.com"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "stability-ai",
        "name": "Stability AI",
        "name_zh": "Stability AI",
        "description": "Stability AI is the company behind Stable Diffusion, an open-source text-to-image model that democratized AI image generation.",
        "description_zh": "Stability AI 是 Stable Diffusion 背后的公司，该开源文本转图像模型使 AI 图像生成大众化。",
        "website": "https://stability.ai",
        "category": "ai-image-video",
        "tags": ["generative-ai", "text-to-image", "diffusion-model", "open-source"],
        "founded_year": 2019,
        "headquarters": {"city": "London", "country": "United Kingdom", "country_code": "GB"},
        "funding": {
            "total_raised_usd": 260000000,
            "last_round": "series-b",
            "investors": ["Coatue", "Lightspeed Venture Partners", "Intel Capital"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [{"name": "Emad Mostaque", "title": "Founder"}]
        },
        "social": {
            "github": "https://github.com/Stability-AI",
            "twitter": "@StabilityAI",
            "linkedin": "https://linkedin.com/company/stability-ai",
            "crunchbase": "https://www.crunchbase.com/organization/stability-ai"
        },
        "products": [
            {"name": "Stable Diffusion", "description": "Open-source text-to-image model", "url": "https://stability.ai/stable-diffusion"},
            {"name": "Stable Video", "description": "AI video generation", "url": "https://stability.ai"}
        ],
        "open_source": True,
        "status": "active",
    },
    {
        "slug": "pika",
        "name": "Pika",
        "name_zh": "Pika",
        "description": "Pika is an AI company building tools to make video creation accessible for everyone through generative AI technology.",
        "description_zh": "Pika 是一家 AI 公司，通过生成式 AI 技术让每个人都能轻松创作视频。",
        "website": "https://pika.art",
        "category": "ai-image-video",
        "tags": ["generative-ai", "text-to-video", "content-creation", "b2c"],
        "founded_year": 2023,
        "headquarters": {"city": "Palo Alto", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 135000000,
            "last_round": "series-a",
            "investors": ["Spark Capital", "Lightspeed Venture Partners"]
        },
        "team": {
            "employee_count_range": "11-50",
            "founders": [
                {"name": "Demi Guo", "title": "CEO"},
                {"name": "Chenlin Meng", "title": "CTO"}
            ]
        },
        "social": {"twitter": "@paborika_labs"},
        "products": [
            {"name": "Pika", "description": "AI video generation platform", "url": "https://pika.art"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Audio & Speech ---
    {
        "slug": "elevenlabs",
        "name": "ElevenLabs",
        "name_zh": "ElevenLabs",
        "description": "ElevenLabs is an AI voice technology company providing realistic text-to-speech, voice cloning, and audio AI tools.",
        "description_zh": "ElevenLabs 是一家 AI 语音技术公司，提供逼真的文本转语音、声音克隆和音频 AI 工具。",
        "website": "https://elevenlabs.io",
        "category": "ai-audio-speech",
        "tags": ["text-to-speech", "generative-ai", "api-platform", "content-creation"],
        "founded_year": 2022,
        "headquarters": {"city": "New York", "state": "New York", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 101000000,
            "last_round": "series-b",
            "last_round_date": "2024-01-22",
            "valuation_usd": 1100000000,
            "investors": ["Andreessen Horowitz", "Nat Friedman", "Daniel Gross"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [
                {"name": "Mati Staniszewski", "title": "CEO"},
                {"name": "Piotr Dabkowski", "title": "CTO"}
            ]
        },
        "social": {
            "github": "https://github.com/elevenlabs",
            "twitter": "@elevenlabsio",
            "linkedin": "https://linkedin.com/company/elevenlabsio",
            "crunchbase": "https://www.crunchbase.com/organization/elevenlabs"
        },
        "products": [
            {"name": "ElevenLabs TTS", "description": "Text-to-speech API", "url": "https://elevenlabs.io"},
            {"name": "Voice Lab", "description": "Voice cloning and design", "url": "https://elevenlabs.io/voice-lab"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Search ---
    {
        "slug": "perplexity-ai",
        "name": "Perplexity AI",
        "name_zh": "Perplexity AI",
        "description": "Perplexity AI is an AI-powered answer engine that provides direct, cited answers to questions using real-time web search.",
        "description_zh": "Perplexity AI 是一款 AI 驱动的答案引擎，利用实时网络搜索提供直接且有引用的答案。",
        "website": "https://www.perplexity.ai",
        "category": "ai-search",
        "tags": ["search-engine", "nlp", "rag", "b2c"],
        "founded_year": 2022,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 250000000,
            "last_round": "series-b",
            "valuation_usd": 3000000000,
            "investors": ["IVP", "NEA", "Databricks Ventures", "Jeff Bezos"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [
                {"name": "Aravind Srinivas", "title": "CEO"},
                {"name": "Denis Yarats", "title": "CTO"}
            ]
        },
        "social": {
            "twitter": "@perplexity_ai",
            "linkedin": "https://linkedin.com/company/perplexity-ai",
            "crunchbase": "https://www.crunchbase.com/organization/perplexity-ai"
        },
        "products": [
            {"name": "Perplexity", "description": "AI-powered answer engine", "url": "https://www.perplexity.ai"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Robotics ---
    {
        "slug": "figure-ai",
        "name": "Figure AI",
        "name_zh": "Figure AI",
        "description": "Figure AI is building commercially viable autonomous humanoid robots to address labor shortages in warehouses and manufacturing.",
        "description_zh": "Figure AI 正在构建商业化的自主人形机器人，以解决仓储和制造业的劳动力短缺问题。",
        "website": "https://www.figure.ai",
        "category": "ai-robotics",
        "tags": ["humanoid-robot", "reinforcement-learning", "hardware"],
        "founded_year": 2022,
        "headquarters": {"city": "Sunnyvale", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 675000000,
            "last_round": "series-b",
            "valuation_usd": 2600000000,
            "investors": ["Microsoft", "OpenAI", "Nvidia", "Jeff Bezos"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [{"name": "Brett Adcock", "title": "CEO"}]
        },
        "social": {
            "twitter": "@Figure_robot",
            "linkedin": "https://linkedin.com/company/figureai"
        },
        "products": [
            {"name": "Figure 01", "description": "Autonomous humanoid robot", "url": "https://www.figure.ai"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "1x-technologies",
        "name": "1X Technologies",
        "name_zh": "1X Technologies",
        "description": "1X Technologies (formerly Halodi Robotics) creates human-centric humanoid robots powered by AI for real-world tasks.",
        "description_zh": "1X Technologies（前身为 Halodi Robotics）创建以人为中心的人形机器人，由 AI 驱动完成真实世界任务。",
        "website": "https://www.1x.tech",
        "category": "ai-robotics",
        "tags": ["humanoid-robot", "reinforcement-learning", "hardware", "europe"],
        "founded_year": 2014,
        "headquarters": {"city": "Moss", "country": "Norway", "country_code": "NO"},
        "funding": {
            "total_raised_usd": 125000000,
            "last_round": "series-b",
            "investors": ["OpenAI", "Tiger Global", "Samsung NEXT"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [{"name": "Bernt Oyvind Bornich", "title": "CEO"}]
        },
        "social": {
            "twitter": "@1aborX_Tech",
            "linkedin": "https://linkedin.com/company/1x-technologies"
        },
        "products": [
            {"name": "NEO", "description": "Bipedal humanoid robot", "url": "https://www.1x.tech/neo"},
            {"name": "EVE", "description": "Wheeled humanoid robot", "url": "https://www.1x.tech/eve"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Infrastructure ---
    {
        "slug": "hugging-face",
        "name": "Hugging Face",
        "name_zh": "Hugging Face",
        "description": "Hugging Face is the AI community platform for sharing models, datasets, and apps. Home of the Transformers library and model Hub.",
        "description_zh": "Hugging Face 是用于分享模型、数据集和应用的 AI 社区平台。Transformers 库和模型中心的发源地。",
        "website": "https://huggingface.co",
        "category": "ai-infrastructure",
        "tags": ["open-source", "developer-tools", "model-serving", "mlops", "api-platform"],
        "founded_year": 2016,
        "headquarters": {"city": "New York", "state": "New York", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 395000000,
            "last_round": "series-d",
            "last_round_date": "2023-08-24",
            "valuation_usd": 4500000000,
            "investors": ["Google", "Amazon", "Nvidia", "Salesforce", "Sequoia Capital"]
        },
        "team": {
            "employee_count_range": "201-500",
            "founders": [
                {"name": "Clement Delangue", "title": "CEO"},
                {"name": "Julien Chaumond", "title": "CTO"}
            ]
        },
        "social": {
            "github": "https://github.com/huggingface",
            "twitter": "@huggingface",
            "linkedin": "https://linkedin.com/company/huggingface",
            "crunchbase": "https://www.crunchbase.com/organization/hugging-face"
        },
        "products": [
            {"name": "Transformers", "description": "State-of-the-art ML library", "url": "https://github.com/huggingface/transformers"},
            {"name": "Hub", "description": "Platform for sharing ML models", "url": "https://huggingface.co/models"},
            {"name": "Inference API", "description": "Hosted model inference", "url": "https://huggingface.co/inference-api"}
        ],
        "open_source": True,
        "status": "active",
    },
    # --- AI Data & Analytics ---
    {
        "slug": "databricks",
        "name": "Databricks",
        "name_zh": "Databricks",
        "description": "Databricks is a unified analytics platform built on Apache Spark that combines data engineering, data science, and machine learning.",
        "description_zh": "Databricks 是基于 Apache Spark 构建的统一分析平台，融合了数据工程、数据科学和机器学习。",
        "website": "https://www.databricks.com",
        "category": "ai-data-analytics",
        "tags": ["data-labeling", "mlops", "b2b", "saas", "open-source"],
        "founded_year": 2013,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 4100000000,
            "last_round": "series-i",
            "last_round_date": "2023-09-14",
            "valuation_usd": 43000000000,
            "investors": ["Andreessen Horowitz", "T. Rowe Price", "Nvidia", "Capital One Ventures"]
        },
        "team": {
            "employee_count_range": "5001+",
            "founders": [
                {"name": "Ali Ghodsi", "title": "CEO"},
                {"name": "Matei Zaharia", "title": "CTO"}
            ]
        },
        "social": {
            "github": "https://github.com/databricks",
            "twitter": "@databricks",
            "linkedin": "https://linkedin.com/company/databricks",
            "crunchbase": "https://www.crunchbase.com/organization/databricks"
        },
        "products": [
            {"name": "Lakehouse Platform", "description": "Unified data and AI platform", "url": "https://www.databricks.com/product"},
            {"name": "MLflow", "description": "Open-source ML lifecycle platform", "url": "https://mlflow.org"}
        ],
        "open_source": True,
        "status": "active",
    },
    {
        "slug": "scale-ai",
        "name": "Scale AI",
        "name_zh": "Scale AI",
        "description": "Scale AI provides high-quality training data and AI infrastructure for enterprises building AI applications at scale.",
        "description_zh": "Scale AI 为大规模构建 AI 应用的企业提供高质量训练数据和 AI 基础设施。",
        "website": "https://scale.com",
        "category": "ai-data-analytics",
        "tags": ["data-labeling", "synthetic-data", "b2b", "mlops"],
        "founded_year": 2016,
        "headquarters": {"city": "San Francisco", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 600000000,
            "last_round": "series-e",
            "valuation_usd": 7300000000,
            "investors": ["Accel", "Tiger Global", "Founders Fund", "Index Ventures"]
        },
        "team": {
            "employee_count_range": "501-1000",
            "founders": [
                {"name": "Alexandr Wang", "title": "CEO"},
                {"name": "Lucy Guo", "title": "Co-founder"}
            ]
        },
        "social": {
            "github": "https://github.com/scaleapi",
            "twitter": "@scale_AI",
            "linkedin": "https://linkedin.com/company/scaleai",
            "crunchbase": "https://www.crunchbase.com/organization/scale-ai"
        },
        "products": [
            {"name": "Scale Data Engine", "description": "Data labeling and curation platform", "url": "https://scale.com/data-engine"},
            {"name": "Scale Generative AI Platform", "description": "Enterprise AI evaluation tools", "url": "https://scale.com/generative-ai-platform"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Assistant ---
    {
        "slug": "inflection-ai",
        "name": "Inflection AI",
        "name_zh": "Inflection AI",
        "description": "Inflection AI builds personal AI assistants designed for natural, empathetic conversation. Creator of Pi.",
        "description_zh": "Inflection AI 构建个人 AI 助手，专注于自然、有同理心的对话。Pi 的创造者。",
        "website": "https://inflection.ai",
        "category": "ai-assistant",
        "tags": ["chatbot", "nlp", "b2c"],
        "founded_year": 2022,
        "headquarters": {"city": "Palo Alto", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 1525000000,
            "last_round": "series-b",
            "investors": ["Microsoft", "Reid Hoffman", "Bill Gates", "Nvidia"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [
                {"name": "Mustafa Suleyman", "title": "Co-founder"},
                {"name": "Karén Simonyan", "title": "Co-founder"}
            ]
        },
        "social": {
            "twitter": "@inflaborection_ai",
            "linkedin": "https://linkedin.com/company/inflection-ai"
        },
        "products": [
            {"name": "Pi", "description": "Personal AI assistant", "url": "https://pi.ai"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "character-ai",
        "name": "Character.AI",
        "name_zh": "Character.AI",
        "description": "Character.AI is a platform where users can create and interact with AI-powered characters for conversation and entertainment.",
        "description_zh": "Character.AI 是一个用户可以创建和与 AI 角色互动的平台，用于对话和娱乐。",
        "website": "https://character.ai",
        "category": "ai-assistant",
        "tags": ["chatbot", "generative-ai", "b2c", "content-creation"],
        "founded_year": 2021,
        "headquarters": {"city": "Menlo Park", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 150000000,
            "last_round": "series-a",
            "valuation_usd": 1000000000,
            "investors": ["Andreessen Horowitz", "SV Angel"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [
                {"name": "Noam Shazeer", "title": "CEO"},
                {"name": "Daniel De Freitas", "title": "Co-founder"}
            ]
        },
        "social": {
            "twitter": "@character_ai",
            "linkedin": "https://linkedin.com/company/character-ai"
        },
        "products": [
            {"name": "Character.AI", "description": "AI character chat platform", "url": "https://character.ai"}
        ],
        "open_source": False,
        "status": "active",
    },
    {
        "slug": "moonshot-ai",
        "name": "Moonshot AI",
        "name_zh": "月之暗面",
        "description": "Moonshot AI is a Chinese AI startup building large language models with extremely long context windows.",
        "description_zh": "月之暗面是一家中国 AI 创业公司，构建具有超长上下文窗口的大语言模型。",
        "website": "https://www.moonshot.cn",
        "category": "ai-assistant",
        "tags": ["generative-ai", "nlp", "chatbot", "china"],
        "founded_year": 2023,
        "headquarters": {"city": "Beijing", "country": "China", "country_code": "CN"},
        "funding": {
            "total_raised_usd": 1000000000,
            "last_round": "series-b",
            "valuation_usd": 3000000000,
            "investors": ["Sequoia Capital China", "Hillhouse Capital", "Alibaba"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [{"name": "Yang Zhilin", "title": "CEO"}]
        },
        "social": {"twitter": "@MoonshotAI"},
        "products": [
            {"name": "Kimi", "description": "Long-context AI assistant", "url": "https://kimi.moonshot.cn"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Enterprise ---
    {
        "slug": "jasper-ai",
        "name": "Jasper AI",
        "name_zh": "Jasper AI",
        "description": "Jasper AI is an enterprise AI platform for marketing teams to create on-brand content at scale.",
        "description_zh": "Jasper AI 是面向营销团队的企业 AI 平台，用于大规模创建品牌一致的内容。",
        "website": "https://www.jasper.ai",
        "category": "ai-enterprise",
        "tags": ["content-creation", "marketing", "b2b", "saas"],
        "founded_year": 2021,
        "headquarters": {"city": "Austin", "state": "Texas", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 131000000,
            "last_round": "series-a",
            "valuation_usd": 1500000000,
            "investors": ["Insight Partners", "Bessemer Venture Partners", "IVP"]
        },
        "team": {
            "employee_count_range": "201-500",
            "founders": [
                {"name": "Dave Rogenmoser", "title": "CEO"},
                {"name": "JP Morgan", "title": "CTO"},
                {"name": "Chris Hull", "title": "COO"}
            ]
        },
        "social": {
            "twitter": "@heyjasperai",
            "linkedin": "https://linkedin.com/company/heyjasperai",
            "crunchbase": "https://www.crunchbase.com/organization/jasper-ai"
        },
        "products": [
            {"name": "Jasper", "description": "AI marketing content platform", "url": "https://www.jasper.ai"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- Autonomous Vehicles ---
    {
        "slug": "waymo",
        "name": "Waymo",
        "name_zh": "Waymo",
        "description": "Waymo is an autonomous driving technology company and subsidiary of Alphabet developing self-driving vehicles.",
        "description_zh": "Waymo 是 Alphabet 旗下的自动驾驶技术公司，开发自动驾驶汽车。",
        "website": "https://waymo.com",
        "category": "autonomous-vehicles",
        "tags": ["self-driving", "computer-vision", "reinforcement-learning", "hardware"],
        "founded_year": 2009,
        "headquarters": {"city": "Mountain View", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 5500000000,
            "last_round": "growth",
            "investors": ["Alphabet", "Silver Lake", "Tiger Global", "Andreessen Horowitz"]
        },
        "team": {
            "employee_count_range": "1001-5000",
            "founders": [{"name": "Sebastian Thrun", "title": "Founder"}]
        },
        "social": {
            "github": "https://github.com/waymo-research",
            "twitter": "@Waymo",
            "linkedin": "https://linkedin.com/company/waymo",
            "crunchbase": "https://www.crunchbase.com/organization/waymo"
        },
        "products": [
            {"name": "Waymo One", "description": "Autonomous ride-hailing service", "url": "https://waymo.com/waymo-one"},
            {"name": "Waymo Driver", "description": "Autonomous driving technology", "url": "https://waymo.com/waymo-driver"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Security & Defense ---
    {
        "slug": "shield-ai",
        "name": "Shield AI",
        "name_zh": "Shield AI",
        "description": "Shield AI builds AI-powered defense technology including autonomous drones and intelligent pilot systems.",
        "description_zh": "Shield AI 构建 AI 驱动的国防技术，包括自主无人机和智能飞行员系统。",
        "website": "https://shield.ai",
        "category": "ai-security-defense",
        "tags": ["drone", "defense", "reinforcement-learning", "edge-ai"],
        "founded_year": 2015,
        "headquarters": {"city": "San Diego", "state": "California", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 900000000,
            "last_round": "series-f",
            "valuation_usd": 2700000000,
            "investors": ["Andreessen Horowitz", "Point72", "Snowflake Ventures"]
        },
        "team": {
            "employee_count_range": "501-1000",
            "founders": [
                {"name": "Ryan Tseng", "title": "CEO"},
                {"name": "Brandon Tseng", "title": "President"}
            ]
        },
        "social": {
            "twitter": "@ShieldAI",
            "linkedin": "https://linkedin.com/company/shield-ai",
            "crunchbase": "https://www.crunchbase.com/organization/shield-ai"
        },
        "products": [
            {"name": "Hivemind", "description": "AI pilot for autonomous aircraft", "url": "https://shield.ai/hivemind"},
            {"name": "V-BAT", "description": "Autonomous VTOL drone", "url": "https://shield.ai/v-bat"}
        ],
        "open_source": False,
        "status": "active",
    },
    # --- AI Healthcare ---
    {
        "slug": "recursion",
        "name": "Recursion",
        "name_zh": "Recursion",
        "description": "Recursion is a clinical-stage biotech company using AI and automation to discover new medicines at scale.",
        "description_zh": "Recursion 是一家临床阶段的生物科技公司，利用 AI 和自动化大规模发现新药物。",
        "website": "https://www.recursion.com",
        "category": "ai-healthcare",
        "tags": ["drug-discovery", "computer-vision", "b2b"],
        "founded_year": 2013,
        "headquarters": {"city": "Salt Lake City", "state": "Utah", "country": "United States", "country_code": "US"},
        "funding": {
            "total_raised_usd": 1100000000,
            "last_round": "ipo",
            "investors": ["Baillie Gifford", "SoftBank", "Nvidia"]
        },
        "team": {
            "employee_count_range": "501-1000",
            "founders": [{"name": "Chris Gibson", "title": "CEO"}]
        },
        "social": {
            "github": "https://github.com/recursionpharma",
            "twitter": "@RecursionPharma",
            "linkedin": "https://linkedin.com/company/recursion-pharmaceuticals",
            "crunchbase": "https://www.crunchbase.com/organization/recursion-pharmaceuticals"
        },
        "products": [
            {"name": "Recursion OS", "description": "AI-driven drug discovery platform", "url": "https://www.recursion.com/technology"}
        ],
        "open_source": False,
        "status": "ipo",
    },
    # --- LLM (China) ---
    {
        "slug": "baichuan-ai",
        "name": "Baichuan AI",
        "name_zh": "百川智能",
        "description": "Baichuan AI is a Chinese AI startup developing large language models focused on Chinese language and culture understanding.",
        "description_zh": "百川智能是一家中国 AI 创业公司，开发专注于中文语言和文化理解的大语言模型。",
        "website": "https://www.baichuan-ai.com",
        "category": "llm-foundation-model",
        "tags": ["generative-ai", "nlp", "transformer", "open-source", "china"],
        "founded_year": 2023,
        "headquarters": {"city": "Beijing", "country": "China", "country_code": "CN"},
        "funding": {
            "total_raised_usd": 450000000,
            "last_round": "series-a",
            "investors": ["Tencent", "Alibaba", "Xiaomi"]
        },
        "team": {
            "employee_count_range": "51-200",
            "founders": [{"name": "Wang Xiaochuan", "title": "CEO"}]
        },
        "social": {
            "github": "https://github.com/baichuan-inc",
            "twitter": "@AiBaichuan"
        },
        "products": [
            {"name": "Baichuan-2", "description": "Open-source large language model", "url": "https://github.com/baichuan-inc/Baichuan2"}
        ],
        "open_source": True,
        "status": "active",
    },
]


def write_company(company: dict) -> None:
    """Write a single company JSON file with metadata."""
    company_with_meta = {
        **company,
        "meta": {
            "added_date": TODAY,
            "last_updated": TODAY,
            "sources": [company["website"]],
            "data_quality_score": 0.8,
        },
    }
    filepath = COMPANIES_DIR / f"{company['slug']}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(company_with_meta, f, indent=2, ensure_ascii=False)
    print(f"  Created {filepath.name}")


def main() -> None:
    """Generate all seed company files."""
    os.makedirs(COMPANIES_DIR, exist_ok=True)

    print(f"Generating {len(SEED_COMPANIES)} company files...")
    for company in SEED_COMPANIES:
        write_company(company)

    print(f"\nDone! {len(SEED_COMPANIES)} companies written to {COMPANIES_DIR}")


if __name__ == "__main__":
    main()
