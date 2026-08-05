"""阶段 1 · 《Function Calling》· 动手任务 1 + 任务 3

任务 1：跑通笔记里的 function calling 示例。
1. 定义 `get_weather` 和 `calculator` 两个工具的 tools schema，实现对应的 Python 函数
2. 实现完整闭环：模型返回 tool_calls → 你执行函数 → 把结果以 role="tool" 回传 → 模型继续
3. 提问"北京和上海温度差几度"，观察它如何触发 **天气 → 天气 → 计算器** 的多轮调用链
4. 把每一轮的 messages 打印出来，看清楚 tool_call_id 是怎么配对的

任务 3：破坏性实验。
1. 把 `get_weather` 的 description 改成含糊的"一个函数"
2. 同样的问题再问一次，观察模型还能不能正确选择工具
3. 恢复后对比，把结论写进注释——体会 description 就是给模型看的 API 文档

要求/提示：
- 这是 Agent 的基石，闭环的每一步都要自己写一遍，别抄
- 注意循环终止条件：模型不再返回 tool_calls 时才算结束，否则会无限套娃
- `finish_reason == "tool_calls"` 是判断依据之一（回顾 ex04）
- 完成标准：一次提问触发 3 次工具调用并给出正确答案；破坏实验前后行为差异可复现
"""

import json
import os
from collections.abc import Callable
from typing import cast

import openai
from dotenv import load_dotenv
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)


# --- 本地函数（真实项目里是查API/查库） ---
def get_weather(city: str) -> str:
    fake_db = {"北京": "晴 32℃", "上海": "小雨 28℃"}
    return fake_db.get(city, f"{city}: 暂无数据")


def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:  # 白名单过滤，绝不裸 eval 用户输入
        return "错误: 含非法字符"
    return str(eval(expression))


TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气",
            # "description": "一个函数",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如'北京'"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，支持加减乘除和括号",
            # "description": "一个函数",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "如 '3*(4+5)'"}
                },
                "required": ["expression"],
            },
        },
    },
]

REGISTRY: dict[str, Callable[..., str]] = {
    "get_weather": get_weather,
    "calculator": calculator,
}


def run(question: str, max_round: int) -> str | None:
    messages: list[ChatCompletionMessageParam] = [{"role": "user", "content": question}]
    rounds = 0
    while True:  # 循环：模型可能连续多轮要求调工具
        if rounds >= max_round:
            return "调用轮数已达上限"
        rounds += 1
        resp = client.chat.completions.create(
            model=os.environ["LLM_MODEL"],
            messages=messages,
            tools=TOOLS,
            temperature=0,
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:  # 不再调工具 -> 最终回答
            return msg.content
        messages.append(
            cast(ChatCompletionMessageParam, msg.model_dump(exclude_none=True))
        )  # 必须先回填模型的 tool_calls 消息
        print(msg)
        for tc in msg.tool_calls:  # 可能一次返回多个（并行调用）
            if tc.type == "function":
                args = json.loads(tc.function.arguments)
                try:
                    result = REGISTRY[tc.function.name](**args)
                except KeyError:
                    result = f"错误: 未知工具 {tc.function.name}"
                except TypeError as e:
                    result = f"错误: 调用参数错误: {e}"
                print(f"[调用] {tc.function.name}({args}) -> {result}")
                messages.append(
                    cast(
                        ChatCompletionMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": str(result),
                        },
                    )
                )
            else:
                messages.append(
                    cast(
                        ChatCompletionMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": "跳过：该工具类型暂不支持，请改用其他工具",
                        },
                    )
                )
                print("跳过：调用了custom tools")


def main() -> None:
    res = run("北京和上海现在天气怎么样，温度差几度？", 5)
    print(res)


if __name__ == "__main__":
    main()

# tool 有正确的description
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 天气函数description 模糊
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 计算函数description模糊
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 双函数description模糊
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

## 以上为gpt-5.6-sol 模型 即使模糊之后，调用依旧正常，


# tool 有正确的description
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 天气函数description 模糊
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 计算函数description模糊
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 双函数description模糊
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 以上为qwen3.5:27b结果，也没能复现出破坏性实验的影响

# 双函数description模糊
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [调用] calculator({'expression': '32-28'}) -> 4

