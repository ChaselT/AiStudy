"""阶段 1 · 《采样参数详解》· 动手任务 2

任务：制造并检测截断。
1. 问一个需要长回答的问题（如"详细讲讲 JVM 垃圾回收"）
2. 故意把 `max_tokens` 设得很小（如 30），让回答被硬生生截断
3. 检测 `resp.choices[0].finish_reason == "length"`，命中时打印醒目告警
4. 对比：把 max_tokens 调大后 finish_reason 变成什么

要求/提示：
- `finish_reason` 的常见取值都记进注释（stop / length / tool_calls / content_filter）
- 这是生产代码里必查的字段——用户看到半截话时你得知道是被截断了还是模型自己说完了
- 完成标准：两次运行分别打出 length 和 stop，告警逻辑生效
"""

import logging
import os

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=300.0,
    max_retries=3,  # 换 base_url 即换供应商
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": "你是一个乐于助人的助手。",
            },
            {
                "role": "user",
                "content": "介绍一下 JVM 的垃圾回收机制",
            },
        ],
        max_tokens=30000,
    )
    if resp.choices:
        match resp.choices[0].finish_reason:
            case "stop":
                if resp.choices[0].message.refusal:
                    logger.info("模型拒绝回答（如敏感内容）")
                else:
                    logger.info("回答完成。")
            case "length":
                logger.warning("警告：回答被截断！")
            case "tool_calls":
                logger.info("模型调用了工具（如 code interpreter / function call）")
            case "content_filter":
                logger.info("内容被平台安全策略拦截")
            case _:
                logger.error("未知 finish_reason：%s", resp.choices[0].finish_reason)
        logger.info("finish_reason: %s", resp.choices[0].finish_reason)


if __name__ == "__main__":
    main()

# max_tokens=30 时，finish_reason=length，回答被截断
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex04_finish_reason.py
# Java虚拟机（JVM）在执行程序时，会不断地生成和消耗对象（如类、接口、字段等）。为了减轻这些
# 警告：回答被截断！

# max_tokens=30000 时，finish_reason=stop，回答完整
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex04_finish_reason.py
# `Java虚拟机(简称JVM)是运行在不同平台上的应用软件的一个重要组成部分，对整个计算机系统具有关键性的影响`

# **1. 账本管理**: JVM 将程序所占用的内存进行一次大的物理化转换，该过程称为虚拟化（virtualization），最终产生一个虚拟机器，并把这个虚拟机分配给客户程序。这样就实现了进程间的共享内存。

# `这段运行时需要消耗大量的系统资源如CPU、内存、以及磁盘空间等`

# 2. `Garbage Collection (垃圾回收)`: JRE内嵌的GC库负责内存的清理工作，通过自动分配和回收垃圾回收。

# **1）自动对象释放**: 无论类的大小如何，Java编译器都会将其转换成字节码，并用相应的机制将该字节码加载到JVM中。如果在不使用这个编译后的字节代码的时候再访问该字节码，则会抛出异常。因此，在开发阶段应该避免通过任何方式获取对象的引用；另外，Java Virtual Machine（JVM）会对需要存储或被需要的临时对象自动进行回收，并按一定的规则清理垃圾。

# * **Java中对象的一些属性**：
#   - 头部: 类和包名、类名、类型;
#   - 表格头部; 数据源;
#   - 内容字段: 实际值、元数据（如序列号）等;

# - 空闲区`ObjectPool`

# 2. 家庭线：当程序运行在多个CPU的虚拟机上,每个 CPU 则需要一个独立的虚拟垃圾回收器去完成垃圾收集任务。
# 3. 当前有多个GC线程时，JVM会根据内存泄漏问题的不同选择并开启不同的GC处理器；
# 4. 有些代码可以在`final`、`public`或`static`上，而其他在`abstract`和`private`中。这是由于Java的继承特性带来的。

# * "jvm" (垃圾回收) 运行时, 程序执行部分:

# 当应用程序运行到一定时间(一般为10秒、500毫秒等), JVM 将产生一个特殊的标志 `SIGINT`(系统调用中断): JVM 会触发这个异常（因为用户没有按键盘按键）。然后JVM在收到这个 `SIGINT` 并确认该程序正处于运行状态之前将继续执行它。当运行的应用程序的计数器达到最大值或达到指定值时,JVM会立即发送一个信号 (SIGHUP), 命令主线程跳出当前进程并继续执行下一个进程。这时JVM会被停止处理，直到新的 `SIGINT` 异常产生为止, JVM 的垃圾回收将会开始。
# 6. 由于Java的所有类都必须包含了public访问成员（如main、equals、toString等）所以所有Java源代码都被视为公共代码，因此JVM会为所有的公有字段和变量分配内存，当这个过程完成之后再分发给一个子进程。当程序在运行过程中产生大量的临时文件且需要频繁对它们进行销毁后, Java编译器也会自动将这些生成的文件转换为字节码并添加到JVM中。

# * "GC"：垃圾回收是指从堆中的内存数据中移除不再使用的对象（通常是临时对象或不需要的对象）的过程，目的是提高运行效率和内存使用率。
#   **主要分为两大类: 1. 不管是Java虚拟机还是多线程的虚拟机，都可以设置自己的GC优先级以控制GC的时间和频率。** 在Java中，通过java -XX:+UseG1GC设置自动垃圾回收器为G1算法。

#   - 这种垃圾回收机制在性能上比标准的JGRT稍好一点。
#   - 但是由于需要专门知道如何设置环境变量才可取到良好效果，也存在依赖于编译的缺点：因为这些设定和参数可能会随程序改动。而大部分开发人员都还没有掌握这种特性。
# finish_reason: stop

# 虽然是stop，但回答的内容完全是胡编乱造，幻觉严重。

# 常见的 finish_reason 取值：
# - stop：模型自己说完了
# - length：回答被截断了（max_tokens 不够）
# - tool_calls：模型调用了工具（如 code interpreter / function call）
# - content_filter：模型拒绝回答（如敏感内容）
