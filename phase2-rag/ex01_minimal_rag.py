"""阶段 2 · 《RAG全景与选型》· 动手任务

任务：跑通最小 RAG，建立整体感。
1. 把笔记里那段 30 行最小 RAG 跑通
   （embedding 先用 bge-m3：`ollama pull bge-m3`，选型下一课再讲）
2. 自己造 8~10 条知识库句子——用你熟悉的领域，方便判断对错
3. 设计 5 个问题，其中**至少 2 个是故意让它答不出来的**（知识库里没有），
   观察拒答约束生效没有
4. 把 k 从 1 调到 5，观察回答质量变化，记录发现

要求/提示：
- 这一课不用向量库，numpy 手算余弦相似度就够——目的是看清骨架
- 拒答那两条很重要：RAG 最危险的失败不是"答不出"，是"编一个"
  （回顾 [[错题与复盘#E32]]：幻觉会藏在可信回答的细节里）
- k 调大调小各有什么问题？想清楚再写结论，别只写"k=3 效果好"

完成标准：
- 能跑通；有一个"知识库里没有 → 正确拒答"的完整日志
- 注释里回答「k 太小和太大分别有什么问题」
"""

"""最小 RAG：无向量库、无分块策略，只为看清骨架。"""

import numpy as np
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# ① 假装这是切好的知识库
CHUNKS = [
    "Java基础类型：包括byte、short、int、long、float、double、char和boolean，不同类型占用的内存空间和取值范围不同。",
    "面向对象三大特性：封装用于隐藏实现细节，继承用于复用代码，多态允许同一接口表现出不同的实现行为。",
    "字符串比较：String对象的内容比较应使用equals方法，双等号只用于判断两个引用是否指向同一个对象。",
    "集合框架：List允许元素重复且有序，Set不允许元素重复，Map以键值对形式存储数据且键不能重复。",
    "异常处理：可以使用try、catch和finally捕获并处理异常，也可以通过throws将异常交给上层调用者处理。",
    "泛型机制：泛型可以在编译阶段约束数据类型，减少强制类型转换，并降低运行时出现类型错误的风险。",
    "线程创建：可以通过继承Thread类、实现Runnable接口或使用线程池执行任务，实际开发中通常优先使用线程池。",
    "JVM内存区域：堆用于存储对象实例，虚拟机栈用于存储方法调用信息，方法区用于存储类结构和静态变量等数据。",
    "垃圾回收机制：JVM会自动识别并回收不再被引用的对象，但开发者不能准确控制垃圾回收发生的具体时间。",
    "Stream流：Java 8提供Stream API，可通过filter、map、sorted和collect等操作对集合数据进行声明式处理。",
]


def embed(texts: list[str]) -> np.ndarray:
    """② 把文本变成向量（第 2、3 课细讲）"""
    resp = client.embeddings.create(model="bge-m3", input=texts)
    return np.array([d.embedding for d in resp.data])


def retrieve(question: str, k: int = 2) -> list[str]:
    """③ 检索：算余弦相似度，取最像的 k 个"""
    doc_vecs = embed(CHUNKS)
    q_vec = embed([question])[0]
    # 归一化后点积 = 余弦相似度
    sims = doc_vecs @ q_vec / (np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(q_vec))
    result_list = [CHUNKS[i] for i in np.argsort(sims)[::-1][:k]]
    print(result_list)
    return result_list


def ask(question: str) -> str | None:
    """④ 把检索结果拼进 prompt，让模型带着资料回答"""
    context = "\n".join(f"- {c}" for c in retrieve(question))
    resp = client.chat.completions.create(
        model="qwen3.5:27b",
        messages=[
            {
                "role": "system",
                "content": "只根据【参考资料】回答；资料里没有就说'知识库中未找到'，不许编。",
            },
            {
                "role": "user",
                "content": f"【参考资料】\n{context}\n\n【问题】{question}",
            },
        ],
        temperature=0,
    )
    return resp.choices[0].message.content


