"""进阶篇 5/7《async异步编程》· 动手任务 2

任务：用 httpx.AsyncClient + gather 并发请求 3 个真实 URL，
      打印每个的状态码与耗时；
      再故意把其中一个换成同步阻塞调用（requests.get 或 time.sleep(3)），
      观察整体耗时如何劣化，并在下方注释里解释原因。

提示：本机有 SOCKS 代理，httpx[socks] 已装；参考第一天跑通的 hello_async.py。

任务 3（不建文件）：回到《Python与Java核心差异》动手任务 3，
      修订你对「为什么用 asyncio 而不是多线程」的回答（写到 notes 或答给 Claude）。
"""
