r"""阶段 1 · 项目①：CLI 智能助手 · 工具定义与注册表

本文件职责：定义各工具的 JSON schema、实现对应的 Python 函数、维护名字到函数的注册表。

═══════════════════ 参考索引（行号已核实）═══════════════════
| 要写的            | 抄哪                                    |
|-------------------|-----------------------------------------|
| get_current_time  | ex08_more_tools.py:57                   |
| calculator        | ex08_more_tools.py:50  白名单在 :51-52  |
| read_file         | ex08_more_tools.py:69-98  整段搬        |
| TOOLS schema 列表 | ex08_more_tools.py:101-154              |
| REGISTRY 注册表   | ex08_more_tools.py:156-161              |
════════════════════════════════════════════════════════════

至少 3 个工具：

1. `get_current_time()` —— 无参数，最适合用来打通工具闭环
   注意 description 与实现必须一致：实现里写死东八区，description 就别说"本机时间"

2. `calculator(expression)` —— 安全求值，**不要裸 eval**
   白名单 `set("0123456789+-*/(). ")` 直接搬，别改。
   这行在 ex08 实战拦下过模型往里塞自然语言（模型不知道参数含义时会瞎填）

3. `read_file(path)` —— 路径沙箱，整段搬 ex08_more_tools 的实现
   四步定序不能乱：**resolve() → relative_to 判边界 → exists 判存在 → is_file 判类型**
   - resolve 必须在最前：relative_to 是路径组件前缀比较，不解析 `..`，
     顺序反了 `..\..\` 能直接穿过去（实测可读到 BASE_DIR 外的真实文件）
   - 不要用 strict=True：它会把存在性检查隐式提前，导致目录外文件"存在"与"不存在"
     返回不同消息，泄露文件是否存在
   - 四种错误消息各自独立（越界/不存在/不是文件/读取失败），它们是给模型看的文档
   - 返回内容要按行数和字符数双重截断，并**显式告知已截断**——
     否则模型会以为看到的就是全文

设计要求：

- 注册表：一个 dict 把工具名映射到函数，schema 列表一并导出。
  **新增工具时只改本文件**，llm.py 和 main.py 都不用动——这是设计质量的检验标准
- REGISTRY 的类型标注用 `dict[str, Callable[..., str]]`。
  `...` 表示"参数签名不做承诺"——按字符串查表调用本来就是运行时才能确定的事，
  静态类型验证不了。这比 `# type: ignore` 诚实
- 每个工具的 description 认真写，它就是给模型看的 API 文档。
  实测：函数名/参数名/参数 description 三者中性化之后，
  模型会把自己的意图描述整句塞进参数里瞎调，而不是停下来说不知道
- 工具执行必须捕获异常并返回**结构化的错误信息**给模型，绝不让异常冒泡到主循环。
  错误信息会引导模型的下一次调用（实测：返回"暂无数据"后它会自己换英文重试），
  所以报错要写给模型看，不是写给日志看

加分项「工具并行调用」：
    `asyncio.gather` **只能并发 awaitable**，直接 gather 几个同步调用等于顺序执行。
    两条路：① 工具函数本身写成 async（联网类工具用 httpx.AsyncClient 才有意义）；
           ② 保持同步，用 asyncio.to_thread(fn, **args) 包一层再 gather
    先想清楚值不值得：get_current_time / calculator 都是微秒级，并行省不下什么，
    只有 search_web 这类网络 I/O 才有收益。**先测单个工具的耗时，别为不存在的瓶颈优化**
"""

import json
import os
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openai.types.chat import (
    ChatCompletionToolParam,
)


def tool_error(code: str, message: str) -> str:
    return json.dumps(
        {"ok": False, "error": {"code": code, "message": message}},
        ensure_ascii=False,
    )


def get_current_time() -> str:
    china_tz = timezone(timedelta(hours=8))
    return datetime.now(china_tz).strftime("%Y-%m-%d %H:%M")


def calculator(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip():
        return tool_error("INVALID_EXPRESSION", "表达式不能为空")

    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return tool_error("INVALID_EXPRESSION", "表达式含有非法字符")

    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except ZeroDivisionError:
        return tool_error("DIVISION_BY_ZERO", "除数不能为零")
    except (SyntaxError, TypeError, ValueError, ArithmeticError):
        return tool_error("INVALID_EXPRESSION", "表达式格式错误或无法计算")
    except Exception:  # noqa: BLE001
        return tool_error("CALCULATION_FAILED", "计算失败")


def load_base_dir() -> Path | None:
    value = os.getenv("READ_BASE_DIR")
    if not value:
        return None

    try:
        return Path(value).resolve()
    except (OSError, RuntimeError):
        return None


BASE_DIR = load_base_dir()


MAX_FILE_LINES = 10
MAX_FILE_CHARS = 4000


def read_file(path: str) -> str:
    if BASE_DIR is None:
        return tool_error(
            "CONFIG_ERROR",
            "READ_BASE_DIR 未配置或配置无效",
        )
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
        return tool_error("OUTSIDE_BASE_DIR", "禁止读取目录外的文件")
    if not real_path.exists():
        return tool_error("FILE_NOT_FOUND", "文件不存在")
    if not real_path.is_file():
        return tool_error("NOT_A_FILE", "目标不是文件")

    try:
        content = real_path.read_text(encoding="utf-8")
    except PermissionError:
        return tool_error("PERMISSION_ERROR", "没有权限读取文件")
    except UnicodeDecodeError:
        return tool_error("Unicode_ERROR", "文件不是 UTF-8 文本")
    except OSError:
        return tool_error("READ_FAILED", "文件读取失败")

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
            "name": "calculator",
            "description": "计算数学表达式，支持加减乘除和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "如 '3*(4+5)'"}
                },
                "required": ["expression"],
                "additionalProperties": False,
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
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "读取 READ_BASE_DIR 配置目录内的 UTF-8 文本文件；"
                "相对路径以该目录为基准，最多返回前 10 行和 4000 个字符"
            ),
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件路径"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
]

REGISTRY: dict[str, Callable[..., str]] = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "read_file": read_file,
}


def test_tools_and_registry_are_consistent() -> None:
    schema_names = {item["function"]["name"] for item in TOOLS}
    assert schema_names == set(REGISTRY)
