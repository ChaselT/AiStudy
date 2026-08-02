"""阶段 1 · 《流式输出与SSE》· 动手任务 3

任务：异步并发流式请求。
1. 用 `AsyncOpenAI` 客户端 + `asyncio.gather` 同时向本地 Ollama 发 3 个流式请求
2. 三个问题各不相同，观察它们的输出是**交错**到达的
3. 对比串行跑 3 次的总耗时，体会异步并发的收益

要求/提示：
- 前置知识回顾阶段 0 的 async 课：`await` 让路而不是堵路，
  `gather` 类比 Java 的 `CompletableFuture.allOf`
- 交错输出会让终端很乱，可以给每个任务加前缀标记（如 `[1]` `[2]`）
- 本地 Ollama 默认并发数有限，如果看起来像串行，去查 `OLLAMA_NUM_PARALLEL`
- 完成标准：并发版总耗时明显小于串行版，注释里记下两组秒数
"""

import asyncio
import os

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.AsyncOpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=300.0,
    max_retries=3,  # 换 base_url 即换供应商
)


async def fetch_url(client, question: str, delay: int | None) -> None:
    """异步并发请求 URL，支持延迟"""
    if delay:
        await asyncio.sleep(delay)
    stream = await client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[{"role": "user", "content": question}],
        stream=True,
    )
    async for chunk in stream:  # 注意是 async for
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()


async def main() -> None:
    async with client:
        await asyncio.gather(
            fetch_url(client, "介绍一下JAVA", 3),
            fetch_url(client, "介绍一下Python", None),
            fetch_url(client, "介绍一下JavaScript", None),
        )


asyncio.run(main())