print(ask("Java 里有哪些方式创建线程，它们分别属于什么机制"))
# print(ask("List、Set和Map分别有什么特点？"))
# print(ask("Java中有哪些创建和执行线程的方式？"))
# print(ask("Java反射机制的主要用途是什么？"))
# print(ask("Spring Boot中的依赖注入是如何实现的？"))


# 跑通：
# PS E:\\workspace\\AiStudy\\phase2-rag> uv run .\\ex01_minimal_rag.py
# 能，根据年假规则，当年未休完可顺延至次年 3 月。

# 10CHUNKS 5 问题 3内2外
# (phase2-rag) PS E:\\workspace\\AiStudy\\phase2-rag> uv run .\\ex01_minimal_rag.py
# 根据参考资料，String 对象的内容比较应使用 equals 方法，双等号只用于判断两个引用是否指向同一个对象。
# 根据【参考资料】，List、Set 和 Map 的特点如下：

# - **List**：允许元素重复且有序。
# - **Set**：不允许元素重复。
# - **Map**：以键值对形式存储数据且键不能重复。
# 根据参考资料，Java 中创建和执行线程的方式包括：
# 1. 继承 Thread 类
# 2. 实现 Runnable 接口
# 3. 使用线程池执行任务
# 知识库中未找到
# 知识库中未找到

# k=1
# 根据参考资料，因为双等号只用于判断两个引用是否指向同一个对象，所以 String 对象的内容比较应使用 equals 方法。
# k=2
# 根据参考资料，String 对象的内容比较应使用 equals 方法，双等号只用于判断两个引用是否指向同一个对象。
# k=3
# 根据参考资料，String 对象的内容比较应使用 equals 方法，因为双等号只用于判断两个引用是否指向同一个对象。
# k=4
# 根据参考资料，String 对象的内容比较应使用 equals 方法，双等号只用于判断两个引用是否指向同一个对象。
# k=5
# 根据参考资料，String 对象的内容比较应使用 equals 方法，双等号只用于判断两个引用是否指向同一个对象。

# 问题：Java 里有哪些方式创建线程，它们分别属于什么机制
# k=1
# 根据【参考资料】，Java 里创建线程的方式有：
# - 继承Thread类
# - 实现Runnable接口
# - 使用线程池执行任务

# 参考资料中未提及这些方式分别属于什么机制，因此关于“它们分别属于什么机制”的信息，知识库中未找到。
# k=2
# ['线程创建：可以通过继承Thread类、实现Runnable接口或使用线程池执行任务，实际开发中通常优先使用线程池。', 'Stream流：Java 8提供Stream API，可通过filter、map、sorted和collect等操作对集合数据进行声明式处理。']
# 根据参考资料，Java 创建线程的方式有：继承Thread类、实现Runnable接口或使用线程池执行任务。关于它们分别属于什么机制，知识库中未找到。
# k=3
# 根据【参考资料】，Java创建线程的方式有以下三种：

# 1. 继承Thread类
# 2. 实现Runnable接口
# 3. 使用线程池执行任务

# 参考资料中提到"实际开发中通常优先使用线程池"，但未明确说明这些方式分别属于什么具体机制。参考资料仅列出了创建线程的三种方式，未对它们的机制进行详细分类。
# k=4
# 根据参考资料，线程创建可以通过继承Thread类、实现Runnable接口或使用线程池执行任务。关于它们分别属于什么机制，知识库中未找到。
# k=5
# 根据参考资料，Java 创建线程的方式可以通过继承Thread类、实现Runnable接口或使用线程池执行任务。关于它们分别属于什么机制，知识库中未找到。


# 结论：
# 实际结果：本次 k 无显著影响 ，没能复现出来预期的问题
# 预期结果：k太小，可能会导致需要的资料不全，导致无法回答，K太大，会传入多余的信息，占用大量上下文，导致成本升高
# 同参数两次运行，一次编造一次拒答。编造概率与k值无关，随机出现，