# 改用qwen2.5:0.5b-instruct 又尝试一次双模糊也没能复现

# 完全隐藏之后就失败了，所以描述还是很重要的，可以让LLM知道要用哪个方法
# description 的职能是区分同构工具
# description缺失时模型会瞎调而非停手
# 工具错误信息是第二份文档，工具的错误信息会引导模型的下一次调用，所以报错要写给模型看，不是写给日志看
# 入参校验是最后防线，防止错误问题

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_rRn4BKfW3HfMhDunSA5zYm5r', function=Function(arguments='{"arg1":"查询北京市当前实时天气：气温、天气状况、体感温度、更新时间"}', name='func1'), type='function'), ChatCompletionMessageFunctionToolCall(id='call_I5mSXFZQ9kAqOnxgbs9hSf4a', function=Function(arguments='{"arg1":"查询上海市当前实时天气：气温、天气状况、体感温度、更新时间"}', name='func2'), type='function')])
# [调用] func1({'arg1': '查询北京市当前实时天气：气温、天气状况、体感温度、更新时间'}) -> 查询北京市当前实时天气：气温、天气状况、体感温度、更新时间: 暂无数据
# [调用] func2({'arg1': '查询上海市当前实时天气：气温、天气状况、体感温度、更新时间'}) -> 错误: 含非法字符
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_irugN8LNsnO8RgewObbTb9oJ', function=Function(arguments='{"arg1":"Beijing current weather temperature"}', name='func1'), type='function'), ChatCompletionMessageFunctionToolCall(id='call_vpEGYbRrpobKShzLOHTCXjkk', function=Function(arguments='{"arg1":"Shanghai current weather temperature"}', name='func2'), type='function')])
# [调用] func1({'arg1': 'Beijing current weather temperature'}) -> Beijing current weather temperature: 暂无数据
# [调用] func2({'arg1': 'Shanghai current weather temperature'}) -> 错误: 含非法字符


# 补了调用记录的日志
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_function_calling.py
# [{'role': 'user', 'content': '北京和上海现在天气怎么样，温度差几度？'}, ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_vHzMAlQ3JoHF7lEfniuYgsYH', function=Function(arguments='{"city":"北京"}', name='get_weather'), type='function'), ChatCompletionMessageFunctionToolCall(id='call_4eRBUmdzxPPTqdgNNzMsOMNZ', function=Function(arguments='{"city":"上海"}', name='get_weather'), type='function')])]
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# [{'role': 'user', 'content': '北京和上海现在天气怎么样，温度差几度？'}, ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_vHzMAlQ3JoHF7lEfniuYgsYH', function=Function(arguments='{"city":"北京"}', name='get_weather'), type='function'), ChatCompletionMessageFunctionToolCall(id='call_4eRBUmdzxPPTqdgNNzMsOMNZ', function=Function(arguments='{"city":"上海"}', name='get_weather'), type='function')]), {'role': 'tool', 'tool_call_id': 'call_vHzMAlQ3JoHF7lEfniuYgsYH', 'content': '晴 32℃'}, {'role': 'tool', 'tool_call_id': 'call_4eRBUmdzxPPTqdgNNzMsOMNZ', 'content': '小雨 28℃'}, ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_QGip4HORQPHyCcPNkYyZ0dmB', function=Function(arguments='{"expression":"32-28"}', name='calculator'), type='function')])]
# [调用] calculator({'expression': '32-28'}) -> 4
# 调用之后，根据call_4eRBUmdzxPPTqdgNNzMsOMNZ告诉LLM是属于哪个工具的响应。

# 最终日志输出
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run  .\ex08_function_calling.py
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_iCwPyEfblPvKAHuTJJUwrRJf', function=Function(arguments='{"city":"北京"}', name='get_weather'), type='function'), ChatCompletionMessageFunctionToolCall(id='call_kSm0PRZuzGF6WmjVg2H0899I', function=Function(arguments='{"city":"上海"}', name='get_weather'), type='function')])
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_rSBgCzBTjQEWA95epcKDcIbR', function=Function(arguments='{"expression":"32-28"}', name='calculator'), type='function')])
# [调用] calculator({'expression': '32-28'}) -> 4
# - **北京**：晴，**32℃**
# - **上海**：小雨，**28℃**

# 北京比上海高 **4℃**。
