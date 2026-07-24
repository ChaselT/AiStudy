"""环境验证脚本：类型注解 + async 并发请求。

运行方式（在 phase0-python 目录下）：
    uv run hello_async.py

对 Java 工程师的说明：
- async def ≈ 返回 CompletableFuture 的方法，但由事件循环调度（单线程并发）
- asyncio.gather ≈ CompletableFuture.allOf，并发等待多个任务
- httpx.AsyncClient ≈ 异步版的 OkHttp/RestTemplate
"""

import asyncio
import time

import httpx


async def fetch_status(client: httpx.AsyncClient, url: str) -> tuple[str, int]:
    """请求一个 URL，返回 (url, 状态码)。"""
    resp = await client.get(url, follow_redirects=True, timeout=10)
    return url, resp.status_code


async def main() -> None:
    urls: list[str] = [
        "https://www.python.org",
        "https://pypi.org",
        "https://github.com",
    ]
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:  # 类比 try-with-resources
        results = await asyncio.gather(*(fetch_status(client, u) for u in urls))
    elapsed = time.perf_counter() - start

    for url, status in results:
        print(f"{status}  {url}")
    print(f"\n3 个请求并发完成，总耗时 {elapsed:.2f}s（串行会是三倍左右）")
    print("环境验证通过：uv + Python 3.11 + 类型注解 + async 全部正常")


if __name__ == "__main__":
    asyncio.run(main())
