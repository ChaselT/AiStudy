"""阶段 1 · 《Function Calling》· 动手任务 2

任务：把工具集扩展到 4 个。
1. 复用 ex08 的闭环，新增两个工具：
   - `get_current_time()`：返回本机当前时间
   - `read_file(path)`：读取文件内容，但**限定只能读 `E:\\workspace\\AiStudy` 目录内的文件**，
     必须做路径校验（防目录穿越，如 `..\\..\\Windows\\System32\\...`）
2. 连同 `get_weather`、`calculator` 共 4 个工具注册到 tools 列表
3. 设计几个问题，分别精准触发不同的工具，验证模型选对了

要求/提示：
- 路径校验是安全题不是功能题：想想 `Path.resolve()` 之后怎么判断"在不在某个目录下"，
  为什么直接用 `startswith` 字符串比较不够（符号链接、相对路径、大小写）
- 工具执行失败（文件不存在、路径越界）时要把**错误信息**回传给模型，让它体面地告诉用户，
  而不是让程序抛异常崩掉
- 完成标准：4 个工具都被正确触发过；越界路径请求被拦下且模型能解释原因；
  这份工具注册表结构清晰到可以直接搬进项目① `tools.py`
"""

import json
import os
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


def get_current_time() -> str:
    china_tz = timezone(timedelta(hours=8))
    return datetime.now(china_tz).strftime("%Y-%m-%d %H:%M")


BASE_DIR = Path(os.environ["READ_BASE_DIR"]).resolve()


MAX_FILE_LINES = 10
MAX_FILE_CHARS = 4000


def read_file(path: str) -> str:
    raw_path = Path(path)

    # 如果传入相对路径，就认为是相对于 BASE_DIR
    candidate = raw_path if raw_path.is_absolute() else BASE_DIR / raw_path

    try:
        real_path = candidate.resolve()
    except OSError:
        return "错误: 路径无效或无法访问"

    # 必须 resolve 后再校验，防目录穿越、防软链接跳出 BASE_DIR
    try:
        real_path.relative_to(BASE_DIR)
    except ValueError:
        return "错误: 禁止读取目录外的文件"
    if not real_path.exists():
        return "错误: 文件不存在"
    if not real_path.is_file():
        return "错误: 目标不是文件"

    try:
        content = real_path.read_text(encoding="utf-8")
    except PermissionError:
        return "错误: 没有权限读取文件"
    except UnicodeDecodeError:
        return "错误: 文件不是 UTF-8 文本"
    except OSError:
        return "错误: 读取文件失败"

    total_lines = len(content.splitlines())

    truncated_content = content
    truncated_reasons: list[str] = []

    if total_lines > MAX_FILE_LINES:
        truncated_content = "\n".join(truncated_content.splitlines()[:MAX_FILE_LINES])
        truncated_reasons.append(f"共 {total_lines} 行，仅返回前 {MAX_FILE_LINES} 行")

    if len(truncated_content) > MAX_FILE_CHARS:
        truncated_content = truncated_content[:MAX_FILE_CHARS]
        truncated_reasons.append(f"内容过长，仅返回前 {MAX_FILE_CHARS} 个字符")

    if truncated_reasons:
        return f"已截断，{'; '.join(truncated_reasons)}：\n{truncated_content}"

    return content


TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气",
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
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "如 '3*(4+5)'"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取东八区当前时间",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": r"读取 E:\workspace\AiStudy 目录内的文件内容，禁止读取目录外文件",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件路径"}},
                "required": ["path"],
            },
        },
    },
]

REGISTRY: dict[str, Callable[..., str]] = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_current_time": get_current_time,
    "read_file": read_file,
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
    questions = [
        "北京和上海现在天气怎么样，温度差几度？",
        "现在本机时间是多少？",
        r"读取 E:\workspace\AiStudy\README.md 的内容",
        r"读取 C:\Windows\System32\drivers\etc\hosts 的内容",
        r"读取 ..\..\Windows\System32\drivers\etc\hosts 的内容",
    ]
    for question in questions:
        print("=" * 60)
        print("问题:", question)
        print(run(question, 5))

    res1 = read_file(r"C:\Windows\System32\drivers\etc\hosts")
    res2 = read_file(r"..\..\tmp\pyc-strings.txt")
    print(f"绝对地址跨盘越界：{res1}")
    print(f"相对地址越界：{res2}")


