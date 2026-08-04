"""阶段 1 · 《结构化输出》· 动手任务 3（实战）

任务：把口语化的任务描述解析成结构化 Todo。
1. 定义 pydantic 模型 `Todo(title, deadline, priority)`
   - `deadline` 用 `datetime`，`priority` 建议用 Enum 或 Literal 限定取值
2. 输入示例："明天下午三点前把周报发给王总，很急"
3. 输出应为：title="把周报发给王总"、deadline=明天 15:00 的具体时间、priority=高
4. 再自己造 4~5 个说法各异的输入测试鲁棒性
   （"下周一之前"、"这两天吧"、"月底前搞定"、"不急"…）

要求/提示：
- 相对时间是难点：模型不知道"今天"是几号，你得把当前时间写进 prompt 告诉它
- 模糊表达（"这两天"）解析不出来时应该怎么办？想清楚是兜底默认值还是让它返回 null
- 完成标准：5+ 个用例全部解析成合法的 `Todo` 对象并打印；
  mypy 检查零报错（`uv run mypy ex07_todo_parser.py`）
"""

import os
from datetime import datetime
from typing import Literal

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ValidationError, field_serializer

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=600.0,
    max_retries=3,  # 换 base_url 即换供应商
)


class Todo(BaseModel):
    title: str
    deadline: datetime
    priority: Literal["高", "中", "低"]

    @field_serializer("deadline", when_used="json")
    def format_deadline(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")


def extract_todo(text: str, max_retries: int = 3) -> Todo:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": f"提取待办事项信息，今天是{datetime.now().strftime('%Y-%m-%d %H:%M')}，输出JSON，符合此Schema：\n{Todo.model_json_schema()}",  # noqa: DTZ005
        },
        {"role": "user", "content": text},
    ]
    for attempt in range(max_retries):
        resp = client.chat.completions.create(
            model=os.environ["LLM_MODEL"],
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        if resp.choices[0].message.content is None:
            print(
                f"尝试 {attempt + 1}/{max_retries}，模型未返回内容,finish_reason:{(resp.choices[0].finish_reason)} message.refusal: {resp.choices[0].message.refusal}"
            )
            raise RuntimeError("模型未返回内容")
        raw = resp.choices[0].message.content
        print(f"尝试 {attempt + 1}/{max_retries}，模型输出：{raw}")
        try:
            return Todo.model_validate_json(raw)
        except ValidationError as e:
            # 把错误喂回去让模型自己改，比盲目重跑有效
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"输出未通过校验：{e}。请修正后重新输出JSON。",
                }
            )
    raise RuntimeError(f"结构化输出失败，已重试 {max_retries} 次")


def main() -> None:
    # 正常数据
    todo = extract_todo("明天下午三点前把周报发给王总，很急")
    print(todo.model_dump_json())
    # 造一条脏数据：模糊时间 "下周一之前"
    todo2 = extract_todo("下周一之前完成项目计划，中等优先级")
    print(todo2.model_dump_json())
    # 造一条脏数据：模糊时间 "这两天吧"
    todo3 = extract_todo("这两天吧，整理会议纪要，低优先级")
    print(todo3.model_dump_json())
    # 造一条脏数据：模糊时间 "月底前搞定"
    todo4 = extract_todo("月底前搞定财务报表，高优先级")
    print(todo4.model_dump_json())
    # 造一条脏数据：模糊时间 "不急"
    todo5 = extract_todo("不急，更新团队文档，中等优先级")
    print(todo5.model_dump_json())


if __name__ == "__main__":
    main()

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex07_todo_parser.py
# 尝试 1/3，模型输出：{
#   "title": "提交周报",
#   "deadline": "2026-08-05T15:00:00",
#   "priority": "高"
# }
# {"title":"提交周报","deadline":"2026-08-05 15:00:00","priority":"高"}
# 尝试 1/3，模型输出：{
#   "title": "完成项目计划",
#   "deadline": "2026-08-10T00:00:00",
#   "priority": "中"
# }
# {"title":"完成项目计划","deadline":"2026-08-10 00:00:00","priority":"中"}
# 尝试 1/3，模型输出：{
#   "title": "整理会议纪要",
#   "deadline": "2026-08-06T17:29:26.583475",
#   "priority": "低"
# }
# {"title":"整理会议纪要","deadline":"2026-08-06 17:29:26","priority":"低"}
# 尝试 1/3，模型输出：{
#   "properties": {
#     "title": {"type": "string"},
#     "deadline": {"format": "date-time", "type": "string"},
#     "priority": {"enum": ["高", "中", "低"], "type": "string"}
#   },
#   "required": ["title", "deadline", "priority"],
#   "title": "Todo",
#   "type": "object"
# }
# 尝试 2/3，模型输出：{
#   "title": "搞定财务报表",
#   "deadline": "2026-08-31T23:59:59.974540",
#   "priority": "高"
# }
# {"title":"搞定财务报表","deadline":"2026-08-31 23:59:59","priority":"高"}
# 尝试 1/3，模型输出：{
#   "title": "更新团队文档",
#   "deadline": "2026-08-11T17:31:04.400254",
#   "priority": "中"
# }
# {"title":"更新团队文档","deadline":"2026-08-11 17:31:04","priority":"中"}

# 响应结果出现了 schema 复读、时间直接微秒复制，只修改了日期，因为提示词没有说明时间阶段如何处理、
# 模糊时间直接给了一个具体时间，说明模型没有理解"这两天"、"月底前"、"不急"等模糊时间的含义，应该在提示词里明确告诉模型这些模糊时间的兜底处理方式。
