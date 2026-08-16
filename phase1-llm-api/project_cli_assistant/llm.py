"""阶段 1 · 项目①：CLI 智能助手 · 客户端封装与流式处理

本文件职责：LLM 客户端的创建、后端切换、一次完整对话轮次（含工具调用闭环）的执行。

═══════════════════ 参考索引（行号已核实）═══════════════════
| 要写的            | 抄哪                                          |
|-------------------|-----------------------------------------------|
| 后端切换三件套    | ex03_switch_backend.py                        |
| 客户端单例        | chat_service/llm.py:55-67                     |
| 异常分层          | ex06_fewshot_vs_zeroshot.py:78-102  llm_call  |
| 非流式工具闭环    | ex08_more_tools.py:181-215  run()             |
| 并行工具执行      | tools.py:48-53 的设计提示（具体实现为新增）    |
| 流式取 delta      | ex05_stream_chat.py                           |
| **流式 + 工具**   | ❌ 没有参考，唯一的新东西                      |
════════════════════════════════════════════════════════════

需要提供的能力：

1. 按环境变量创建客户端，支持云端与本地 Ollama 切换
   - 三件套：`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`，**模型名不许硬编码**
   - 用 `@lru_cache(maxsize=1)` 做单例：每次新建 client 会新建连接池，
     高并发下打爆句柄
   - **一定要配 timeout**：SDK 默认 read timeout 是 600 秒，
     对交互式 CLI 来说等于卡死

2. 流式调用：边收 chunk 边把文本交给上层打印，同时把完整回复拼出来供回填历史

3. 工具调用闭环：识别 tool_calls → 交给 tools 层执行 → 结果以 role="tool" 回传
   → 继续下一轮。要点（ex08 踩过的）：
   - 循环必须有**轮次上限**，防止模型来回调工具停不下来
   - 到达上限时别静默返回 None，要带上失败原因
   - 未知工具名会 KeyError，要兜底，且返回值写给模型看
   - `tc.type == "function"` 收窄之后，**else 分支也必须回填一条 tool 消息**——
     协议要求每个 tool_call_id 都有对应响应，缺一个下轮请求就 400

4. 异常分层（ex06 那版最完整）：429 限流 / 超时 / 5xx / 4xx / 连接错，
   哪些该重试哪些不该，各自的降级行为

⚠️ 本文件最难的一处：流式模式下的 tool_calls

    流式时 `chunk.choices[0].delta.tool_calls` 是个**列表**，每个元素带 `index`。
    - `function.name` 通常只在第一个分片出现
    - `function.arguments` 是**逐段拼接**的字符串，你会收到 `{"ci`、`ty":"北`、`京"}`
    - 必须用 `index` 做 key 累积到一个 dict 里，**全部收完再 json.loads**
    - 中途解析必然失败（拿到的是半截 JSON）

    调试建议：**先把每个 chunk 的 delta 原样打印出来**，看清分片长什么样再写累积逻辑。
    别照着想象写——ex08 的破坏实验教过，先观察真实形态。

    这块建议**单独跑通再接进主循环**：它是唯一没有参考的部分，
    和其他模块的 bug 混在一起时你会分不清是累积逻辑错了还是历史回填错了。

设计要求：
- **本文件不 print**，把输出交给 main.py（职责单一，将来换 GUI 也不用改这里）
- 本文件不该知道"用户输入长什么样"，只接收结构化的参数
"""

# tools.py 会在导入时读取 READ_BASE_DIR，所以必须先执行 load_dotenv，再导入 tools。
# 这一个必要的延迟导入会打破 Ruff 的纯字母排序，仅对本文件关闭 I001。
# ruff: noqa: I001

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, cast

import httpx
import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam

# 这行来自 ex03_switch_backend.py。先加载 .env，后面才能读到 LLM_* 和
# READ_BASE_DIR。override=False 表示 PowerShell 临时设置的环境变量优先级更高。
load_dotenv(override=False)

from .tools import REGISTRY, TOOLS  # 必须在 load_dotenv 后导入


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


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise LLMError(f"缺少配置项：{name}", retryable=False)
    return value


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
            final_assistant = {"role": "assistant", "content": streamed.text}
            new_messages.append(final_assistant)
            return TurnResult(streamed.text, new_messages, usages)

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


def _translate_api_error(
    exc: openai.APIError | httpx.TransportError,
    partial_text: str,
    usage: Any | None,
) -> LLMError:
    """按 ex06_fewshot_vs_zeroshot.py 的顺序把 SDK 异常翻译成人话。"""

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
