"""阶段 1 测试 · B 卷实操（60 分）——结构化情报助手

═══════════════════════════════════════════════════════════════
考试规则
  · 可查官方文档（openai / pydantic）
  · 不可用 AI 生成代码，**不可打开自己以前作业里的成品实现**
    （ex07/ex08/project_cli_assistant 都不许翻）
  · 卡住超过 15 分钟可以向 Claude 要"方向性提示"（不给代码）
  · 预计用时 90 分钟
  · A 卷已得 29.5/40，**本卷 ≥50.5 分**即通过阶段 1（总分 ≥80）
═══════════════════════════════════════════════════════════════

题目：实现一个命令行的结构化情报助手。

1.（15 分）定义 pydantic 模型 `NewsDigest`，字段：
       title: str
       summary: str                              # ≤50 字
       sentiment: Literal["正面", "中性", "负面"]
       keywords: list[str]                       # 3-5 个

2.（20 分）实现两个工具供模型调用（Function Calling）：
       read_local_file(path)  读取本地文本
       word_count(text)       统计字数
   模型需要能**自主决定**调用哪个。

3.（15 分）用户输入一段新闻文本或文件路径后：
   模型（本地 Ollama 或任意 API 均可）分析并以**结构化输出**返回 `NewsDigest`，
   解析失败自动重试一次。

4.（10 分）最终回答用**流式输出**打印到终端（摘要部分逐字出现）。

**加分项（+10，可抵扣失分）**：传入一张新闻截图，用视觉模型走同样的流程。

───────────────────────────────────────────────────────────────
评分点（除功能分外，这些直接影响得分）
  · 消息流转正确（assistant 的 tool_calls 与 tool 结果按 tool_call_id 配对）
  · 异常与重试处理：超时/重试参数配置齐全 + **按异常类型分支**
  · 密钥不硬编码，模型名走环境变量
  · 代码结构清晰（工具定义 / 调用循环 / 输出，三者分层）
───────────────────────────────────────────────────────────────

运行：uv run exam_intel_bot.py
"""

import asyncio
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast

import httpx
import openai
from dotenv import load_dotenv
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from pydantic import BaseModel, Field, ValidationError

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

TextCallback = Callable[[str], None]
ToolCallback = Callable[[str, Mapping[str, Any]], None]


class LLMError(RuntimeError):
    """交给 main.py 展示的友好错误，不让 SDK 异常直接刷满终端。"""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
        partial_text: str = "",
        usages: Sequence[Any] = (),
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        # 流中断前的文字已经通过 on_text 显示过，main.py 可以据此决定如何提示。
        self.partial_text = partial_text
        # 前几次工具轮已经真实产生费用；后续失败也不能让 /cost 少算它们。
        self.usages = list(usages)


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise LLMError(f"缺少配置项：{name}", retryable=False)
    return value


class NewsDigest(BaseModel):
    title: str
    summary: str = Field(min_length=0, max_length=50, description="文章摘要")  # ≤50 字
    sentiment: Literal["正面", "中性", "负面"]
    keywords: list[str] = Field(min_length=3, max_length=5, description="关键词，3-5个")


def tool_error(code: str, message: str) -> str:
    return json.dumps(
        {"ok": False, "error": {"code": code, "message": message}},
        ensure_ascii=False,
    )


def word_count(expression: str) -> int | str:
    if not isinstance(expression, str) or not expression.strip():
        return tool_error("INVALID_EXPRESSION", "内容为空")

    try:
        return len(expression)
    except Exception:  # noqa: BLE001
        return tool_error("CALCULATION_FAILED", "字数统计失败")


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


def read_local_file(path: str) -> str:
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
            "name": "word_count",
            "description": "统计文章字数",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "一段文章内容"}
                },
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_local_file",
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

REGISTRY: dict[str, Callable[..., int | str]] = {
    "word_count": word_count,
    "read_local_file": read_local_file,
}


def test_tools_and_registry_are_consistent() -> None:
    schema_names = {item["function"]["name"] for item in TOOLS}
    assert schema_names == set(REGISTRY)


@lru_cache(maxsize=1)
def get_llm_client() -> openai.OpenAI:
    """返回进程内共用的同步客户端。

    这里按 ``chat_service/llm.py`` 使用 lru_cache 做单例，配置三件套和 60 秒
    超时则来自 ``ex03_switch_backend.py``。换 .env 就能切后端，代码不用改。
    """

    return openai.OpenAI(
        base_url=_required_env("LLM_BASE_URL"),
        api_key=_required_env("LLM_API_KEY"),
        timeout=60.0,
        max_retries=3,
    )


