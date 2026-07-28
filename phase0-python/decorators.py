"""进阶篇 4/7《装饰器与上下文管理器》· 动手任务 1 + 2

任务 1：实现 @log_call 装饰器，打印函数名、入参、返回值；
        再实现带参版 @log_call(level="DEBUG")。
        用两个不同签名的函数验证 *args/**kwargs 透传正确。

任务 2：实现 @retry(times, delay)：失败后 time.sleep(delay) 再重试，
        用一个 70% 概率抛异常的函数测试。

要求：@wraps 别忘；完成后 uv run decorators.py 和 uv run mypy decorators.py 都要过。
"""

from functools import wraps
import time


def log_call_basic(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print(fn.__name__)
        print(args)
        print(kwargs)
        result = fn(*args, **kwargs)
        print(f"result is {result}")
        return result

    return wrapper


def log_call(level: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            print(f"log_call {level}:{fn.__name__} log")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def log_call_dual_mode(fn=None, *, level="DEBUG"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"log_call_dual_mode {level}:{func.__name__} log")
            return func(*args, **kwargs)

        return wrapper

    if fn is None:
        return decorator
    return decorator(fn)


@log_call_basic
def func1():
    print("this is func1")


@log_call_basic
def func2(a, mykwarg):
    print("this is func2")


@log_call(level="INFO")
def info_func():
    print("this is info_func")


@log_call(level="DEBUG")
def debug_func():
    print("this is debug_func")


@log_call_dual_mode
def dual_func_none():
    print("this is func1")


@log_call_dual_mode(level="INFO")
def dual_func_info():
    print("this is info_func")


# @log_call_dual_mode("DEBUG")
# def dual_func_str():
#     print("this is debug_func")


# 直接传str的报错
# Traceback (most recent call last):
#   File "E:\workspace\AiStudy\phase0-python\decorators.py", line 108, in <module>
#     @log_call_dual_mode("DEBUG")
#      ^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "E:\workspace\AiStudy\phase0-python\decorators.py", line 71, in wrapper
#     print(f"log_call_dual_mode DEBUG:{fn.__name__} {level} log")
#                                       ^^^^^^^^^^^
# AttributeError: 'str' object has no attribute '__name__'. Did you mean: '__ne__'?


def retry(times: int, delay: int):  # 第一层：接收装饰器参数
    def decorator(fn):  # 第二层：接收被装饰函数
        @wraps(fn)
        def wrapper(*args, **kwargs):  # 第三层：实际执行
            start = time.perf_counter()
            for i in range(times):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    print(f"attempt {i + 1} failed: {e}")
                if i < times - 1:
                    time.sleep(delay)
            print(f"{fn.__name__} took {time.perf_counter() - start:.4f}s")
            raise RuntimeError(f"{fn.__name__} failed after {times} tries")

        return wrapper

    return decorator


@retry(times=3, delay=1)  # ≈ Spring Retry 的 @Retryable(maxAttempts = 3)
def flaky_api() -> str:
    import random

    if random.random() < 1.0:
        raise ConnectionError("timeout")
    return "ok"


def main():
    print(f"1:{func1()}")
    print(f"7:{func2(4, mykwarg='saa')}")
    print(f"2:{info_func()}")
    print(f"3:{debug_func()}")
    print(f"4:{flaky_api()}")
    print(f"5:{dual_func_none()}")
    print(f"6:{dual_func_info()}")


#     print(f"7:{dual_func_str()}")


if __name__ == "__main__":
    main()
