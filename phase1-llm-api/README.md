# 阶段 1 · LLM 应用开发

对应笔记：`D:\ObsidianVault\AI学习\02-LLM应用开发\`，入口 `02-LLM应用开发-MOC.md`。

## 本阶段目标

从"会调 HTTP 接口的 Java 工程师"变成"能独立开发 LLM 应用的 AI 工程师"：

- 能解释 LLM 为什么会幻觉、多轮对话为什么要每次带全部历史
- 能不看笔记写出带流式输出的多轮对话脚本
- 能跑通 Function Calling 完整闭环（模型请求调用 → 执行函数 → 回传结果）
- 能用 pydantic 校验 LLM 的 JSON 输出并实现失败重试
- 本地 Ollama 跑通 qwen2.5:14b，并用 openai SDK 连接它
- 用 FastAPI 写出 SSE 流式聊天接口
- 完成项目①：CLI 智能助手

## 配置密钥

```powershell
# 在本目录下
Copy-Item .env.example .env
# 然后编辑 .env 填入真实密钥
```

`.env` 已被仓库根目录 `.gitignore` 忽略，**密钥永远不写进代码**。
`.env.example` 里列了各个 key 去哪申请。

本阶段全程可用 **DeepSeek（便宜）+ 本地 Ollama（免费）**，接口与 OpenAI 兼容，
只需改 `LLM_BASE_URL` / `LLM_MODEL`，没有 OpenAI 账号不影响学习。

## 运行练习

```powershell
uv run ex01_hallucination.py          # 单个练习脚本
uv run mypy ex07_todo_parser.py       # 类型检查
uv run ruff check .                   # 代码规范
uv run uvicorn chat_service.main:app --reload --port 8000   # FastAPI 服务
uv run project_cli_assistant/main.py  # 项目①
```

依赖已装好：`openai` `tiktoken` `pydantic` `python-dotenv` `fastapi[standard]` `httpx[socks]`，
开发依赖 `mypy` `pytest` `ruff`。新增依赖用 `uv add xxx`。

> 注意：本机有 SOCKS 代理，httpx 必须带 `[socks]` extra，漏了会 ImportError。

## 目录说明

| 路径 | 内容 |
|---|---|
| `ex01_*.py` ~ `ex10_*.py` | 各篇笔记的动手任务（编号对应 MOC 的学习顺序） |
| `notes_01_base_vs_instruct.md` | 第 1 篇的实验记录文件 |
| `prompts/` | prompt 模板目录（第 6 篇任务 3：prompt 与代码分离） |
| `chat_service/` | FastAPI 服务（第 11 篇） |
| `project_cli_assistant/` | 项目①：CLI 智能助手 |
| `data/` | 测试图片、对话历史等（已被 .gitignore 忽略，不进 Git） |

## 学习节奏

| 周次 | 内容 | 产出 |
|---|---|---|
| 第 1 周 | 原理速览 + Token + Chat API | ex01~ex03 |
| 第 2 周 | 采样参数 + 流式 + Prompt 工程 | ex04~ex06 + prompts 模板库 |
| 第 3 周 | 结构化输出 + Function Calling | ex07~ex08 |
| 第 4 周 | 多模态 + Ollama + FastAPI | ex09~ex10 + chat_service |
| 第 5 周 | 项目①：CLI 智能助手 | 完整项目 + 自测 |

**原则：每篇笔记的动手任务做完再进下一篇。** 最后通过《阶段1测试》（≥80 分）才进入阶段 2。