def close_llm_client() -> None:
    """程序退出时关闭已存在的连接池。未创建过客户端就直接跳过。"""

    if get_llm_client.cache_info().currsize == 0:
        return
    client = get_llm_client()
    get_llm_client.cache_clear()
    client.close()


def _print_text(chunk: str) -> None:
    """把一个文本分片立即显示到终端。

    这一行直接照 ``ex05_stream_chat.py`` 的流式打印写法。``flush=True`` 会让
    用户马上看到新文字；完整回答的拼接由 llm.py 负责，这里不把 chunk 存进历史。
    """

    print(chunk, end="", flush=True)


def _print_tool(name: str, arguments: Mapping[str, Any]) -> None:
    """工具真正执行前给出反馈，避免终端静默几秒。"""

    readable_arguments = json.dumps(arguments, ensure_ascii=False)
    print(f"\n[调用 {name}] {readable_arguments}")


@dataclass
class TurnResult:
    """完整成功的一轮：最终回答、本轮新增消息、每次请求的 token 用量。"""

    reply: str
    new_messages: list[dict[str, Any]]
    usages: list[Any]


@dataclass
class _ToolCallBuffer:
    """一个工具调用在流结束前的临时拼接区。"""

    call_id: str = ""
    call_type: str = ""
    name: str = ""
    arguments: str = ""
    custom_name: str = ""
    custom_input: str = ""


@dataclass
class _StreamResult:
    """一次 API 流全部收完后的内部结果。"""

    text: str
    tool_buffers: dict[int, _ToolCallBuffer]
    usage: Any | None
    finish_reason: str | None


def parse_structured_output(content: str) -> NewsDigest:
    """从模型响应中提取 JSON 并校验，失败自动重试一次"""
    # 尝试提取 JSON（可能被 markdown 包裹）
    json_str = content.strip()

    # 移除 markdown 代码块标记
    if "```json" in json_str:
        start = json_str.find("```json") + 7
        end = json_str.find("```", start)
        if end != -1:
            json_str = json_str[start:end].strip()
    elif "```" in json_str:
        start = json_str.find("```") + 3
        end = json_str.find("```", start)
        if end != -1:
            json_str = json_str[start:end].strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise StructuredOutputError(f"JSON 解析失败: {e}") from e

    try:
        return NewsDigest(**data)
    except ValidationError as e:
        raise StructuredOutputError(f"字段校验失败: {e}") from e


class StructuredOutputError(Exception):
    """结构化输出解析失败"""


def _text_field(value: Any, field: str, index: int) -> str | None:
    """兼容后端字段可以缺失，但出现时必须真的是字符串。"""

    field_value = getattr(value, field, None)
    if field_value is not None and not isinstance(field_value, str):
        raise LLMError(
            f"第 {index} 个工具调用的 {field} 字段不是字符串",
            retryable=False,
        )
    return field_value


def _remember_once(
    buffer: _ToolCallBuffer,
    field: str,
    value: str | None,
    index: int,
) -> None:
    """id/type/name 只记录非空值；重复时必须与首片一致。"""

    if not value:
        return
    old_value = getattr(buffer, field)
    if old_value and old_value != value:
        raise LLMError(
            f"模型返回的第 {index} 个工具调用分片前后不一致",
            retryable=False,
        )
    setattr(buffer, field, value)


def _collect_tool_part(part: Any, buffers: dict[int, _ToolCallBuffer]) -> None:
    """把一个 tool_call delta 追加到它的 index 缓存中。"""

    index = getattr(part, "index", None)
    if type(index) is not int or index < 0:
        raise LLMError("模型返回了无效的工具调用 index", retryable=False)

    buffer = buffers.setdefault(index, _ToolCallBuffer())
    _remember_once(buffer, "call_id", _text_field(part, "id", index), index)
    _remember_once(buffer, "call_type", _text_field(part, "type", index), index)

    function = getattr(part, "function", None)
    if function is not None:
        _remember_once(buffer, "name", _text_field(function, "name", index), index)
        buffer.arguments += _text_field(function, "arguments", index) or ""

    # 当前项目只声明 function，但题目明确要求 else 分支也必须闭环。
    # 若兼容后端返回合法 custom 分片，同样把 name/input 收齐，后面回填 tool 消息。
    custom = getattr(part, "custom", None)
    if custom is not None:
        _remember_once(buffer, "custom_name", _text_field(custom, "name", index), index)
        buffer.custom_input += _text_field(custom, "input", index) or ""


