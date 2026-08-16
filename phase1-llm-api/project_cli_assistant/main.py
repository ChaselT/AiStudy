"""阶段 1 · 项目①：CLI 智能助手 · 入口与对话循环

本文件职责：命令行入口、主对话循环、斜杠命令处理、把各模块粘起来。

═══════════════════ 参考索引（行号已核实）═══════════════════
| 要写的        | 抄哪                                              |
|---------------|---------------------------------------------------|
| 对话循环      | ex03_multi_turn.py                                |
| 流式打印      | ex05_stream_chat.py                               |
| 顶层异常处理  | chat_service/main.py 的 _stream_events            |
════════════════════════════════════════════════════════════

项目整体功能要求：

1. **多轮对话**：维护对话历史，支持连续追问，支持 `/clear` 清空
2. **流式输出**：回复逐字打印到终端，不是等全部生成完再输出
3. **至少 3 个工具调用**：get_current_time / calculator / read_file
4. **可切换后端**：环境变量在云端 API 与本地 Ollama 之间切换
5. **健壮性**：超时和重试配置齐全，429/超时/5xx 有区分处理，密钥走 `.env`，
   `/cost` 能打印本次会话累计 token 与估算花费

加分项：上下文超长时自动摘要压缩；工具并行调用；对话历史持久化到 JSON。

本文件负责的部分：

- 解析启动参数/环境变量，初始化各模块
- `while True` 主循环：读输入 → 调用 llm 层 → 流式打印 → 回填历史
- 斜杠命令：`/clear`、`/exit`、`/cost`，可自行扩展（`/history`、`/model`、`/save`…）
- 顶层异常处理：网络错误、Ctrl+C 要体面退出，**不能糊一屏栈**

要点：

- 流式打印用 `print(chunk, end="", flush=True)`。
  ⚠️ ex05 实测：`flush=True` 会吃掉约 45% 的耗时——测量工具影响被测对象。
  交互体验需要它，但**别拿带 flush 的代码去测性能**
- 流式结束后要把**完整回复**回填历史，不是把 chunk 一个个塞进去
- 工具调用发生时给用户一点反馈（比如打印 `[调用 get_current_time]`），
  否则界面会静默卡几秒，用户以为死了
- Ctrl+C 捕获 `KeyboardInterrupt`，正常退出并可选择保存历史

写完自查：
- [ ] 换个 `.env` 里的 `LLM_MODEL` 就能切模型，代码一行不用改
- [ ] 断网时报错信息是人话，不是一屏 traceback
- [ ] `/clear` 之后模型确实失忆（问它上一句说了什么）
- [ ] 三个工具都被正确触发过至少一次
- [ ] 长对话（20 轮以上）不会因为上下文超限而崩
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

# README 目前给出的启动命令是：uv run project_cli_assistant/main.py。
# 直接运行文件时，Python 默认只把 project_cli_assistant/ 放进模块搜索路径，找不到
# 它的父目录。把项目根目录补进去后，直接运行和 `python -m` 两种方式都能使用。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_cli_assistant.history import (
    DEFAULT_HISTORY_FILE,
    ChatHistory,
)
from project_cli_assistant.llm import (
    LLMError,
    close_llm_client,
    run_turn,
)

# 自动摘要阈值按 history.py 的默认建议设置。最近 3 轮保留原文，较早内容才总结。
# 这两个值写成常量，学习时容易找到；以后不同模型需要不同阈值时再改为环境变量。
SUMMARY_TRIGGER_TOKENS = 4000
KEEP_RECENT_TURNS = 3

SUMMARY_SYSTEM_PROMPT = """你是对话摘要助手。
请把用户提供的旧对话压缩成简洁、准确的中文摘要，保留：
1. 用户明确提供的事实、偏好和约束；
2. 已经作出的决定与尚未完成的事项；
3. 后续回答仍然需要的重要工具结果。
只输出摘要正文，不要调用工具，不要添加标题。"""


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


def _add_usages(history: ChatHistory, usages: Sequence[Any]) -> None:
    """累计工具闭环内每一次模型请求的 token 用量。"""

    for usage in usages:
        history.add_usage(usage)


def _read_price(name: str) -> float | None:
    """读取可选的每百万 token 单价；没配或配置错误时返回 None。"""

    value = os.getenv(name, "").strip()
    if not value:
        return None
    try:
        price = float(value)
    except ValueError:
        return None
    return price if price >= 0 else None


def _show_cost(history: ChatHistory) -> None:
    """实现 `/cost`：始终显示 token；配置了单价时再估算费用。"""

    print(
        "累计 token："
        f"输入 {history.prompt_tokens}，"
        f"输出 {history.completion_tokens}，"
        f"合计 {history.total_tokens}"
    )

    # 单价不按模型名硬编码，因为云端、中转站和本地 Ollama 的价格都可能不同。
    input_price = _read_price("LLM_INPUT_PRICE_PER_MILLION")
    output_price = _read_price("LLM_OUTPUT_PRICE_PER_MILLION")
    if input_price is None or output_price is None:
        print("估算费用：未配置模型单价")
        return

    estimated = history.cost(input_price, output_price)
    print(f"估算费用：{estimated:.6f}")


def _save_history(history: ChatHistory, path: str | Path) -> None:
    """保存历史；磁盘错误只提示，不让整个 CLI 打出堆栈。"""

    try:
        history.save(path)
    except (OSError, TypeError, ValueError) as exc:
        print(f"[警告] 对话历史保存失败：{exc}")


def _summarize(
    old_messages: list[dict[str, Any]],
    history: ChatHistory,
) -> str:
    """调用 llm.run_turn 生成摘要，同时记录摘要请求本身的 token。

    旧消息先序列化成 JSON 放进一条 user 消息，避免拆散其中的工具调用配对。
    摘要过程传入空的文本回调，因此不会把摘要草稿流式打印到正常回答中。
    """

    summary_messages = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(old_messages, ensure_ascii=False),
        },
    ]

    try:
        result = run_turn(summary_messages, lambda _chunk: None)
    except LLMError as exc:
        # 即使摘要最终失败，之前已完成的请求也真实产生了 token 消耗。
        _add_usages(history, exc.usages)
        raise

    _add_usages(history, result.usages)
    return result.reply


def _compress_history(history: ChatHistory) -> None:
    """需要时压缩早期历史；失败则降级到截断KEEP_RECENT_TURNS。"""

    try:
        history.compress_if_needed(
            lambda messages: _summarize(messages, history),
            max_prompt_tokens=SUMMARY_TRIGGER_TOKENS,
            keep_recent_turns=KEEP_RECENT_TURNS,
        )
    except (LLMError, ValueError, TypeError) as exc:
        # compress_if_needed 只有拿到非空摘要后才替换消息，失败不会破坏原历史。
        history.trim(KEEP_RECENT_TURNS)
        print(f"\n[提示] 自动摘要失败，已经截取最近{KEEP_RECENT_TURNS}轮对话：{exc}")


def _load_history(path: str | Path) -> ChatHistory | None:
    """启动时恢复历史；损坏文件不自动覆盖，交给用户检查。"""

    try:
        return ChatHistory.load_or_create(path)
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
    ) as exc:
        print(f"[错误] 对话历史读取失败：{exc}")
        return None


def main(history_path: str | Path = DEFAULT_HISTORY_FILE) -> None:
    """运行 CLI 对话循环。测试可传临时 history_path，避免写默认 data 目录。"""

    history = _load_history(history_path)
    if history is None:
        # 读取失败时不要创建新历史并覆盖可能仍可人工修复的原文件。
        return

    try:
        # while True + input() + /exit 的整体结构照 ex03_multi_turn.py 写。
        while True:
            text = input("你> ").strip()
            if not text:
                continue

            command = text.lower()
            if command in {"/exit", "quit", "exit"}:
                break
            if command == "/clear":
                history.clear()
                _save_history(history, history_path)
                print("对话历史已清空。")
                continue
            if command == "/cost":
                _show_cost(history)
                continue
            if command.startswith("/"):
                print(f"未知命令：{text}")
                continue

            user_message = {"role": "user", "content": text}

            # 不先 append 到真实历史。只有整轮成功后，才一次提交 user、
            # assistant(tool_calls)、tool 和最终 assistant，避免失败留下半轮消息。
            request_messages = [*history.messages, user_message]
            try:
                result = run_turn(
                    request_messages,
                    _print_text,
                    _print_tool,
                )
            except LLMError as exc:
                # 处理方式对应 chat_service/main.py::_stream_events：异常转成人话，
                # 当前轮结束但主循环继续；partial_text 已经显示过，不再重复打印或保存。
                print(f"\n[错误] {exc}")
                _add_usages(history, exc.usages)
                if exc.usages:
                    _save_history(history, history_path)
                continue

            print()  # 最后一个流式分片使用 end=""，完整成功后补一个换行。

            # ex03_multi_turn.py 只回填一条 assistant；本项目还可能有工具消息，
            # 因此必须完整保存 result.new_messages，不能只保存 result.reply。
            history.messages.extend([user_message, *result.new_messages])
            _add_usages(history, result.usages)

            # 只有本轮拿到了真实 usage，才使用最新 prompt_tokens 判断是否压缩。
            # 某些本地兼容后端不返回 usage，此时跳过，避免误用上一次的旧数值。
            if result.usages:
                _compress_history(history)

            # 每个成功轮次立即落盘，程序异常退出时最多只损失正在生成的这一轮。
            _save_history(history, history_path)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C 或输入流结束都属于正常退出，不显示 traceback。
        print("\n已退出。")
    finally:
        _save_history(history, history_path)
        try:
            close_llm_client()
        except Exception as exc:  # noqa: BLE001
            # 关闭连接池失败不应覆盖正常退出；这里只显示简短提示。
            print(f"[警告] LLM 客户端关闭失败：{exc}")


def _parse_args() -> argparse.Namespace:
    """只保留一个最实用的启动参数：指定历史 JSON 文件。"""

    parser = argparse.ArgumentParser(description="CLI 智能助手")
    parser.add_argument(
        "--history",
        type=Path,
        default=DEFAULT_HISTORY_FILE,
        help="对话历史 JSON 文件路径",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    main(arguments.history)
