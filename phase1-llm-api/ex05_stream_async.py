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
import time
import typing
from functools import wraps

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.AsyncOpenAI(
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
async def fetch_url(client: openai.AsyncOpenAI, question: str, tag: str = "") -> None:

    stream = await client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[{"role": "user", "content": question}],
        stream=True,
    )
    async for chunk in stream:  # 注意是 async for
        delta = chunk.choices[0].delta.content
        if delta:
            print(f"[{tag}]{delta}", end="", flush=True)
    print()


async def main() -> None:
    async with client:
        start1 = time.perf_counter()
        await asyncio.gather(
            fetch_url(client, "用一句话介绍一下JAVA", "1"),
            fetch_url(client, "用一句话介绍一下Python", "2]"),
            fetch_url(client, "用一句话介绍一下JavaScript", "3"),
        )
        print(f"Concurrent version took {time.perf_counter() - start1:.4f}s")
        start2 = time.perf_counter()
        await fetch_url(client, "用一句话介绍一下JAVA", "1")
        await fetch_url(client, "用一句话介绍一下Python", "2")
        await fetch_url(client, "用一句话介绍一下JavaScript", "3")
        print(f"Sequential version took {time.perf_counter() - start2:.4f}s")


asyncio.run(main())

# [[1]]Java[[2]]Python[[3]]JavaScript[[1]]是一种[[2]]是一种[[3]] 是[[1]]广泛[[2]]高级[[3]]一种[[1]]使用的[[2]]编程[[3]]主要用于[[1]]编程[[2]]语言[[3]]实现[[1]]语言[[2]]，[[3]]网页[[1]]，[[2]]由[[3]]交互[[1]]具有[[2]]Free[[3]]的[[1]]灵活性[[2]] Software[[3]]脚[[1]]和[[2]] Foundation[[3]]本[[1]]安全性[[2]]的[[3]]语言[[1]]，[[2]]Guid[[3]]，[[1]]适用于[[2]]o[[3]]使[[1]]各种[[2]] van[[3]]程序[[1]]应用程序[[2]] Ros[[3]]与[[1]]开发[[2]]sum[[3]] Web[[1]]。[[2]]于[[3]] 页面
# fetch_url took 0.8675s
# [[2]]1[[3]]无缝[[2]]9[[3]]集成[[2]]8[[3]]。[[2]]9[[3]]它可以[[2]]年[[3]]用于[[2]]提出[[3]]处理[[2]]并[[3]]用户[[2]]广泛[[3]]输入[[2]]使用[[3]]、[[2]]。[[3]]动画[[2]]Python[[3]]效果[[2]]以其[[3]]、[[2]]简单[[3]]数据[[2]]、[[3]]交换[[2]]易[[3]]和[[2]]学[[3]]网络[[2]]和[[3]]浏览[[2]]直观[[3]]等多种[[2]]的特点[[3]]场景[[2]]而[[3]]。[[2]]广[[3]]此外[[2]]受欢迎[[3]]，[[2]]，在[[3]]JavaScript[[2]]软件[[2]]开发[[3]] 还[[2]]、[[3]]具有[[2]]科学[[3]]访问[[2]]计算[[3]]局部[[2]]等领域[[3]]数据[[2]]具有[[3]]和[[2]]广泛的[[3]]影响[[2]]用途[[3]]全局[[2]]。[[3]]状态[[2]]它的[[3]]的能力[[2]]语法[[3]]。[[2]]结构[[3]]通过[[2]]是[[3]] JavaScript[[2]]面向[[2]]对象[[3]] 编[[2]]设计[[3]]写的[[2]]的语言[[3]]代码[[2]]，[[3]]可以[[2]]拥有[[3]]为[[2]]丰富的[[3]] Web[[2]]生态系统[[2]]支持[[3]] 应[[2]]各种[[3]]用[[2]]应用程序[[3]]开发[[2]]开发[[3]]提供[[2]]。[[3]]许多[[2]]Python[[3]]灵活性[[2]]凭借[[3]]和[[2]]其[[3]]扩展[[2]]动态[[3]]性[[2]]执行[[3]]。[[2]]的数据
# fetch_url took 1.3114s
# [[2]]类型[[2]]以及[[2]]强大的[[2]]交互[[2]]性[[2]]吸引了[[2]]大量的[[2]]开发者[[2]]和技术[[2]]爱好者[[2]]。
# fetch_url took 1.3543s
# Concurrent version took 1.6018s
# [[1]]JAVA[[1]]是一种[[1]]广泛[[1]]用于[[1]]各种[[1]]应用程序[[1]]开发[[1]]的[[1]]编程[[1]]语言[[1]]，[[1]]具有[[1]]强大的[[1]]跨[[1]]平台[[1]]性和[[1]]动态[[1]]性能[[1]]。[[1]]它是[[1]]Java[[1]]技术[[1]]系列[[1]]的一个[[1]]分支[[1]]，并[[1]]且[[1]]它[[1]]被[[1]]广泛应用[[1]]在[[1]]软件[[1]]开发[[1]]、[[1]]Web[[1]]应用[[1]]系统[[1]]、[[1]]操作系统[[1]]等领域[[1]]。[[1]]JAVA[[1]]的主要[[1]]目标[[1]]是[[1]]创造[[1]]一个[[1]]基于[[1]]对象[[1]]和[[1]]泛[[1]]型[[1]]的[[1]]环境[[1]]，[[1]]方便[[1]]开发者[[1]]与[[1]]程序[[1]]结构[[1]]化[[1]]地[[1]]组织[[1]]代码[[1]]，并[[1]]使[[1]]程序[[1]]更加[[1]]易于[[1]]维护[[1]]。[[1]]JAVA[[1]]语言[[1]]本身[[1]]是一个[[1]]标准[[1]]规范[[1]]，[[1]]适用于[[1]]Windows[[1]]和[[1]]Unix[[1]]等[[1]]不同[[1]]平台上[[1]]运行[[1]]的[[1]]Java[[1]]应用程序[[1]]。
# fetch_url took 0.7222s
# [[2]]Python[[2]] 是[[2]]一种[[2]]动态[[2]]语言[[2]]，[[2]]以其[[2]]简洁[[2]]性和[[2]]易[[2]]读[[2]]性强[[2]]而[[2]]闻名[[2]]于[[2]]世[[2]]。[[2]]它[[2]]通过[[2]]严格的[[2]]语法[[2]]和[[2]]丰富的[[2]]库[[2]]功能[[2]]使[[2]]编程[[2]]更[[2]]加快[[2]]速[[2]]、[[2]]简单[[2]]和[[2]]易于[[2]]维护[[2]]。[[2]]无论是[[2]]数据分析[[2]]、[[2]]科学[[2]]计算[[2]]还是[[2]]人工智能[[2]]开发[[2]]，[[2]]Python[[2]] 都[[2]]是[[2]]不错[[2]]的选择[[2]]。
# fetch_url took 0.6005s
# [[3]]JavaScript[[3]]是[[3]]基于[[3]] ECM[[3]]AS[[3]]cript[[3]]（[[3]]EC[[3]]MAS[[3]]cript[[3]]）[[3]]规范[[3]]的[[3]]脚[[3]]本[[3]]编程[[3]]语言[[3]]，[[3]]用于[[3]]在[[3]]Web[[3]]应用[[3]]中[[3]]实现[[3]]交互[[3]]性[[3]]。[[3]]它[[3]]具有[[3]]响应[[3]]性[[3]]、[[3]]跨[[3]]平台[[3]]和[[3]]高效[[3]]的特点[[3]]，[[3]]广泛[[3]]应用于[[3]]网页[[3]]开发[[3]]、[[3]]服务器[[3]]端[[3]]渲染[[3]]等[[3]]场景[[3]]。[[3]]随着[[3]]技术[[3]]的进步[[3]]，[[3]]JavaScript[[3]]逐渐[[3]]代替[[3]]了[[3]]ASP[[3]].NET[[3]]等[[3]]框架[[3]]成为[[3]]后[[3]]端[[3]]开发[[3]]的核心[[3]]工具[[3]]之一[[3]]。
# fetch_url took 0.6476s
# Sequential version took 1.9705s

# asyncio.gather 会比串行跑 3 次快很多，前者总耗时 1.6018s，后者总耗时 1.9705s
# 三个问题的输出是交错到达的，说明它们是并发执行的
# 本地单卡推理的并发收益有限——省下的只是排队和网络往返，算力总量没变。而云端 API 的并发收益会大得多，因为服务端有大量 GPU 在跑，你的三个请求是真的落在不同卡上。
