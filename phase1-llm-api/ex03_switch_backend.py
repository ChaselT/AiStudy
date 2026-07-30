"""阶段 1 · 《Chat Completions API》· 动手任务 3

任务：一份代码跑通两个后端。
1. 用环境变量 `LLM_BASE_URL` / `LLM_MODEL`（以及 `LLM_API_KEY`）控制客户端配置
2. 同一份代码，不改一行，分别跑通：
   - DeepSeek 云端 API
   - 本地 Ollama（qwen2.5:14b）
3. 打印当前实际使用的 base_url 与 model，方便确认真的切过去了

要求/提示：
- 给环境变量设合理的默认值（读不到时走本地 Ollama，免费不烧钱）
- 切换方式：改 `.env`，或在 PowerShell 里 `$env:LLM_MODEL = "..."` 后再跑
- 这就是项目①"可切换后端"的雏形，写得干净点，后面能直接复用
- 完成标准：两个后端各跑一次并截图/记录输出，注释里写下两者回复风格的差异
"""
