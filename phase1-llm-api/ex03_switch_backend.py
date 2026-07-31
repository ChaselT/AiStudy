"""阶段 1 · 《Chat Completions API》· 动手任务 3

任务：一份代码跑通两个后端。
1. 用环境变量 `LLM_BASE_URL` / `LLM_MODEL`（以及 `LLM_API_KEY`）控制客户端配置
2. 同一份代码，不改一行，分别跑通：
   - 云端 API（中转站 / DeepSeek 均可）
   - 本地 Ollama（`qwen3.5:27b`）
3. 打印当前实际使用的 base_url 与 model，方便确认真的切过去了

要求/提示：
- 给环境变量设合理的默认值（读不到时走本地 Ollama，免费不烧钱）
- 切换方式：改 `.env`，或在 PowerShell 里 `$env:LLM_MODEL = "..."` 后再跑
- 这就是项目①"可切换后端"的雏形，写得干净点，后面能直接复用
- 完成标准：两个后端各跑一次并截图/记录输出，注释里写下两者回复风格的差异
"""

import os

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ.get("LLM_API_KEY", "asasd"),  # 从环境变量读，绝不硬编码
    base_url=os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1"),
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def main() -> None:
    model = os.environ.get("LLM_MODEL", "qwen3.5:27b")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个乐于助人的助手。"},
            {"role": "user", "content": "一句话解释幂等性"},
        ],
    )
    if resp.usage:
        print(resp.choices[0].message.content)
        print(resp.usage)
        print(
            f"模型：{model}，prompt_tokens:{resp.usage.prompt_tokens},completion_tokens:{resp.usage.completion_tokens},total_tokens:{resp.usage.total_tokens}"
        )
        if resp.usage.completion_tokens_details:  # noqa: SIM102
            if resp.usage.completion_tokens_details.reasoning_tokens:
                print(
                    f"思考消耗：{resp.usage.completion_tokens_details.reasoning_tokens}"
                )
    else:
        print("未返回usage")


if __name__ == "__main__":
    main()

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api>
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex03_switch_backend.py
# 幂等性是指一个操作无论重复执行多少次，其产生的最终效果都与只执行一次的效果完全相同。
# 模型：qwen3.5:27b，prompt_tokens:26,completion_tokens:1410,total_tokens:1436
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex03_switch_backend.py
# 幂等性是指同一操作执行一次或多次，产生的最终结果都相同。
# 模型：gpt-5.6-sol，prompt_tokens:26,completion_tokens:27,total_tokens:53
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api>
# qwen3.5:27b 的输出token消耗为1410，gpt-5.6-sol的消耗为27，相差52倍，这是由于thinking模型的thinking导致的，thinking 也是算输出
# 中转站也会损失部分官方api的响应字段，只能用总用量来对比差值
