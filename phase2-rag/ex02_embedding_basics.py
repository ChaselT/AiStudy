"""阶段 2 · 《Embedding原理与相似度》· 动手任务

任务：把"语义相似度"从概念变成能看的数字。
1. 用 bge-m3 把 10 个句子向量化，打印维度，确认同样输入得到同样输出（幂等性）
2. 自己实现 cosine()，算出 **10×10 的相似度矩阵**并打印
   - 句子要精心设计：2~3 组近义句 + 几个完全不相关的
   - 检查对角线是不是 1.0
3. 验证「归一化后点积 == 余弦相似度」，用 np.allclose 断言
4. **标定实验**：设计 5 个相关对 + 5 个不相关对，列出各自分数，回答：
   你的数据上阈值该画在哪？**相关对的最低分和不相关对的最高分有没有重叠？**
5. 试试加/不加检索前缀（非对称检索），对比同一组查询的分数变化

要求/提示：
- 相似度矩阵建议格式化成表格打印，行列都标上句子编号，肉眼才看得出规律
- 第 4 题的"重叠"是重点：**如果有重叠，说明单靠阈值分不开好坏**——
  这正是后面要学 rerank 的原因。没重叠反而说明你的测试样本区分度太高，不真实
- bge 系列的检索前缀写法查官方文档，别猜。写错不会报错，只会悄悄掉点（E36 场景）

完成标准：
- 相似度矩阵能打印出来；np.allclose 断言通过
- 注释里有你标定出的阈值 + **重叠情况的说明**
"""

import numpy as np
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

SENTENCES = [
    # 0-2：一组近义句，说的是Java字符串内容比较
    "Java字符串比较：判断两个String对象的内容是否相同，应使用equals方法。",
    "String内容判断：在Java中比较字符串的实际内容，需要调用equals方法。",
    "字符串相等判断：equals用于比较String的内容，双等号只比较对象引用。",
    # 3-4：另一组近义句，说的是Java线程创建
    "Java线程创建：可以继承Thread类、实现Runnable接口或使用线程池执行任务。",
    "多线程任务：Java可以通过Thread、Runnable以及线程池等方式运行并发任务。",
    # 5-9：互不相关，横跨不同领域
    "地理知识：中国的首都是北京，北京位于华北地区。",
    "生物知识：植物通过光合作用吸收二氧化碳，并释放氧气。",
    "数学知识：圆的面积等于圆周率乘以半径的平方。",
    "经济知识：通货膨胀通常表现为物价持续上涨和货币购买力下降。",
    "天文知识：地球围绕太阳公转一周大约需要365天。",
]


def embed(texts: list[str]) -> np.ndarray:
    """② 把文本变成向量（第 2、3 课细讲）"""
    resp = client.embeddings.create(model="bge-m3", input=texts)
    return np.array([d.embedding for d in resp.data])


print(embed(SENTENCES).shape)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


vecs = embed(SENTENCES)

v0 = vecs[0]
v1 = vecs[1]
v5 = vecs[5]
print(cosine(v0, v0))
print(cosine(v0, v1))
print(cosine(v1, v0))
print(cosine(v1, v5))


n = len(SENTENCES)
sim = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        numerator = np.dot(vecs[i], vecs[j])
        denominator = np.linalg.norm(vecs[i]) * np.linalg.norm(vecs[j])

        # 防止向量长度为0时出现除零错误
        sim[i][j] = numerator / denominator if denominator != 0 else 0.0

print(np.round(sim, 3))
print(np.linalg.norm(vecs, axis=1))

sim2 = vecs @ vecs.T
print(np.round(sim2, 3))
print(np.allclose(sim, sim2))

usemy_pairs = [
    cosine(vecs[0], vecs[1]),
    cosine(vecs[0], vecs[2]),
    cosine(vecs[1], vecs[2]),
    cosine(vecs[3], vecs[4]),
    cosine(vecs[0], vecs[3]),
    cosine(vecs[0], vecs[4]),
    cosine(vecs[1], vecs[3]),
    cosine(vecs[1], vecs[4]),
    cosine(vecs[2], vecs[3]),
    cosine(vecs[2], vecs[4]),
]
not_pairs = [
    cosine(vecs[0], vecs[9]),
    cosine(vecs[1], vecs[8]),
    cosine(vecs[2], vecs[7]),
    cosine(vecs[5], vecs[9]),
    cosine(vecs[6], vecs[7]),
]