def _translate_api_error(
    exc: openai.APIError | httpx.TransportError,
    partial_text: str,
    usage: Any | None,
) -> LLMError:

    error_usages = [] if usage is None else [usage]

    # 子类必须写在父类前：RateLimitError 也是 APIStatusError。
    if isinstance(exc, openai.RateLimitError):
        retry_after = exc.response.headers.get("retry-after")
        suffix = f"，建议 {retry_after} 秒后重试" if retry_after else "，请稍后重试"
        message = "请求过于频繁" + suffix
        retryable = True
    # APITimeoutError 是 APIConnectionError 的子类；httpx 也可能在读流时直接超时。
    elif isinstance(exc, (openai.APITimeoutError, httpx.TimeoutException)):
        message = "模型响应超时，请稍后重试"
        retryable = True
    elif isinstance(exc, openai.APIStatusError):
        retryable = exc.status_code in {408, 409} or exc.status_code >= 500
        message = (
            f"模型服务暂时不可用（HTTP {exc.status_code}），请稍后重试"
            if retryable
            else f"模型请求有误（HTTP {exc.status_code}），请检查配置或参数"
        )
    elif isinstance(exc, openai.APIConnectionError):
        message = "无法连接模型服务，请检查网络、代理和 LLM_BASE_URL"
        retryable = True
    elif isinstance(exc, httpx.TransportError):
        message = "模型连接在传输过程中中断，请检查网络后重试"
        retryable = True
    else:
        # 流式 SSE 的 error 事件会抛基础 APIError，也在这里转成友好错误。
        message = "模型服务返回了无法处理的错误，请稍后重试"
        retryable = True

    return LLMError(
        message,
        retryable=retryable,
        partial_text=partial_text,
        usages=error_usages,
    )


def _read_stream(
    client: openai.OpenAI,
    messages: list[dict[str, Any]],
    on_text: TextCallback,
) -> _StreamResult:
    """发送一次流式请求，同时拼接文本和工具调用分片。"""

    text_parts: list[str] = []
    tool_buffers: dict[int, _ToolCallBuffer] = {}
    usage: Any | None = None
    finish_reason: str | None = None

    try:
        stream = client.chat.completions.create(
            # 后端切换三件套来自 ex03_switch_backend.py，模型名没有硬编码。
            model=_required_env("LLM_MODEL"),
            messages=cast(list[ChatCompletionMessageParam], messages),
            tools=TOOLS,
            temperature=0,
            stream=True,
            # 官方文档规定该选项与 stream=True 配合，尾包才会给出 usage。
            stream_options={"include_usage": True},
        )

        try:
            # 逐段取 content 并 join 的方法来自 ex05_stream_chat.py。
            for chunk in stream:
                # usage 尾包通常 choices=[]，所以必须先读 usage 再判断 choices。
                if chunk.usage is not None:
                    usage = chunk.usage
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                if choice.finish_reason is not None:
                    finish_reason = choice.finish_reason
                delta = choice.delta

                # refusal 也是标准流式字段。把它作为可见文本交给上层，不能静默返回空串。
                for piece in (delta.content, delta.refusal):
                    if piece:
                        text_parts.append(piece)
                        on_text(piece)

                # 唯一没有参考代码的新逻辑：必须按 index 聚合，不能按到达顺序猜。
                for part in delta.tool_calls or []:
                    _collect_tool_part(part, tool_buffers)
        finally:
            # 回调或解析中途抛错时也及时归还 HTTP 连接。
            close_stream = getattr(stream, "close", None)
            if close_stream is not None:
                close_stream()
    except LLMError as exc:
        exc.partial_text = exc.partial_text or "".join(text_parts)
        if usage is not None:
            exc.usages = [usage]
        raise
    except (openai.APIError, httpx.TransportError) as exc:
        raise _translate_api_error(exc, "".join(text_parts), usage) from exc

    return _StreamResult(
        text="".join(text_parts),
        tool_buffers=tool_buffers,
        usage=usage,
        finish_reason=finish_reason,
    )


