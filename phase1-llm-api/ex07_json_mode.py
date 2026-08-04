"""阶段 1 · 《结构化输出》· 动手任务 1

任务：验证 `response_format` 的作用。
1. 选一个抽取任务（比如从一段自我介绍里抽出 姓名/年龄/技能列表）
2. **不开** `response_format`，只在 prompt 里说"请输出 JSON"，跑 10 次，
   每次用 `json.loads` 尝试解析，统计成功率
3. **开启** `response_format={"type": "json_object"}`，同样跑 10 次，统计成功率
4. 把两组数字和典型失败样本（比如带 ```json 代码块围栏的输出）记进注释

要求/提示：
- 失败样本很有价值，把模型到底吐了什么原样打印出来看
- 注意：并非所有后端都支持 json mode，Ollama 与云端行为可能不同，注释里记下你测的是哪个
- 完成标准：两组成功率数字 + 至少一个失败样本 + 一句话结论
"""

import json
import os

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def call_llm(json_mode: bool) -> str | None:
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": "从简历文本提取信息，输出JSON，字段：name(str), years(int), skills(list[str])。",
            },
            {
                "role": "user",
                "content": "张三，8年Java开发经验，熟悉Spring、MySQL、Redis。",
            },
        ],
        response_format={"type": "json_object"} if json_mode else openai.omit,
    )
    if resp.usage:  # 收窄：这个分支里 resp.usage 一定是 CompletionUsage
        print(resp.choices[0].message.content)
        print(
            f"prompt_tokens:{resp.usage.prompt_tokens},completion_tokens:{resp.usage.completion_tokens},total_tokens:{resp.usage.total_tokens}"
        )
    else:
        print("该后端未返回 usage")
    return resp.choices[0].message.content


def main() -> None:
    with_json_success_count = 0
    without_json_success_count = 0
    for i in range(10):
        print(f"Run {i + 1} with JSON mode:")
        res = call_llm(json_mode=True)
        if res is None:
            print("No content returned")
        else:
            try:
                res = json.loads(res)  # 如果不是合法 JSON 会抛异常
                with_json_success_count += 1
            except json.JSONDecodeError:
                print("Failed to decode JSON")
        print(f"Run {i + 1} without JSON mode:")
        res = call_llm(json_mode=False)
        if res is None:
            print("No content returned")
        else:
            try:
                res = json.loads(res)  # 如果不是合法 JSON 会抛异常
                without_json_success_count += 1
            except json.JSONDecodeError:
                print("Failed to decode JSON")

    print(f"With JSON mode: {with_json_success_count}/10 successful")
    print(f"Without JSON mode: {without_json_success_count}/10 successful")


if __name__ == "__main__":
    main()
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex07_json_mode.py
# Run 1 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:568,completion_tokens:44,total_tokens:612
# Run 1 without JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:52,completion_tokens:493,total_tokens:545
# Run 2 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:163,completion_tokens:49,total_tokens:212
# Run 2 without JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Spring", "MySQL", "Redis"]
# }
# prompt_tokens:52,completion_tokens:654,total_tokens:706
# Run 3 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:486,completion_tokens:44,total_tokens:530
# Run 3 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# ```
# prompt_tokens:52,completion_tokens:427,total_tokens:479
# Failed to decode JSON
# Run 4 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:449,completion_tokens:44,total_tokens:493
# Run 4 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# ```
# prompt_tokens:52,completion_tokens:548,total_tokens:600
# Failed to decode JSON
# Run 5 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:433,completion_tokens:44,total_tokens:477
# Run 5 without JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:52,completion_tokens:870,total_tokens:922
# Run 6 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:1016,completion_tokens:49,total_tokens:1065
# Run 6 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# ```
# prompt_tokens:52,completion_tokens:957,total_tokens:1009
# Failed to decode JSON
# Run 7 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:484,completion_tokens:44,total_tokens:528
# Run 7 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# ```
# prompt_tokens:52,completion_tokens:420,total_tokens:472
# Failed to decode JSON
# Run 8 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:594,completion_tokens:44,total_tokens:638
# Run 8 without JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:52,completion_tokens:570,total_tokens:622
# Run 9 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:695,completion_tokens:44,total_tokens:739
# Run 9 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# ```
# prompt_tokens:52,completion_tokens:364,total_tokens:416
# Failed to decode JSON
# Run 10 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:446,completion_tokens:44,total_tokens:490
# Run 10 without JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:52,completion_tokens:653,total_tokens:705
# With JSON mode: 10/10 successful
# Without JSON mode: 5/10 successful
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api>

# 没有json mode时，模型有时会在输出里加上 ```json 代码块围栏，导致 json.loads 解析失败。
# 27b 上 prompt_tokens 乱跳、completion 塌缩
# 而用0.5b 上两组prompt_tokens恒定 51
# 结论（推理模型的 thinking token 被记进了 prompt_eval_count，分栏失真但总量相当，看成本要看 total）。

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex07_json_mode.py
# Run 1 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 1 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# ```
# prompt_tokens:51,completion_tokens:38,total_tokens:89
# Failed to decode JSON
# Run 2 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 2 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# ```
# prompt_tokens:51,completion_tokens:45,total_tokens:96
# Failed to decode JSON
# Run 3 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 3 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     "Spring"
#   ]
# }
# ```
# prompt_tokens:51,completion_tokens:37,total_tokens:88
# Failed to decode JSON
# Run 4 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 4 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# ```
# prompt_tokens:51,completion_tokens:41,total_tokens:92
# Failed to decode JSON
# Run 5 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 5 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["编程语言", "框架", "数据库"]
# }
# ```
# prompt_tokens:51,completion_tokens:36,total_tokens:87
# Failed to decode JSON
# Run 6 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:51,completion_tokens:37,total_tokens:88
# Run 6 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# ```
# prompt_tokens:51,completion_tokens:38,total_tokens:89
# Failed to decode JSON
# Run 7 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["java", "spring", "mysql", "redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 7 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java"
#   ]
# }
# ```
# prompt_tokens:51,completion_tokens:33,total_tokens:84
# Failed to decode JSON
# Run 8 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 8 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# ```
# prompt_tokens:51,completion_tokens:38,total_tokens:89
# Failed to decode JSON
# Run 9 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:34,total_tokens:85
# Run 9 without JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     "Spring",
#     "MySQL",
#     "Redis"
#   ]
# }
# prompt_tokens:51,completion_tokens:41,total_tokens:92
# Run 10 with JSON mode:
# {
#   "name": "张三",
#   "years": 8,
#   "skills": ["Java", "Selenium", "Spring", "MySQL", "Redis"]
# }
# prompt_tokens:51,completion_tokens:38,total_tokens:89
# Run 10 without JSON mode:
# ```json
# {
#   "name": "张三",
#   "years": 8,
#   "skills": [
#     "Java",
#     " Spring",
#     " MySQL",
#     " Redis"
#   ]
# }
# ```
# prompt_tokens:51,completion_tokens:45,total_tokens:96
# Failed to decode JSON
# With JSON mode: 10/10 successful
# Without JSON mode: 1/10 successful

# 换成qwen2.5:0.5b-instruct 模型后，token消耗 变化明显 prompt_tokens:51,所以之前的问题应该是thinking 模型的问题
# 模型越小，json_mode 的重要性越高，可以用于保证模型下限
# json_mode 只保证格式，不保证内容正确