print(sorted(usemy_pairs, reverse=True))
print(sorted(not_pairs, reverse=True))

PREFIX = "为这个句子生成表示用于检索相关文章："

PRE_SENTENCES = [PREFIX + SENTENCES[0], PREFIX + SENTENCES[1], PREFIX + SENTENCES[3]]

vecs_pre = embed(PRE_SENTENCES)

# 0 和1
a = cosine(vecs[0], vecs[1])
b = cosine(vecs_pre[0], vecs[1])
print(f"0,1: {a}")
print(f"pre 0,1: {b}")
print(f"diff 0,1:{(a - b):0.3f}")

# 0 和 2
a = cosine(vecs[0], vecs[2])
b = cosine(vecs_pre[0], vecs[2])
print(f"0,2: {a:.3f}")
print(f"pre 0,2: {b:.3f}")
print(f"diff 0,2: {a - b:.3f}")

# 1 和 2
a = cosine(vecs[1], vecs[2])
b = cosine(vecs_pre[1], vecs[2])
print(f"1,2: {a:.3f}")
print(f"pre 1,2: {b:.3f}")
print(f"diff 1,2: {a - b:.3f}")

# 3 和 4
a = cosine(vecs[3], vecs[4])
b = cosine(vecs_pre[2], vecs[4])
print(f"3,4: {a:.3f}")
print(f"pre 3,4: {b:.3f}")
print(f"diff 3,4: {a - b:.3f}")

# 0 和 3
a = cosine(vecs[0], vecs[3])
b = cosine(vecs_pre[0], vecs[3])
print(f"0,3: {a:.3f}")
print(f"pre 0,3: {b:.3f}")
print(f"diff 0,3: {a - b:.3f}")


# 相关最低    0.4604  (2↔4，Java字符串 ↔ Java线程)
# 不相关最高  0.4781  (2↔7，Java字符串 ↔ 数学)
# 重叠区间    [0.4604, 0.4781]
# 更值得记的是这张表
# 阈值 0.46:  漏检 0  误检 2
# 阈值 0.47:  漏检 1  误检 1
# 阈值 0.48:  漏检 1  误检 0   ← 最优
# 阈值 0.50:  漏检 2  误检 0

# 最优阈值也有 1/15 的错误率，而且你只能选择"错哪一边"：

# - 阈值调低 → 不漏掉相关内容，但混进噪声（误检）
# - 阈值调高 → 检索干净，但会漏掉真正相关的（漏检）

# 这就是召回率 vs 准确率的取舍，第 11 课评估体系的核心。而选哪边是业务决策不是技术决策：
# - 法律/医疗检索 → 宁可多给，漏了要出事
# - 客服自动回复 → 宁可少给，错答比不答糟

# 0,1: 0.9029927716354291
# pre 0,1: 0.8513561716804044
# diff 0,1:0.052
# 0,2: 0.843
# pre 0,2: 0.794
# diff 0,2: 0.049
# 1,2: 0.791
# pre 1,2: 0.754
# diff 1,2: 0.037
# 3,4: 0.847
# pre 3,4: 0.739
# diff 3,4: 0.108
# 0,3: 0.541
# pre 0,3: 0.493
# diff 0,3: 0.047
# 加了前缀，数据反而变差了

# 结论

# 1. 相似度矩阵能看出语义层次（近义 0.79-0.90 / 同领域跨主题 0.46-0.54 / 跨领域 0.32-0.48）
# 2. M @ M.T 与循环等价，前提是已归一化；而"已归一化"只到 float32 精度（模长实测 1.0000004）
# 3. 阈值分不开好坏，最优阈值仍有 1/15 错误率 → 这是要学 rerank 的原因
# 4. 标定集的样本选择直接决定结论——同一批数据，抽 1 对说"没重叠"，抽 6 对说"有重叠"
# 5. bge-m3 不需要指令前缀，加了反而掉分（5/5 全部下降，平均 -0.054）；前缀要求随模型代际变化，查官方文档