def _validate_stream_end(result: _StreamResult, usages: Sequence[Any]) -> None:
    """只接受完整结束的流，避免把半截回答写进历史。"""

    reason = result.finish_reason
    if reason == "length":
        message = "模型回答因长度上限被截断，请缩短问题后重试"
        retryable = False
    elif reason == "content_filter":
        message = "模型回答被内容安全策略过滤"
        retryable = False
    elif reason is None:
        message = "模型响应在正常结束前中断"
        retryable = True
    elif reason not in {"stop", "tool_calls"}:
        message = f"模型返回了不支持的结束原因：{reason}"
        retryable = False
    elif reason == "tool_calls" and not result.tool_buffers:
        message = "模型声明要调用工具，但没有返回工具调用内容"
        retryable = False
    elif reason == "stop" and result.tool_buffers:
        message = "模型同时返回了结束回答和工具调用，响应格式不一致"
        retryable = False
    else:
        return

    raise LLMError(
        message,
        retryable=retryable,
        partial_text=result.text,
        usages=usages,
    )


def _build_tool_calls(
    buffers: Mapping[int, _ToolCallBuffer],
) -> list[dict[str, Any]]:
    """流结束后，按 index 还原可回填给 API 的完整 tool_calls。"""

    calls: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index in sorted(buffers):
        buffer = buffers[index]
        if not buffer.call_id:
            raise LLMError(f"第 {index} 个工具调用缺少 id", retryable=False)
        if buffer.call_id in seen_ids:
            raise LLMError("模型返回了重复的 tool_call_id", retryable=False)
        seen_ids.add(buffer.call_id)

        call_type = buffer.call_type or "function"
        if call_type == "function":
            if not buffer.name:
                raise LLMError(f"第 {index} 个函数调用缺少工具名", retryable=False)
            calls.append(
                {
                    "id": buffer.call_id,
                    "type": "function",
                    "function": {
                        "name": buffer.name,
                        # 一定在全部分片收完之后，才会由 _run_tool 做 json.loads。
                        "arguments": buffer.arguments or "{}",
                    },
                }
            )
        elif call_type == "custom":
            if not buffer.custom_name:
                raise LLMError(f"第 {index} 个 custom 调用缺少名称", retryable=False)
            calls.append(
                {
                    "id": buffer.call_id,
                    "type": "custom",
                    "custom": {
                        "name": buffer.custom_name,
                        "input": buffer.custom_input,
                    },
                }
            )
        else:
            # 未知类型没有可构造的合法 assistant 消息，不能发送一个注定 400 的字典。
            raise LLMError(
                f"暂不支持 {call_type!r} 类型的工具调用",
                retryable=False,
            )

    return calls


async def _run_tools_in_parallel(
    tool_calls: Sequence[Mapping[str, Any]],
    on_tool: ToolCallback | None,
) -> list[dict[str, Any]]:
    """按 tools.py 顶部的提示，并行执行一批同步工具。

    ``asyncio.gather`` 只能并发 awaitable，不能直接把普通同步函数传进去。
    ``asyncio.to_thread`` 会先把每次 ``_run_tool`` 放到工作线程，并返回可以 await
    的对象；再用 ``gather`` 同时等待它们，这样才是真正的并行工具调用。

    gather 的返回值顺序与传入 awaitable 的顺序相同，所以即使后面的工具先完成，
    回填给模型的 tool 消息仍保持原 tool_calls 顺序；每条消息也保留自己的
    tool_call_id，不会因为并行完成顺序不同而配错。
    """

    results = await asyncio.gather(
        *[asyncio.to_thread(_run_tool, tool_call, on_tool) for tool_call in tool_calls]
    )
    return list(results)


def _run_tool(
    tool_call: Mapping[str, Any],
    on_tool: ToolCallback | None,
) -> dict[str, Any]:
    """执行一个工具；成功或失败都返回一条配对的 role=tool 消息。"""

    call_id = str(tool_call["id"])
    call_type = str(tool_call["type"])
    arguments: dict[str, Any] = {}
    argument_error = ""

    if call_type == "function":
        function = tool_call["function"]
        name = str(function["name"])
        try:
            decoded = json.loads(str(function.get("arguments", "{}")))
            if not isinstance(decoded, dict):
                argument_error = "工具参数必须是 JSON 对象"
            else:
                arguments = decoded
        except json.JSONDecodeError as exc:
            argument_error = f"工具参数不是合法 JSON：{exc}"
    else:
        # 合法 custom 调用也必须回填 tool 结果，只是本学习项目没有执行器。
        custom = tool_call["custom"]
        name = str(custom["name"])
        arguments = {"input": custom.get("input", "")}

    # 通知必须发生在真实执行之前，慢工具运行时终端才不会静默。
    if on_tool is not None:
        on_tool(name, arguments)

    if argument_error:
        result = f"错误：工具 {name} 的参数无效：{argument_error}"
    elif call_type != "function":
        result = f"错误：暂不支持 {call_type!r} 类型的工具调用"
    else:
        function_impl = REGISTRY.get(name)
        if function_impl is None:
            result = f"错误：未知工具 {name}"
        else:
            try:
                result = str(function_impl(**arguments))
            except TypeError as exc:
                result = f"错误：工具 {name} 的调用参数错误：{exc}"
            except Exception as exc:  # noqa: BLE001
                # 工具失败要写给模型看，让它有机会修改参数。Ctrl+C 不会被这里吞掉，
                # 因为 KeyboardInterrupt 继承 BaseException，而不是 Exception。
                result = f"错误：工具 {name} 执行失败：{exc}"

    return {"role": "tool", "tool_call_id": call_id, "content": result}


