"""阶段 1 · 《Chat Completions API》· 动手任务 1

任务：完成人生第一次 LLM API 调用。
1. 用 openai SDK 发一次 chat completions 请求
2. 打印模型回复内容
3. 打印 `resp.usage`（prompt_tokens / completion_tokens / total_tokens）

要求/提示：
- 密钥**必须**走环境变量（`DEEPSEEK_API_KEY` 等），先复制 `.env.example` 为 `.env` 填进去
- 用 DeepSeek 云端就设置对应 base_url；用本地 Ollama 则 base_url 指向本地端口
- 完成标准：终端能看到回复正文和 usage 三个数字；`.env` 不出现在 `git status` 里
"""
