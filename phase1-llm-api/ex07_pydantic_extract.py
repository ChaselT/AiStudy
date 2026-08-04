"""阶段 1 · 《结构化输出》· 动手任务 2

任务：实现笔记里 `extract_resume` 的完整流程（LLM 输出 → pydantic 校验 → 失败重试）。
1. 定义简历的 pydantic 模型（姓名、工作年限 int、技能 list[str] 等）
2. 让模型从一段简历文本里抽取信息，输出 JSON
3. 用 pydantic 校验；校验失败时把**错误信息回喂给模型**要求它自我修复，最多重试 N 次
4. 构造一条脏数据（如把年限写成"年限：八年"），观察：
   - 第一次校验为什么失败（ValidationError 具体报什么）
   - 回喂错误后模型能不能修正成 8

要求/提示：
- pydantic 类比 POJO + Bean Validation，`ValidationError` 里的信息就是给模型的"编译错误"
- 重试次数要有上限，别写成死循环烧 token
- 完成标准：脏数据场景下能看到"失败 → 回喂 → 成功"的完整日志；
  重试耗尽时有明确的失败返回而不是抛栈崩溃
"""

import os

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, ValidationError

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=600.0,
    max_retries=3,  # 换 base_url 即换供应商
)


class Resume(BaseModel):
    name: str
    years: int = Field(ge=0, le=50, description="工作年限")
    skills: list[str] = Field(min_length=1)


def extract_resume(text: str, max_retries: int = 3) -> Resume:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": f"提取简历信息，输出JSON，符合此Schema：\n{Resume.model_json_schema()}",
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
            print(f"尝试 {attempt + 1}/{max_retries}，模型未返回内容")
            continue
        raw = resp.choices[0].message.content
        print(f"尝试 {attempt + 1}/{max_retries}，模型输出：{raw}")
        try:
            return Resume.model_validate_json(raw)
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


def extract_resume2(text: str, max_retries: int = 3) -> Resume:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "提取简历信息，输出JSON",
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
            print(f"尝试 {attempt + 1}/{max_retries}，模型未返回内容")
            continue
        raw = resp.choices[0].message.content
        print(f"尝试 {attempt + 1}/{max_retries}，模型输出：{raw}")
        try:
            return Resume.model_validate_json(raw)
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
    resume = extract_resume("李四，8年Java开发经验，熟悉Python、MySQL、Redis。")
    print(resume)
    # 造一条脏数据：年限写成"八年"
    resume2 = extract_resume("张三，八年Java开发经验，熟悉Spring、MySQL、Redis。")
    print(resume2)
    # 造一条脏数据：错误单词 拼写错误
    resume3 = extract_resume("王五，八年Java开发经验，熟悉Sprng、MySQL、Redis。")
    print(resume3)
    # 错误年限
    resume4 = extract_resume("赵六，八十年Java开发经验，熟悉Spring、MySQL、Redis。")
    print(resume4)
    # 缺少技能
    resume5 = extract_resume("钱七，八年Java开发经验。")
    print(resume5)
    # 错误年限2
    resume6 = extract_resume2("周八，八十年Java开发经验，熟悉Spring、MySQL、Redis。")
    print(resume6)


if __name__ == "__main__":
    main()
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex07_pydantic_extract.py
# 尝试 1/3，模型输出：{
#   "name": "李四",
#   "years": 8,
#   "skills": ["Python", "MySQL", "Redis"]
# }
# name='李四' years=8 skills=['Python', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{
#   "name": "张三",
#   "years": 8,
#   "skills": ["Spring", "MySQL", "Redis"]
# }
# name='张三' years=8 skills=['Spring', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{
#   "name": "王五",
#   "years": 8,
#   "skills": ["Sprng", "MySQL", "Redis"]
# }
# name='王五' years=8 skills=['Sprng', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{
#   "name": "赵六",
#   "years": 50,
#   "skills": ["Spring", "MySQL", "Redis"]
# }
# name='赵六' years=50 skills=['Spring', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{
#   "name": "钱七",
#   "years": 8,
#   "skills": ["Java开发"]
# }
# name='钱七' years=8 skills=['Java开发']

# 面对超限的年限，模型自动修正为 50 年（上限），并且技能列表里没有出现空列表，没技能的，把"Java开发"当成技能了。

# 新增提示词不传schema的方法， 复现 失败后retry的情况，模型输出了"years_of_experience"而不是"years"，导致 pydantic 校验失败，触发重试。
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex07_pydantic_extract.py
# 尝试 1/3，模型输出：{
#   "name": "李四",
#   "years": 8,
#   "skills": ["Python", "MySQL", "Redis"]
# }
# name='李四' years=8 skills=['Python', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{
#   "name": "张三",
#   "years": 8,
#   "skills": ["Spring", "MySQL", "Redis"]
# }
# name='张三' years=8 skills=['Spring', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{
#   "name": "王五",
#   "years": 8,
#   "skills": ["Sprng", "MySQL", "Redis"]
# }
# name='王五' years=8 skills=['Sprng', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{
#   "name": "赵六",
#   "years": 50,
#   "skills": ["Spring", "MySQL", "Redis"]
# }
# name='赵六' years=50 skills=['Spring', 'MySQL', 'Redis']
# 尝试 1/3，模型输出：{"name":"钱七","years":8,"skills":["Java"]}
# name='钱七' years=8 skills=['Java']
# 尝试 1/3，模型输出：{
#   "name": "周八",
#   "years_of_experience": 80,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ],
#   "position": "Java Developer"
# }
# 尝试 2/3，模型输出：{
#   "name": "周八",
#   "years": 80,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ],
#   "position": "Java Developer"
# }
# 尝试 3/3，模型输出：{
#   "name": "周八",
#   "years": 50,
#   "skills": [
#     "Spring",
#     "MySQL",
#     "Redis"
#   ],
#   "position": "Java Developer"
# }
# name='周八' years=50 skills=['Spring', 'MySQL', 'Redis']
# 1. 错误逐层暴露——第 1 次报 years 缺失时 le=50 根本没机会跑，所以模型只改字段名不改值；第 2 次才轮到超限报出来。重试上限按"错误层数"估，不是按"错误数"估
# 2. position 字段三次都在，pydantic 一次没抗议——默认忽略多余字段，要拒绝得写 model_config = ConfigDict(extra="forbid")（对应 Jackson 的 FAIL_ON_UNKNOWN_PROPERTIES）
