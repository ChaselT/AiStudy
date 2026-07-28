"""进阶篇 4/7《装饰器与上下文管理器》· 动手任务 1 + 2

任务 1：实现 @log_call 装饰器，打印函数名、入参、返回值；
        再实现带参版 @log_call(level="DEBUG")。
        用两个不同签名的函数验证 *args/**kwargs 透传正确。

任务 2：实现 @retry(times, delay)：失败后 time.sleep(delay) 再重试，
        用一个 70% 概率抛异常的函数测试。

要求：@wraps 别忘；完成后 uv run decorators.py 和 uv run mypy decorators.py 都要过。
"""
