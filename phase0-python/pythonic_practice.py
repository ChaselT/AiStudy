"""进阶篇 6/7《常用标准库与生态》· 动手任务 1

给定 words = ["Apple", "banana", "Cherry", "date"]，用推导式完成：
  (a) 取长度 >4 的词并转小写
  (b) 生成 {词: 长度} 的 dict（dict 推导式）
  (c) 用 enumerate 打印带序号清单

要求：每题在注释里写出等价的 Java Stream 写法（你最熟的主场，对照着写印象最深）。
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

words = ["Apple", "banana", "Cherry", "date"]


def main():
    long_words = [w.lower() for w in words if len(w) > 4]
    # List<String> result = words.stream().filter(w -> w.length() > 4).map(String::toLowerCase).collect(Collectors.toList());
    logger.info("(a)取长度 >4 的词并转小写: %r", long_words)
    length_dict = {w: len(w) for w in words}
    # Map<String, Integer> result = words.stream().collect(Collectors.toMap(w -> w,String::length));
    logger.info("(b) 生成 词: 长度 的 dict（dict 推导式）:%r", length_dict)
    for i, w in enumerate(words, start=1):
        print(f"{i}. {w}")
    # 普通for 写法：for(i=1;i<words.size();i++){System.out.print((i) + ". " + words.get(i-1) + " ");}
    # lambda：IntStream.range(0, words.size()).forEach(i -> System.out.print((i + 1) + ". " + words.get(i) + " "));


if __name__ == "__main__":
    main()
