"""阶段 1 · 项目①：CLI 智能助手 · 历史管理（截断/摘要/持久化）

本文件职责：维护 messages 列表的增删改查、控制上下文长度、统计 token、可选的落盘与恢复。

═══════════════════ 参考索引（行号已核实）═══════════════════
| 要写的        | 抄哪                                              |
|---------------|---------------------------------------------------|
| 截断          | ex02_usage_watch.py:50  trim_history              |
| token 累计    | ex02_usage_watch.py / ex03_switch_backend.py      |
| 多轮消息结构  | ex03_multi_turn.py                                |
════════════════════════════════════════════════════════════

需要提供的能力：

1. 追加消息、读取历史
2. 清空历史（供 `/clear` 使用，**注意 system 消息要保留**）
3. 截断：保留 system + 最近 N 条
4. token 累计（供 `/cost` 使用）
5. 加分项 1：上下文超长时自动**摘要压缩**——把早期对话交给模型总结成一段摘要，
   用摘要替换掉那批消息（想清楚摘要放在 messages 的哪个位置、以什么角色存在）
6. 加分项 2：对话历史持久化到 JSON 文件，下次启动可恢复

⚠️ 本文件最容易踩的坑：截断会破坏工具调用消息的配对

    assistant 的 tool_calls 消息和对应的 tool 结果消息**必须成对存在**。
    截断截到一半（留下了 tool_calls 却丢了 tool 结果，或反过来），
    下一次请求 API 直接报错。

    ex02 的 trim_history 是在还没有工具调用的阶段写的，**它没处理这个情况**，
    直接搬过来会在工具闭环跑通后炸掉。你得自己加配对保护。

    建议：截断时以「完整的一轮」为单位，而不是以「消息条数」为单位。

按 token 数决定何时压缩，别数消息条数（ex02 已实证"按条数截断约束不了成本"）。
怎么数 token：

  ✅ **推荐：直接用上一轮响应里的 `usage.prompt_tokens`**
     ——这是服务端给的实测值，最准，且零额外成本（你每轮本来就拿到了）
  ⚠️ tiktoken 是 OpenAI 的分词器，**数不准本地 qwen**（实测同一句话差异明显），
     只能当粗估，且要知道偏差方向
  ⚠️ 按字符数粗估最糙，但跨模型不会错得离谱

持久化：
- 路径别写死绝对路径，存到 `data/` 下（已被根 .gitignore 忽略，聊天记录不进 Git）
- 存之前想清楚：pydantic 对象、datetime 这些不能直接 json.dump
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

DEFAULT_HISTORY_FILE = (
    # 用当前文件定位项目根目录，不依赖用户从哪个目录启动程序。
    # 最终路径为：phase1-llm-api/data/cli_assistant_history.json
    Path(__file__).resolve().parent.parent / "data" / "cli_assistant_history.json"
)

# 摘要也使用 system 消息保存，但加固定前缀，方便后面识别它。
# messages 中的顺序会是：初始 system -> 摘要 system -> 最近几轮对话。
SUMMARY_PREFIX = "以下是之前对话的摘要：\n"


class ChatHistory:
    """保存一段 CLI 对话的消息、token 用量和持久化数据。

    OpenAI 的 Chat Completions API 本身不记忆历史。每次请求时，都要把
    ``messages`` 完整传给模型。这个类就是专门维护该列表的简单容器。

    ``messages`` 的基本结构如下：

    - system：规定助手身份，始终放在第一条；
    - user：用户本轮问题；
    - assistant：模型回答，或者包含 ``tool_calls`` 的工具调用请求；
    - tool：本地工具执行结果，通过 ``tool_call_id`` 对应某次调用。
    """

    def __init__(self, system_prompt: str = "你是一个乐于助人的助手。") -> None:
        # 单独保存初始 system 消息，clear/trim 后可以可靠地把它放回第一条。
        self.system_message = {"role": "system", "content": system_prompt}

        # API 接收的就是这样一个消息字典列表。使用 copy 是为了避免
        # messages 与 system_message 指向同一个可变字典，互相意外修改。
        self.messages: list[dict[str, Any]] = [self.system_message.copy()]

        # 以下三个字段统计“本次 CLI 会话”中所有 API 请求的累计用量，
        # /cost 命令可以直接读取它们。一次用户提问如果触发工具调用，
        # 可能产生多次模型请求，因此每次响应的 usage 都应该调用 add_usage。
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

        # 自动摘要关心的是“当前上下文是否已经很长”，所以要保存最近一次
        # 请求的输入 token，而不是用一直增长的累计 prompt_tokens 判断。
        self.last_prompt_tokens = 0

    def append(self, role: str, content: Any, **extra: Any) -> None:
        """向历史末尾追加一条消息。

        普通消息只传 ``role`` 和 ``content``：

        ``history.append("user", "你好")``

        工具消息还需要 ``tool_calls`` 或 ``tool_call_id``，这些字段通过
        ``extra`` 传入。例如：

        ``history.append("tool", "2", tool_call_id="call-1")``
        """

        # extra 会和 role/content 合并为一个符合 API 格式的消息字典。
        self.messages.append({"role": role, "content": content, **extra})

    def clear(self) -> None:
        """清空对话和旧摘要，但保留最初的 system 消息。

        这里故意不清零 token 统计，因为模型请求已经真实发生、费用也已经
        产生。若希望开始全新的费用统计，可以重新创建一个 ChatHistory。
        """

        # 不使用“保留所有 system 消息”，因为第二条 system 可能是旧摘要；
        # /clear 后必须连摘要一起删除，模型才会真正忘记之前的对话。
        self.messages = [self.system_message.copy()]

    def trim(self, max_turns: int = 3) -> None:
        """保留最近的完整轮次。

        一轮从 user 消息开始，到下一个 user 消息之前结束。例如一次带工具
        调用的完整轮次可能包含：

        ``user -> assistant(tool_calls) -> tool -> assistant``

        裁剪时以这整个列表为单位，因此不会留下孤立的 tool_calls 或 tool
        结果。若按单条消息直接切片，下一次 API 请求可能因为配对不完整而 400。

        ``max_turns`` 是上限：保留最近的轮数。
        """

        if max_turns < 0:
            raise ValueError("max_turns 不能小于 0")

        # 第一条初始 system 永远保留，只对后面的对话部分做截断。
        conversation = self.messages[1:]
        if not conversation or max_turns == 0:
            self.messages = [self.system_message.copy()]
            return

        # 先把扁平消息列表变成“轮次列表”，再从最新一轮向前选择。
        turns = _split_turns(conversation)
        kept_turns: list[list[dict[str, Any]]] = turns[-max_turns:]

        self.messages = [self.system_message.copy()] + [
            message for turn in kept_turns for message in turn
        ]

    def add_usage(self, usage: Any | None) -> None:
        """累计一次 API 响应的 token 用量。

        OpenAI SDK 通常返回带属性的 ``CompletionUsage`` 对象；测试、JSON
        或其他兼容后端也可能给出字典。因此这里同时支持两种形式。
        部分本地模型不返回 usage，此时传入 None，方法会直接跳过。
        """

        if usage is None:
            return

        if isinstance(usage, dict):
            # 字典形式，例如 {"prompt_tokens": 10, ...}。
            prompt = usage.get("prompt_tokens", 0)
            completion = usage.get("completion_tokens", 0)
            total = usage.get("total_tokens", prompt + completion)
        else:
            # OpenAI SDK 对象形式，例如 response.usage.prompt_tokens。
            prompt = getattr(usage, "prompt_tokens", 0)
            completion = getattr(usage, "completion_tokens", 0)
            total = getattr(usage, "total_tokens", prompt + completion)

        # 累计字段用于 /cost；last_prompt_tokens 只记录本次值，用于摘要阈值。
        self.prompt_tokens += int(prompt or 0)
        self.completion_tokens += int(completion or 0)
        self.total_tokens += int(total or 0)
        self.last_prompt_tokens = int(prompt or 0)

    def compress_if_needed(
        self,
        summarize: Callable[[list[dict[str, Any]]], str],
        max_prompt_tokens: int = 4000,
        keep_recent_turns: int = 3,
    ) -> bool:
        """输入 token 超过阈值时，用摘要替换早期完整轮次。

        ``summarize`` 是调用模型的函数：接收需要压缩的消息列表，返回摘要
        字符串。history 模块只负责决定“总结哪些消息”，不负责创建 LLM 客户端，
        这样历史管理和模型调用的职责不会混在一起。

        主循环可在一轮对话完成并调用 ``add_usage`` 后执行：

        ``history.compress_if_needed(summarize, max_prompt_tokens=4000)``

        ``keep_recent_turns`` 决定原文保留多少轮。最近对话通常比摘要更准确，
        所以默认原样保留最近 3 轮，只总结更早的内容。

        返回 True 表示发生了压缩，False 表示本次不需要压缩。
        """

        # 使用服务端上一轮返回的真实 prompt_tokens 判断上下文长度。
        if self.last_prompt_tokens < max_prompt_tokens:
            return False
        if keep_recent_turns < 0:
            raise ValueError("keep_recent_turns 不能小于 0")

        # 先跳过永远保留的初始 system 消息。切片得到新列表，所以后面的 pop
        # 不会直接修改 self.messages。
        conversation = self.messages[1:]
        old_summary: dict[str, Any] | None = None

        # 历史可能已经压缩过一次。固定前缀帮助我们识别第二条 system 是摘要，
        # 而不是用户最初设置的系统提示。
        if (
            conversation
            and conversation[0].get("role") == "system"
            and str(conversation[0].get("content", "")).startswith(SUMMARY_PREFIX)
        ):
            old_summary = conversation.pop(0)

        turns = _split_turns(conversation)

        # 没有足够的早期轮次可压缩时，不调用模型，避免一次无意义的 API 消耗。
        if len(turns) <= keep_recent_turns:
            return False

        # 前半部分交给模型总结，最后 keep_recent_turns 轮保留原文。
        split_at = len(turns) - keep_recent_turns
        old_messages = [message for turn in turns[:split_at] for message in turn]
        recent_messages = [message for turn in turns[split_at:] for message in turn]

        # 再次压缩时，把旧摘要也交给模型，生成一份合并后的新摘要。
        if old_summary is not None:
            old_messages.insert(0, old_summary)

        # 真正的模型调用发生在传入的 summarize 函数内部。
        summary = summarize(old_messages).strip()
        if not summary:
            raise ValueError("摘要不能为空")

        # 摘要紧跟初始 system 放置，之后再拼接最近几轮的原始消息。
        summary_message = {"role": "system", "content": SUMMARY_PREFIX + summary}
        self.messages = [self.system_message.copy(), summary_message, *recent_messages]
        return True

    def cost(self, input_price: float = 0, output_price: float = 0) -> float:
        """按每百万 token 的输入、输出单价估算本次会话费用。

        不同模型价格不同，所以价格由调用方传入而不是写死。若使用本地 Ollama
        或暂时不知道价格，保持默认 0 即可。
        """

        return (
            self.prompt_tokens * input_price + self.completion_tokens * output_price
        ) / 1_000_000

    def save(self, path: str | Path = DEFAULT_HISTORY_FILE) -> Path:
        """将消息和 token 用量保存为 UTF-8 JSON 文件。

        默认保存到项目 ``data/`` 目录；该目录已被 Git 忽略，聊天内容不会
        被提交到仓库。``ensure_ascii=False`` 用来让中文直接可读，``indent=2``
        用来方便学习时打开 JSON 观察数据结构。
        """

        file_path = Path(path)

        # data/ 可能还不存在，parents=True 会连同缺失的父目录一起创建。
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 只保存 JSON 原生支持的字典、列表、字符串和数字。
        # 不直接保存 OpenAI/Pydantic 响应对象，因为 json.dumps 不认识它们。
        data = {
            "system_message": self.system_message,
            "messages": self.messages,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
                "last_prompt_tokens": self.last_prompt_tokens,
            },
        }
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return file_path

    @classmethod
    def load(cls, path: str | Path = DEFAULT_HISTORY_FILE) -> ChatHistory:
        """从 ``save`` 生成的 JSON 文件恢复消息和 token 统计。

        使用类方法是因为恢复时要创建并返回一个新的 ChatHistory 对象。
        """

        # 先把 JSON 文本还原为普通 Python 字典。
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        system_message = data["system_message"]

        # 先走正常构造函数，保证所有字段存在，再用文件中的值覆盖。
        history = cls(system_message["content"])
        history.system_message = system_message
        history.messages = data["messages"]

        # get(..., 0) 让较早保存、没有完整 usage 字段的文件也能恢复。
        usage = data.get("usage", {})
        history.prompt_tokens = usage.get("prompt_tokens", 0)
        history.completion_tokens = usage.get("completion_tokens", 0)
        history.total_tokens = usage.get("total_tokens", 0)
        history.last_prompt_tokens = usage.get("last_prompt_tokens", 0)
        return history

    @classmethod
    def load_or_create(
        cls,
        path: str | Path = DEFAULT_HISTORY_FILE,
        system_prompt: str = "你是一个乐于助人的助手。",
    ) -> ChatHistory:
        """启动时恢复历史；文件还不存在就创建一个新会话。

        主程序启动时只需要调用这个方法，不必自己重复写 exists 判断：

        ``history = ChatHistory.load_or_create()``
        """

        file_path = Path(path)
        if file_path.exists():
            return cls.load(file_path)
        return cls(system_prompt)


# ChatHistory 更短，适合学习；ConversationHistory 语义更完整。
# 两个名字指向同一个类，不会产生两套实现。
ConversationHistory = ChatHistory


def _split_turns(messages: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """把扁平消息列表按 user 消息分成完整轮次。

    例如：

    ``[user, assistant, user, assistant(tool_calls), tool, assistant]``

    会变成：

    ``[[user, assistant], [user, assistant(tool_calls), tool, assistant]]``

    trim 和摘要都复用这个函数，确保它们采用相同的“完整轮次”定义。
    """

    turns: list[list[dict[str, Any]]] = []
    for message in messages:
        # 每遇到一条 user 消息，就开始一个新的对话轮次。
        if message.get("role") == "user":
            turns.append([])
        if not turns:
            # 正常历史不会走到这里；保留异常消息比静默丢失更容易排查。
            turns.append([])
        turns[-1].append(message)
    return turns
