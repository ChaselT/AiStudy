"""进阶篇 4/7《装饰器与上下文管理器》· 动手任务 3

任务：用 @contextmanager 实现 cd(path)——
      进入 with 块时切换工作目录，退出时无论是否异常都切回原目录。
      （用 os.getcwd() / os.chdir()；"无论是否异常"提示你 try/finally 放哪）

要求：写一段测试代码验证正常路径和 with 块内抛异常两种情况，退出后都回到原目录。
"""

from contextlib import contextmanager
import os


@contextmanager
def cd(path):
    old_path = os.getcwd()
    os.chdir(path)
    print(f"into {path}")
    try:
        yield
    finally:
        os.chdir(old_path)
        print(f"final into {old_path}")


def main():
    with cd("basics"):
        print(f"1: path to {os.getcwd()}")
    try:
        with cd("aaa"):
            print(f"2: path to {os.getcwd()}")
    except Exception as e:
        print(e)
        pass
    print(os.getcwd())
    try:
        with cd("basics"):
            print(f"3: {os.getcwd()}")  # 证明已经真的切过去了
            raise RuntimeError("干活干到一半炸了")
    except RuntimeError as e:
        print(e)
        pass

    print(os.getcwd())


if __name__ == "__main__":
    main()