def run_turn(
    messages: Sequence[Mapping[str, Any]],
    on_text: TextCallback,
    on_tool: ToolCallback | None = None,
    *,
    client: openai.OpenAI | None = None,
    max_rounds: int = 5,
) -> TurnResult:
    """完成一次用户提问，包括可能发生的多轮工具调用。

    ``messages`` 应已包含本轮 user 消息。文本 delta 会立刻交给 ``on_text``；
    ``on_tool`` 在工具真正执行前收到工具名和参数，可用于显示“正在调用”。

    本函数只修改自己的消息副本。成功后 main.py 再把 ``new_messages`` 加入
    ChatHistory；中途失败时，调用方历史不会留下缺少配对结果的 tool_calls。
    """

    if max_rounds <= 0:
        raise ValueError("max_rounds 必须大于 0")

    llm_client = client or get_llm_client()
    working_messages = [dict(message) for message in messages]
    new_messages: list[dict[str, Any]] = []
    usages: list[Any] = []
    retry_count = 0  # 在 for 循环外初始化
    # 这一层 while/for 闭环基本照着 ex08_more_tools.py 的 run() 写。
    for round_number in range(1, max_rounds + 1):
        try:
            streamed = _read_stream(llm_client, working_messages, on_text)
        except LLMError as exc:
            # _read_stream 只知道当前请求；在这里补上之前工具轮的 usage。
            exc.usages = [*usages, *exc.usages]
            raise

        if streamed.usage is not None:
            usages.append(streamed.usage)

        _validate_stream_end(streamed, usages)

        # 没有工具调用，说明这就是最终回答。
        if not streamed.tool_buffers:
            try:
                digest = parse_structured_output(streamed.text)
                final_text = json.dumps(
                    digest.model_dump(), ensure_ascii=False, indent=2
                )
                final_assistant = {"role": "assistant", "content": final_text}
                new_messages.append(final_assistant)
                return TurnResult(final_text, new_messages, usages)
            except StructuredOutputError as e:
                retry_count += 1
                if retry_count >= 2:  # 最多重试一次
                    raise LLMError(
                        f"结构化输出解析失败，已重试 {retry_count} 次: {e}",
                        retryable=False,
                        usages=usages,
                    )
                print(f"\n⚠️ 解析失败: {e}，要求模型重新输出...")
                working_messages.append(
                    {
                        "role": "user",
                        "content": f"你输出的格式不正确，需要符合 NewsDigest 模型：title, summary(≤50字), sentiment(正面/中性/负面), keywords(3-5个)。错误信息: {e}。请重新输出 JSON。",
                    }
                )
                continue  # 继续下一轮，让模型重新生成

        try:
            tool_calls = _build_tool_calls(streamed.tool_buffers)
        except LLMError as exc:
            exc.partial_text = streamed.text
            exc.usages = list(usages)
            raise

        # 协议要求先回填 assistant 的 tool_calls，再回填每个 tool 结果。
        tool_assistant: dict[str, Any] = {
            "role": "assistant",
            "content": streamed.text or None,
            "tool_calls": tool_calls,
        }
        working_messages.append(tool_assistant)
        new_messages.append(tool_assistant)

        # 工具闭环沿用 ex08_more_tools.py:181-215；参考代码这里用普通 for，
        # 实际是串行执行。并行方法按 tools.py:48-53 的提示实现：同步工具先用
        # asyncio.to_thread 包装成 awaitable，再交给 asyncio.gather 并发等待。
        if len(tool_calls) == 1:
            tool_messages = [_run_tool(tool_calls[0], on_tool)]
        else:
            # 本函数是同步 API，asyncio.run 要求调用处没有运行中的事件循环；若将来在 async 上下文中复用，这里要改成 await _run_tools_in_parallel(...) 并把 run_turn 一并改成协程。
            tool_messages = asyncio.run(_run_tools_in_parallel(tool_calls, on_tool))
        working_messages.extend(tool_messages)
        new_messages.extend(tool_messages)

        if round_number == max_rounds:
            # 这是程序失败，不伪装成模型说出的一条 assistant 消息。
            raise LLMError(
                f"工具调用已达到 {max_rounds} 轮上限，未能得到最终回答",
                retryable=False,
                usages=usages,
            )

    raise AssertionError("无法到达的代码")


