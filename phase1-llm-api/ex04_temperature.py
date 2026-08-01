"""阶段 1 · 《采样参数详解》· 动手任务 1 + 任务 3

任务 1：temperature 对比实验。
1. 选一个**创意型**问题（如"给一家做 AI 面试的创业公司起 3 个名字"）
2. 分别用 temperature = 0 / 0.7 / 1.4，每档各跑 3 次，共 9 次
3. 把 9 个输出整齐打印出来对比，总结规律写进注释

任务 3：确定性验证。
1. temperature=0 跑同一个 prompt 10 次
2. 统计输出**完全相同**的比例
3. 写结论注释：temperature=0 到底是不是 100% 确定性？为什么？

要求/提示：
- 用本地 Ollama 跑更省钱，10+ 次调用云端也花不了几分钱，任选
- 打印时把每次输出编号，肉眼对比才看得出差异
- 完成标准：能用一句话说清楚 temperature 在采样时到底改变了什么
  （提示：它作用在 softmax 之前的 logits 上），并解释你观察到的重复率
"""

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


import os


def normalize(text: str) -> str:
    """忽略首尾空格、中文逗号以及逗号旁的空格。"""
    return ",".join(item.strip() for item in text.replace("，", ",").strip().split(","))


def main() -> None:
    runs = 10

    print(f"{'temperature':<16}|{'轮次':<8}|结果")

    for temperature in [0, 0.7, 1.4]:
        results: list[str] = []
        fingerprints: list[str | None] = []

        for i in range(runs):
            resp = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个乐于助人的助手。",
                    },
                    {
                        "role": "user",
                        "content": (
                            "给一家做 AI 面试的创业公司起 3 个名字，"
                            "只输出名字，不要解释，三个名字用逗号分隔。"
                        ),
                    },
                ],
                temperature=temperature,
            )

            raw_text = resp.choices[0].message.content or ""
            result = normalize(raw_text)

            results.append(result)
            fingerprints.append(resp.system_fingerprint)

            print(f"{temperature:<16}|{i + 1:<8}|{result}")

        # set 用来得到所有不同的候选结果
        unique_results = set(results)

        # 找到出现次数最多的结果
        dominant_result = max(unique_results, key=results.count)
        deterministic_count = results.count(dominant_result)
        deterministic_ratio = deterministic_count / runs

        print(
            f"\ntemperature={temperature}："
            f"确定性比例 {deterministic_count}/{runs}"
            f" = {deterministic_ratio:.0%}"
        )
        print(f"不同结果数量：{len(unique_results)}")
        print(f"出现最多的结果：{dominant_result}")
        print(f"系统指纹：{set(fingerprints)}")
        print("-" * 80)


if __name__ == "__main__":
    main()


# 5.6不生效，改本地使用qwen2.5:0.5b-instruct
# temperature     |轮次              |结果
# 0               |1               | AI面试宝典  AI面试秘籍  AI面试指南|
# 0               |2               | AI面试宝典  AI面试小能手  AI面试高手团|
# 0               |3               | AI面试宝典  AI面试小能手  AI面试高手团|
# 0.7             |1               | AI面试宝典  AI面试宝典 2.0  AI面试大法|
# 0.7             |2               | AI面试小队  AI面试学院  AI面试集团|
# 0.7             |3               | 好智者、智慧行、智选机     |
# 1.4             |1               | AI Innovations Humanize|
# 1.4             |2               | AI启航实验室 开学吧数据科技有限公司|
# 1.4             |3               | AI探索世界 助力未来技能 钦望人才顾问|
# 0 的时候，输出结果相似度非常高，几乎完全相同，说明 temperature=0 时模型的输出是高度确定性的。
# 0.7 时，输出结果有一定的多样性，但仍然存在一些相似的名字，说明 temperature=0.7 时模型的输出具有一定的随机性。
# 1.4 时，输出结果更加多样化，几乎没有重复的名字，说明 temperature=1.4 时模型的输出具有较高的随机性和创造性。

# 中转站5.6输出
# temperature     |轮次              |结果
# 0               |1               | 智面科技，见微人才，慧聘引擎  |
# 0               |2               | 智面云,伯乐镜,面未来     |
# 0               |3               | 智面星，伯乐镜，慧聘官     |
# 0.7             |1               | 智面科技,镜鉴AI,伯乐云面  |
# 0.7             |2               | 智面科技,镜问AI,慧聘引擎  |
# 0.7             |3               | 慧面，镜聘，智遇科技      |
# 1.4             |1               | 智面未来,识才引擎,面见智能  |
# 1.4             |2               | 智面，识才镜，慧聘官      |
# 1.4             |3               | 智面，识才镜，面试星球     |
# 有重复，但是基本没有重复很高的，temperature 无效


# 连续输出10次temperature=0 结果相似度非常高，但是也不能百分百确定性
# AI面试宝典  AI面试秘籍  AI面试指南|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|
# AI面试宝典  AI面试小能手  AI面试高手团|


# temperature 是在 softmax 之前给 logits 做除法——除以小于 1 的数会放大 token 之间的分数差距
# （分布变尖、趋向确定），除以大于 1 的数会压缩差距（分布变平、趋向随机）。它不改变 token 的相对排序，只改变"第二名有多大机会翻盘"


# temperature     |轮次      |结果
# 0               |1       |1. "AI面试宝典"2. "智选未来"3. "智能面试通"
# 0               |2       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |3       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |4       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |5       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |6       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |7       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |8       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |9       |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 0               |10      |1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"

# temperature=0：确定性比例 9/10 = 90%
# 不同结果数量：2
# 出现最多的结果：1. "AI面试宝典"2. "智选未来"3. "AI面试加速器"
# 系统指纹：{'fp_ollama'}
