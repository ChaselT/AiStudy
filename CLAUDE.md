# AI 学习项目记忆（换账号/换机器后请先读完本文件）

这是一个「Java 工程师转行 AI 工程师」的学习项目。无论用哪个账号打开本项目，Claude 都应按本文件约定协助学习。

## 学员画像

- 在职 Java 后端工程师，转行 AI 应用工程师（先应用后深入路线）
- 每天约 2 小时学习时间（工作日晚间为主），全程用**中文**沟通
- Python 起点：会基本语法；讲解新概念**优先用 Java 类比**（uv↔Maven、pydantic↔POJO/Bean Validation、FastAPI↔Spring Boot、装饰器↔注解+AOP、asyncio↔CompletableFuture）

## 关键路径

| 内容 | 位置 |
|------|------|
| 总计划 + 里程碑 | 本目录 `PLAN.md` |
| 学习文档（知识图谱） | `D:\ObsidianVault\AI学习\`，入口 `00-总览\AI学习地图.md` |
| 当前进度 | `D:\ObsidianVault\AI学习\00-总览\学习进度.md`（**每次会话先看这个**判断学到哪了） |
| 代码实战 | 本目录 `phase0-python/` ~ `phase4-finetune/`（按阶段） |

## 硬件（2026-07 确认）

RTX 2080 Ti **魔改 22GB 显存**（WMI 会误报 4GB，以 nvidia-smi 为准）、i7-13700KF、64GB 内存、CUDA 13.1、Windows 11。
- 能力：本地推理 Qwen2.5-14B 流畅、32B-Q4 勉强；QLoRA 微调 14B；CV 训练无压力
- 限制：Turing sm_75 无 BF16，训练用 FP16
- 系统有 SOCKS 代理：Python 里 httpx 需装 `httpx[socks]`

## 工作约定（Claude 必须遵守）

1. **学习文档由 Claude 生成**，不让学员上网找课。每进入新阶段，在 Obsidian `AI学习\` 对应目录生成该阶段文档：每篇一个概念、frontmatter tags（`AI学习` + `阶段N` + 主题）、Java 类比、可运行代码示例、动手任务（指向对应 phase 目录）、`[[双链]]`关联；每阶段一篇 MOC。深度根据学员上一阶段的掌握情况调整。
2. **阶段测试守门**：生成新阶段文档时必须同时生成 `阶段N测试.md`（笔试 40 分 + 实操 60 分，实操代码 `exam_` 前缀）。学员说「批改阶段N测试」时按卷面评分标准批改，**≥80 分才进下一阶段**，不达标指出薄弱笔记、复习后**换题重考**。批改发现的错题记入 Obsidian `00-总览\错题与复盘.md`（含正确理解和关联笔记双链），阶段测试前提醒学员先刷错题。
3. **进度记录**：帮学员更新 `学习进度.md` 的勾选和周记；每 4 周提醒复盘；进度允许 ±2 周浮动。
4. **代码全进 Git**：本目录已是 Git 仓库，远程 `https://github.com/ChaselT/AiStudy`（私有）；知识库仓库 `https://github.com/ChaselT/ObsidianVault`（私有，144MB 的 xlsx 大文件已 gitignore）。**每次学习会话结束时帮学员 commit + push 两个仓库**。密钥走环境变量/.env（已在 .gitignore），绝不硬编码。注意：新阶段用 `uv init` 时加 `--vcs none`，避免嵌套 git 仓库（phase0 踩过坑）。
5. 学习之外的杂项临时文件不要写进本目录。

## 阶段一览（详见 PLAN.md）

0 环境+Python（2周）→ 1 LLM API（项目①CLI助手）→ 2 RAG（项目②知识库问答）→ 3 Agent+工程化（项目③，简历主打，含多模态）→ 4 深度学习原理 + CV训练（项目⑤YOLO）+ LLM微调（项目④QLoRA 14B）→ 5 求职冲刺（2027-04 起投递，双轨：AI应用工程师主攻 + Java+AI混合岗保底）

## 大事记（重要节点追加在此，保持简短）

- 2026-07-24：计划制定；Obsidian 图谱骨架 + 阶段 0/1 文档与测试卷生成；uv 环境跑通（`phase0-python/hello_async.py`）；两仓库推送 GitHub（ChaselT/AiStudy、ChaselT/ObsidianVault，均私有）；全局命令 `/ai-study` 就绪
