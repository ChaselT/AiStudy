"""阶段 1 · 《流式输出与SSE》· 动手任务 1

任务：流式输出 + 延迟测量。
1. 用 `stream=True` 流式打印回答，做到终端里逐字（逐 chunk）蹦出来
2. 用 `time.perf_counter()` 统计两个指标：
   - TTFT（首个 chunk 到达的延迟）
   - 总耗时
3. 同一个问题再用**非流式**跑一次，对比两者的 TTFT 和总耗时，结论写注释

要求/提示：
- 逐字打印要注意 `print` 的 `end=""` 与 flush，否则看不到流式效果（缓冲问题）
- 注意 chunk 里 delta.content 可能是 None，别直接拼接
- 完成标准：能看到明显的逐字输出；能解释"为什么总耗时差不多，但流式体感快得多"
"""

import asyncio
import os
import time
import typing
from functools import wraps

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

client = AsyncOpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=300.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def timed(fn: typing.Callable) -> typing.Callable:
    @wraps(fn)  # 保留原函数的 __name__/__doc__，必写！
    async def wrapper(*args: typing.Any, **kwargs: typing.Any) -> None:
        start = time.perf_counter()
        result = await fn(*args, **kwargs)
        print(f"{fn.__name__} took {time.perf_counter() - start:.4f}s")
        return result

    return wrapper


@timed
async def streaming_request(question: str) -> None:
    start = time.perf_counter()
    stream = await client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[{"role": "user", "content": question}],
        stream=True,
        max_tokens=200,
        stream_options={"include_usage": True},
    )
    flag = True  # 用于标记首个 chunk 到达的延迟
    async for chunk in stream:  # 注意是 async for
        if chunk.usage:
            print(f"streaming_request usage: {chunk.usage}")
            continue
        if not chunk.choices[0]:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            if flag:
                flag = False
                print(
                    f" streaming_request TTFT: {time.perf_counter() - start:.4f}s"
                )  # 首个 chunk 到达的延迟
            print(delta, end="", flush=True)
    print()


@timed
async def streaming_no_print_request(question: str) -> None:
    start = time.perf_counter()
    stream = await client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[{"role": "user", "content": question}],
        stream=True,
        max_tokens=200,
        stream_options={"include_usage": True},
    )
    flag = True  # 用于标记首个 chunk 到达的延迟
    res = []
    async for chunk in stream:  # 注意是 async for
        if chunk.usage:
            print(f"streaming_no_print_request usage: {chunk.usage}")
            continue
        if not chunk.choices[0]:
            continue
        delta = chunk.choices[0].delta.content
        if delta and flag:
            flag = False
            print(
                f"streaming_no_print_request TTFT: {time.perf_counter() - start:.4f}s"
            )  # 首个 chunk 到达的延迟
            # print(delta, end="", flush=True)
            res.append(delta)


#  print()


@timed
async def non_streaming_request(question: str) -> None:
    start = time.perf_counter()
    response = await client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[{"role": "user", "content": question}],
        stream=False,
        max_tokens=200,
    )
    print(response.choices[0].message.content)
    print(f"non_streaming_request usage: {response.usage}")
    print(f"non_streaming_request TTFT took {time.perf_counter() - start:.4f}s")


async def main() -> None:
    await streaming_request("介绍一下SSE")
    await non_streaming_request("介绍一下SSE")
    await streaming_no_print_request("介绍一下SSE")


asyncio.run(main())

#  streaming_request TTFT: 0.6827s
# sse（Session Started）事件表示请求在向服务器发送之前，客户端已经和服务端建立了连接。这表明请求是在HTTP或者HTTPS会话层所发生的操作。

# 当 SSE 事件被触发时，浏览器的开发者工具通常会生成控制台的日志，这些日志记录了发生错误以及服务器或其他应用程序与SSE相关的任何其他信息。如果sse是用于异步通信（如WebSockets），则这个事件的状态可能以"ready-to-go"或"in-progress"表示。

# 此外，在某些编程语言和库中，你也可以通过SSE来发送数据。这通常意味着你需要一个服务器端的实现，在你的代码中调用函数以便从服务器读取数据，然后将其作为网页中的内容显示给用户。

# 尽管sse是一个有用的事件，但它并不能直接与WebSocket通信（在WebSocket的客户端部分，你可能需要更详细的解释）。如果你打算使用SSE和WebSocket来构建一套服务之间的交互模式，请先确保
# streaming_request usage: CompletionUsage(completion_tokens=200, prompt_tokens=32, total_tokens=232, completion_tokens_details=None, prompt_tokens_details=None)

# streaming_request took 1.4589s
# SSE（Streaming and Push）是数据流的推送技术，它强调通过实时的数据流提供静态页面的更新、事件订阅、自动缓存和分层渲染等效果。这种技术和方法在互联网和大数据领域有广泛的应用。

# SSE的主要特点是：

# 1. 高效性：通常比传统的HTTP GET请求速度快。
# 2. 实时：可以满足用户对实时数据的需求，如新闻、股市、体育比分、实时消息推送等。
# 3. 可视化：通过使用如DynamoDB、RDS和SQL等数据库技术的特性，它可以构建出清晰易懂的数据流状态图，帮助理解页面更新的历史和细节。

# SSE的主要实现方式有：

# 1. 使用WebSocket：这是一种在客户端和服务器之间实时传输文本消息的技术。
# 2. 使用Socket.io：这是一种低代码和低资源的方法，可以很容易地将JavaScript与Websocket集成。

# 然而，尽管SSE提供了一种高效、快速的数据
# non_streaming_request usage: CompletionUsage(completion_tokens=200, prompt_tokens=32, total_tokens=232, completion_tokens_details=None, prompt_tokens_details=None)
# non_streaming_request TTFT took 1.0122s
# non_streaming_request took 1.0123s
# streaming_no_print_request TTFT: 0.1309s
# streaming_no_print_request usage: CompletionUsage(completion_tokens=200, prompt_tokens=32, total_tokens=232, completion_tokens_details=None, prompt_tokens_details=None)
# streaming_no_print_request took 0.8019s
# 1. 流式本身几乎没有额外开销，甚至略快：B 0.80s vs C 1.01s（快 20%）。合理，因为流式不需要服务端把整个响应缓冲完再一次性发
# 2. 打印开销 = 1.4589 - 0.8019 = 0.657 秒，占流式打印版总耗时的 45%。而且TTFT 也被打印拖累：0.13s → 0.68s，慢了 5 倍
# 3. 非流式的 TTFT = 总耗时（1.0122 ≈ 1.0123，两个数字几乎相同）——这就是流式体感优势的全部来源：同样等 1 秒，一个是空屏干等，一个是 0.13 秒就开始出字
