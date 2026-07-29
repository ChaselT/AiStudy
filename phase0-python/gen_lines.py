"""进阶篇 6/7《常用标准库与生态》· 动手任务 3

任务：写一个生成器函数，逐行读取任意文本文件并过滤空行，
      用它统计本项目某个 .py 文件的非空行数。

提示：生成器 = 用 yield 的函数（"边循环边收集"的懒加载版）；
      这是大文件处理的标准姿势——不把整个文件读进内存。
"""

from collections.abc import Iterator


def read_large(path: str) -> Iterator[str]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


def main():
    read_result = read_large("./fetch_and_save.py")
    num = 0

    for line in read_result:
        print(line)
        num += 1
    print(f"该文件一共：{num} 行")
    count = sum(1 for _ in read_large("./fetch_and_save.py"))
    print(f"count该文件一共：{count} 行")


if __name__ == "__main__":
    main()
