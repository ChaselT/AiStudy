"""进阶篇 5/7《async异步编程》· 动手任务 1

任务：实现 call_llm 模拟函数（async，内部 await asyncio.sleep 模拟网络耗时），
      分别用「逐个 await」和 asyncio.gather 跑 5 个调用，
      打印两种方式的总耗时对比。

预期：逐个 ≈ 5 倍单次耗时；gather ≈ 1 倍。跑出这个对比才算完成。
"""