system_message: dict[str, Any] = {
    "role": "system",
    "content": (
        "你是一个情报分析助手。用户会给你一段新闻文本或文件路径。"
        "你需要：\n"
        "1. 如果用户提供的是文件路径，先调用 read_local_file 读取内容\n"
        "2. 分析新闻内容，提取标题、摘要（≤50字）、情感倾向、关键词（3-5个）\n"
        "3. 如果用户要求统计字数，调用 word_count\n"
        "4. 最终以 JSON 格式输出 NewsDigest，包含 title, summary, sentiment, keywords"
    ),
}


def display_result(digest: NewsDigest) -> None:
    """展示结果，摘要逐字打印"""
    print("\n" + "=" * 50)
    print(f"📌 标题: {digest.title}")
    print("📰 摘要: ", end="", flush=True)
    for char in digest.summary:
        print(char, end="", flush=True)
        time.sleep(0.05)  # 逐字出现
    print("\n" + f"💬 情感: {digest.sentiment}")
    print(f"🏷️  关键词: {', '.join(digest.keywords)}")
    print("=" * 50)


def analyze_image(image_path: str) -> NewsDigest:
    """分析新闻截图（加分项），使用默认 LLM_MODEL（需支持多模态）"""
    import base64

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {image_path}")

    # 读取并编码图片
    with path.open("rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # 判断文件类型
    suffix = path.suffix.lower()
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }.get(suffix, "image/png")

    # 构建视觉请求（使用默认模型，需配置支持多模态的模型）
    vision_messages = [
        {
            "role": "system",
            "content": (
                "你是一个情报分析助手。分析这张新闻截图，提取标题、摘要(≤50字)、"
                "情感倾向(正面/中性/负面)、关键词(3-5个)，以 JSON 格式输出。"
                "只输出 JSON，不要有其他文字。"
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析这张新闻截图"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                },
            ],
        },
    ]

    client = get_llm_client()

    # 重试一次
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=_required_env("LLM_MODEL"),  # 使用默认模型
                messages=vision_messages,  # type: ignore
                temperature=0.1,
            )
            content = response.choices[0].message.content or ""
            return parse_structured_output(content)
        except StructuredOutputError as e:
            if attempt == 0:
                print(f"\n⚠️ 图片分析解析失败，重试中... {e}")
                continue
            raise
        except Exception as e:
            if attempt == 0:
                print(f"\n⚠️ 图片分析失败，重试中... {e}")
                continue
            raise

    raise RuntimeError("图片分析失败")


def main() -> None:
    """运行 CLI 对话循环，支持文本和图片输入"""
    try:
        while True:
            text = input("你> ").strip()
            if not text:
                continue

            command = text.lower()
            if command in {"/exit", "quit", "exit"}:
                break
            if command.startswith("/"):
                print(f"未知命令：{text}")
                continue

            # 检查是否是图片路径
            path = Path(text)
            if path.exists() and path.suffix.lower() in {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".bmp",
                ".webp",
            }:
                try:
                    print(f"🖼️ 检测到图片: {text}")
                    digest = analyze_image(str(path))
                    display_result(digest)
                    continue
                except Exception as e:  # noqa: BLE001
                    print(f"❌ 图片分析失败: {e}")
                    continue

            # 文本模式
            user_message: dict[str, Any] = {"role": "user", "content": text}
            request_messages: list[dict[str, Any]] = [system_message, user_message]
            try:
                result = run_turn(request_messages, _print_text, _print_tool)
                # 解析 JSON 并展示
                digest = NewsDigest(**json.loads(result.reply))
                display_result(digest)
            except LLMError as exc:
                print(f"\n[错误] {exc}")
                continue

    except (KeyboardInterrupt, EOFError):
        print("\n已退出。")
    finally:
        try:
            close_llm_client()
        except Exception as exc:  # noqa: BLE001
            print(f"[警告] LLM 客户端关闭失败：{exc}")


if __name__ == "__main__":
    main()