if __name__ == "__main__":
    main()

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex08_more_tools.py
# ============================================================
# 问题: 北京和上海现在天气怎么样，温度差几度？
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_sjGF3EsAeuLgJq6G6t0o4ILk', function=Function(arguments='{"city":"北京"}', name='get_weather'), type='function'), ChatCompletionMessageFunctionToolCall(id='call_hMPTTY39JtND0OHs8n8WGDa1', function=Function(arguments='{"city":"上海"}', name='get_weather'), type='function')])
# [调用] get_weather({'city': '北京'}) -> 晴 32℃
# [调用] get_weather({'city': '上海'}) -> 小雨 28℃
# - **北京**：晴，**32℃**
# - **上海**：小雨，**28℃**

# 两地温度相差 **4℃**，北京比上海高 **4℃**。
# ============================================================
# 问题: 现在本机时间是多少？
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_rGyNzXhpr38X2kO2wl3n6Vh6', function=Function(arguments='{}', name='get_current_time'), type='function')])
# [调用] get_current_time({}) -> 2026-08-05 18:05
# 当前时间是 **2026年8月5日 18:05（东八区）**。
# ============================================================
# 问题: 读取 E:\workspace\AiStudy\README.md 的内容
# ChatCompletionMessage(content=None, refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[ChatCompletionMessageFunctionToolCall(id='call_bZGD4QvHbyKlmZzdnZRhmZVO', function=Function(arguments='{"path":"E:\\\\workspace\\\\AiStudy\\\\README.md"}', name='read_file'), type='function')])
# [调用] read_file({'path': 'E:\\workspace\\AiStudy\\README.md'}) -> 已截断，共 26 行，仅返回前 10 行：
# # AiStudy — Java 工程师转型 AI 应用工程师·学习代码全记录

# 一名后端 Java 工程师从零转型 AI 应用工程师的完整学习轨迹（2026-07 启程，规划 10-13 个月）。本仓库存放全程的实战代码；配套的知识图谱笔记在姊妹仓库 [ai-learning-notes](https://github.com/ChaselT/ai-learning-notes)。

# ## 学习路线

# | 阶段 | 主题 | 产出 | 目录 |
# |------|------|------|------|
# | 0 | Python 从零到工程化（uv/typing/pydantic/async） | 30+ 练习 | `phase0-python/` |
# | 1 | LLM API 应用开发 | 项目① CLI 智能助手 | `phase1-llm-api/` |
# `E:\workspace\AiStudy\README.md` 共 26 行，但工具仅返回了前 10 行：

# ```markdown
# # AiStudy — Java 工程师转型 AI 应用工程师·学习代码全记录

# 一名后端 Java 工程师从零转型 AI 应用工程师的完整学习轨迹（2026-07 启程，规划 10-13 个月）。本仓库存放全程的实战代码；配套的知识图谱笔记在姊妹仓库 [ai-learning-notes](https://github.com/ChaselT/ai-learning-notes)。

# ## 学习路线

# | 阶段 | 主题 | 产出 | 目录 |
# |------|------|------|------|
# | 0 | Python 从零到工程化（uv/typing/pydantic/async） | 30+ 练习 | `phase0-python/` |
# | 1 | LLM API 应用开发 | 项目① CLI 智能助手 | `phase1-llm-api/` |
# ```

# 其余 16 行因工具返回长度限制而被截断。
# ============================================================
# 问题: 读取 C:\Windows\System32\drivers\etc\hosts 的内容
# 抱歉，无法读取该文件。工具仅允许访问 `E:\workspace\AiStudy` 目录内的文件，`C:\Windows\System32\drivers\etc\hosts` 不在允许范围内。
# ============================================================
# 问题: 读取 ..\..\Windows\System32\drivers\etc\hosts 的内容
# 无法读取该文件。文件读取工具仅允许访问 `E:\workspace\AiStudy` 目录内的文件，`..\..\Windows\System32\drivers\etc\hosts` 位于允许范围之外。
# 绝对地址跨盘越界：错误: 禁止读取目录外的文件
# 相对地址越界：错误: 禁止读取目录外的文件
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api>
