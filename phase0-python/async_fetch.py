"""进阶篇 5/7《async异步编程》· 动手任务 2

任务：用 httpx.AsyncClient + gather 并发请求 3 个真实 URL，
      打印每个的状态码与耗时；
      再故意把其中一个换成同步阻塞调用（requests.get 或 time.sleep(3)），
      观察整体耗时如何劣化，并在下方注释里解释原因。

提示：本机有 SOCKS 代理，httpx[socks] 已装；参考第一天跑通的 hello_async.py。

任务 3（不建文件）：回到《Python与Java核心差异》动手任务 3，
      修订你对「为什么用 asyncio 而不是多线程」的回答（写到 notes 或答给 Claude）。
"""

import asyncio
import time
import httpx


async def fetch_url(client: httpx.AsyncClient, url: str, duration: int | None):
    if duration is not None:
        time.sleep(duration)
        print(f"{url} sleep {duration} s")
    start = time.perf_counter()
    result = await client.get(url)

    print(f"{url}:took {time.perf_counter() - start:.4f}s ")
    print(f"{url}:result is {result} ")
    print(f"{url}: code is {result.status_code}")
    return result


async def main() -> None:
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=200) as client:
        answers = await asyncio.gather(
            fetch_url(client, "http://baidu.com", 3),
            fetch_url(client, "https://www.hi-code.cc", None),
            fetch_url(client, "https://www.bejson.com/", None),
        )
    print(answers)

    print(f"took {time.perf_counter() - start:.4f}s ")


if __name__ == "__main__":
    asyncio.run(main())

# httpx.AsyncClient + gather 总耗时：
# http://baidu.com:took 0.1243s
# http://baidu.com:result is <Response [301 Moved Permanently]>
# http://baidu.com: code is 301
# https://www.bejson.com/:took 0.1564s
# https://www.bejson.com/:result is <Response [200 OK]>
# https://www.bejson.com/: code is 200
# https://www.hi-code.cc:took 0.8734s
# https://www.hi-code.cc:result is <Response [200 OK]>
# https://www.hi-code.cc: code is 200
# [<Response [301 Moved Permanently]>, <Response [200 OK]>, <Response [200 OK]>]
# took 0.9481s

# 其中一个await asyncio.sleep(3)
# PS E:\workspace\AiStudy\phase0-python> uv run .\async_fetch.py
# https://www.bejson.com/:took 0.2768s
# https://www.bejson.com/:result is <Response [200 OK]>
# https://www.bejson.com/: code is 200
# https://www.hi-code.cc:took 1.5040s
# https://www.hi-code.cc:result is <Response [200 OK]>
# https://www.hi-code.cc: code is 200
# http://baidu.com sleep 3 s
# http://baidu.com:took 0.1366s
# http://baidu.com:result is <Response [301 Moved Permanently]>
# http://baidu.com: code is 301
# [<Response [301 Moved Permanently]>, <Response [200 OK]>, <Response [200 OK]>]
# took 3.1963s

# time.sleep(3)
# PS E:\workspace\AiStudy\phase0-python> uv run .\async_fetch.py
# http://baidu.com sleep 3 s
# http://baidu.com:took 0.2001s
# http://baidu.com:result is <Response [301 Moved Permanently]>
# http://baidu.com: code is 301
# https://www.bejson.com/:took 0.2487s
# https://www.bejson.com/:result is <Response [200 OK]>
# https://www.bejson.com/: code is 200
# https://www.hi-code.cc:took 1.2804s
# https://www.hi-code.cc:result is <Response [200 OK]>
# https://www.hi-code.cc: code is 200
# [<Response [301 Moved Permanently]>, <Response [200 OK]>, <Response [200 OK]>]
# took 4.3564s

# 经过多次观察，如果某个url的耗时超过了sleep的这个请求的耗时，则没影响，使用time.sleep 则是所有的都会等这个sleep结束，

# asyncio 适合“同时等待很多事情”，多线程适合“同时运行很多阻塞式调用”, 异步请求，大部分时间在等网络响应，所以使用asyncio更合适
