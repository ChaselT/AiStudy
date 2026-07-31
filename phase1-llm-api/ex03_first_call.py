"""阶段 1 · 《Chat Completions API》· 动手任务 1

任务：完成人生第一次 LLM API 调用。
1. 用 openai SDK 发一次 chat completions 请求
2. 打印模型回复内容
3. 打印 `resp.usage`（prompt_tokens / completion_tokens / total_tokens）
4. 给 client 配上 `timeout` 和 `max_retries`
5. **把模型名故意写错一次**，捕获 `NotFoundError` 并打印友好提示
   —— 体会"4xx 是请求本身有问题，重试多少次都没用，不该重试"

要求/提示：
- 密钥**必须**走环境变量，先复制 `.env.example` 为 `.env` 填进去
- 后端三件套（LLM_BASE_URL / LLM_API_KEY / LLM_MODEL）已在 .env 里，读它们而不是硬编码
- 完成标准：终端能看到回复正文和 usage 三个数字；错误模型名那次能捕获并友好提示；
  `.env` 不出现在 `git status` 里
"""
