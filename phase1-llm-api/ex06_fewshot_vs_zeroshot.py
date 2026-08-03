"""阶段 1 · 《Prompt工程》· 动手任务 2

任务：zero-shot 与 few-shot 的格式稳定性对比。
1. 抽取任务：从一段招聘 JD 里抽出「岗位 / 城市 / 薪资」
2. 准备 5 个不同的 JD 用例（自己找几段真实 JD 文本，长短风格各异）
3. zero-shot 版：只描述任务，不给例子，5 个用例各跑一次
4. few-shot 版：在 prompt 里给 2~3 个输入输出示范，同样 5 个用例各跑一次
5. 统计两边的**格式稳定性**：输出结构一致的比例、能否直接被程序解析

要求/提示：
- 判断"格式稳定"要有客观标准（比如能否 split / 能否 json.loads），别凭感觉
- few-shot 的例子本身要格式统一，示范就是契约
- 完成标准：给出两组成功率数字，并在注释里回答"few-shot 到底改变了什么"
"""

import os
import pathlib

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletion

from jd_samples import JDS

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=600.0,
    max_retries=3,  # 换 base_url 即换供应商
)

zero_shot_system_prompt = """
从招聘 JD 中抽取岗位、城市、薪资
"""

few_shot_system_prompt = (
    pathlib.Path(__file__).parent / "prompts" / "jd_extract_fewshot.md"
).read_text(encoding="utf-8")

few_shot = [
    {
        "role": "user",
        "content": "高级 Java 工程师 15-28k 昆明 5-10年",
    },
    {
        "role": "assistant",
        "content": "岗位：高级 Java 工程师 城市：昆明 薪资：15-28k",
    },
    {
        "role": "user",
        "content": "agent系统开发工程师12-24K昆明3-5年Agent系统开发工程师工作地点:昆明市五华区新途径教育培训学校有限公司",
    },
    {
        "role": "assistant",
        "content": "岗位：agent系统开发工程师 城市：昆明 薪资：12-24K",
    },
    {
        "role": "user",
        "content": "Java + AI 混合岗（高级/资深）Base：南京薪资：面议，具体面谈后按能力定级。",
    },
    {
        "role": "assistant",
        "content": "岗位：Java + AI 混合岗（高级/资深） 城市：南京 薪资：面议",
    },
    {
        "role": "user",
        "content": "Java + AI 混合岗（高级/资深）Base：南京薪资：28万/年，具体面谈后按能力定级。",
    },
    {
        "role": "assistant",
        "content": "岗位：Java + AI 混合岗（高级/资深） 城市：南京 薪资：23k",
    },
]


def llm_call(message: list) -> ChatCompletion | str:
    # 模型错误演示
    try:
        resp = client.chat.completions.create(
            model=os.environ["LLM_MODEL"], messages=message
        )
        return resp
    except openai.RateLimitError as e:  # 429：限流，等一下再来
        retry_after = e.response.headers.get("retry-after", "5")
        print(f"限流，{retry_after}s 后重试")
        return "限流了，请稍后再试"
    except openai.APITimeoutError:  # 超时：可重试
        print("超时，重试或降级到小模型")
        return "请稍后再试"
    except openai.APIStatusError as e:  # 其他非 2xx
        if e.status_code >= 500:
            print(f"服务端错误 {e.status_code}，可重试")
            return "请稍后再试"
        else:
            print(f"请求有问题（{e.status_code}），重试也没用：{e.message}")
            return "请求失败，请检查参数"
    except openai.APIConnectionError:  # 网络层失败（代理挂了常见）
        print("连不上，检查网络/代理")
        return "请求失败，请检查网络"


def main() -> None:
    for jd in JDS:
        messages = [{"role": "system", "content": zero_shot_system_prompt}]
        messages.append({"role": "user", "content": jd})
        resp = llm_call(messages)
        if isinstance(resp, str):
            print(resp)
            continue
        else:
            print(f"zero-shot: {resp.choices[0].message.content}")

    for jd in JDS:
        messages2 = [{"role": "system", "content": few_shot_system_prompt}]
        messages2.extend(few_shot)
        messages2.append({"role": "user", "content": jd})
        resp = llm_call(messages2)
        if isinstance(resp, str):
            print(resp)
            continue
        else:
            print(f"few-shot: {resp.choices[0].message.content}")


if __name__ == "__main__":
    main()


# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex06_fewshot_vs_zeroshot.py
# zero-shot: 岗位：AI 应用开发工程师
# 城市：杭州
# 薪资：25-40K·15 薪
# zero-shot: 根据您提供的 JD 信息，抽取结果如下：

# *   **岗位**：大模型应用工程师（Agent 方向）
# *   **城市**：成都
# *   **薪资**：月薪15000-20000元，年终奖2-4个月
# zero-shot: *   **岗位**：高级 AI 工程师
# *   **城市**：北京·望京
# *   **薪资**：45-70W/年
# zero-shot: - **岗位**：Java + AI 混合岗（高级/资深）
# - **城市**：南京
# - **薪资**：面议
# zero-shot: *   **岗位**：LLM 平台研发工程师
# *   **城市**：北京 / 上海 / 深圳
# *   **薪资**：30-50K，13 薪
# zero-shot: 根据提供的招聘 JD，抽取的关键信息如下：

# *   **岗位**：多模态算法应用工程师
# *   **城市**：苏州（苏州工业园区）
# *   **薪资**：20-35K（14 薪）
# zero-shot: - **岗位**：多模态算法应用工程师
# - **城市**：苏州（苏州工业园区）
# - **薪资**：年薪 25 万
# few-shot: 岗位：AI应用开发工程师 城市：杭州 薪资：25k-40k
# few-shot: 岗位：大模型应用工程师（Agent 方向） 城市：成都 薪资：15k-20k
# few-shot: 岗位：高级 AI 工程师 城市：北京 薪资：37.5-59k
# few-shot: 岗位：Java + AI 混合岗（高级/资深） 城市：南京 薪资：面议
# few-shot: 岗位：LLM 平台研发工程师 城市：北京/上海/深圳 薪资：30-50k
# few-shot: 岗位：多模态算法应用工程师 城市：苏州 薪资：20-35K（14薪）
# few-shot: 岗位：多模态算法应用工程师 城市：苏州 薪资：约 21k

# 1. zero-shot 如果按照 岗位、城市、薪资 的顺序来 split，还需要处理掉MD的格式，只有 4/7 能成功解析，剩下三条都多了无用的解释、介绍
# 2. few-shot 则是 7/7 成功。
# 3. few-shot 教会了 zero-shot 完全没做的事：年薪→月薪换算（只给了一个示例，模型自己推出规则）
# 4. few-shot 的覆盖面 = 示例的覆盖面：第 6 条"14薪"没被示例覆盖，就没归一化
# 5. 回答骨架里那个问题"few-shot 到底改变了什么"：它改变的不只是格式，是让模型从示例中归纳出你没明说的规则——而这正是 instruction 做不到的
