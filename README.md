# AiStudy — Java 工程师转型 AI 应用工程师·学习代码全记录

一名后端 Java 工程师从零转型 AI 应用工程师的完整学习轨迹（2026-07 启程，规划 10-13 个月）。本仓库存放全程的实战代码；配套的知识图谱笔记在姊妹仓库 [ai-learning-notes](https://github.com/ChaselT/ai-learning-notes)。

## 学习路线

| 阶段 | 主题 | 产出 | 目录 |
|------|------|------|------|
| 0 | Python 从零到工程化（uv/typing/pydantic/async） | 30+ 练习 | `phase0-python/` |
| 1 | LLM API 应用开发 | 项目① CLI 智能助手 | `phase1-llm-api/` |
| 2 | RAG 与向量检索 | 项目② 知识库问答系统 | `phase2-rag/` |
| 3 | Agent 开发与工程化（LangGraph 1.x / MCP / Spring AI 2.0） | 项目③ 企业级 Agent 应用 | `phase3-agent/` |
| 4 | 深度学习原理 + CV 训练 + LLM 微调 | 项目④ QLoRA 微调模型；项目⑤ YOLO 图像识别 | `phase4-*/` |
| 5 | 作品集与求职 | 简历级项目打磨 | — |

## 学习方法论

- **AI 教练制**：由 Claude 生成体系化教学文档 + 布置作业 + 批改 review + 阶段测试守门（≥80 分过关），学习代码全部本人手写（教练模式：AI 只指点不代写）
- **双轨制**：Obsidian 知识图谱学理论，本仓库动手实战；错题本闭环复盘
- **白天输入、晚上输出**：碎片时间预习笔记，整块时间写代码
- 环境：Windows 11 + uv + Python 3.11 + RTX 2080 Ti 22G（本地跑 14B 模型 / QLoRA 微调）

## 约定

- 每个 phase 目录是独立 uv 项目；练习文件头的 docstring 即题目
- 全程 mypy + Ruff 把关；提交历史即学习日历
