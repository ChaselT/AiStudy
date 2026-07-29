"""进阶篇 5/7《async异步编程》· 动手任务 1

任务：实现 call_llm 模拟函数（async，内部 await asyncio.sleep 模拟网络耗时），
      分别用「逐个 await」和 asyncio.gather 跑 5 个调用，
      打印两种方式的总耗时对比。

预期：逐个 ≈ 5 倍单次耗时；gather ≈ 1 倍。跑出这个对比才算完成。
"""

import asyncio
import time


async def call_llm(prompt: str, times: int):
    await asyncio.sleep(1)
    return f"{prompt}的第{times}次调用"


async def main() -> None:
    start = time.perf_counter()
    for i in range(1, 6):
        result = await call_llm("aaa", i)
        print(result)
    print(f"逐个 await took {time.perf_counter() - start:.4f}s")
    start2 = time.perf_counter()
    answers = await asyncio.gather(
        call_llm("bbb", 1),
        call_llm("ccc", 2),
        call_llm("ddd", 3),
        call_llm("eee", 4),
        call_llm("fff", 5),
    )
    print(answers)
    print(f"asyncio.gather took {time.perf_counter() - start2:.4f}s")


if __name__ == "__main__":
    asyncio.run(main())
