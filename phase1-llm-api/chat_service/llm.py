"""阶段 1 · 《FastAPI入门》· chat_service 的 Service 层

本文件职责：LLM 客户端的创建与调用封装。类比 Spring 的 @Service + @Bean 配置。

至少需要：
- 一个用 `@lru_cache` 做成单例的 `get_llm_client()`，供 `Depends` 注入
  （类比 Spring 默认的 singleton scope）
- 普通调用与流式调用的封装函数，供路由层调用

要求/提示：
- 客户端用 `AsyncOpenAI`，配置从环境变量读：LLM_BASE_URL / LLM_API_KEY / LLM_MODEL
- 为什么要单例：每次新建 client 会新建连接池，高并发下会打爆句柄
- 路由层不该知道"用的是哪个模型/哪个 base_url"，这些细节都关在本文件里
"""

import os
from collections.abc import AsyncGenerator, Sequence
from functools import lru_cache
from typing import Literal, TypedDict

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from .schemas import ChatRequest, ChatResponse, Usage


class ConversationMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str


def validate_config() -> None:
    _required_env("LLM_BASE_URL")
    _required_env("LLM_API_KEY")
    _required_env("LLM_MODEL")


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"缺少配置项: {name}")
    return value


def _build_messages(
    request: ChatRequest,
    history: Sequence[ConversationMessage],
) -> list[ChatCompletionMessageParam]:
    messages: list[ChatCompletionMessageParam] = [
        {"role": item["role"], "content": item["content"]}  # type: ignore[misc]
        for item in history
    ]
    messages.append({"role": "user", "content": request.message})
    return messages


@lru_cache(maxsize=1)
def get_llm_client() -> AsyncOpenAI:
    """返回FastAPI依赖项使用的进程范围客户端。
    AsyncOpenAI拥有一个HTTP连接池。重用一个客户端可以避免创建
    每个请求一个池，并在负载下耗尽文件描述符或句柄。"""
    return AsyncOpenAI(
        base_url=_required_env("LLM_BASE_URL"),
        api_key=_required_env("LLM_API_KEY"),
        timeout=600.0,
        max_retries=3,
    )


@lru_cache(maxsize=1)  # 同步实验路由也复用一个连接池，避免每次请求新建客户端
def get_sync_llm_client() -> OpenAI:  # 供两个同步客户端实验路由共同注入
    """Return the process-wide synchronous client used by experiment routes."""
    return OpenAI(  # 创建 OpenAI 兼容同步客户端及其 HTTP 连接池
        base_url=_required_env("LLM_BASE_URL"),  # 与异步基线使用相同服务地址
        api_key=_required_env("LLM_API_KEY"),  # 与异步基线使用相同 API Key
    )


def _to_chat_response(response: ChatCompletion) -> ChatResponse:  # 统一映射 SDK 响应
    if not response.choices:  # 普通文本回答至少应该包含一个 choice
        raise RuntimeError(  # 用清晰异常代替后续不直观的 IndexError
            "LLM response did not contain any choices"  # 说明响应缺少候选结果
        )
    if response.usage is None:  # ChatResponse 要求返回 token 使用量
        raise RuntimeError(  # 兼容服务未返回 usage 时明确失败
            "LLM response did not contain token usage"  # 说明缺失的响应字段
        )

    return ChatResponse(  # 把 SDK 响应转换成公开的 Pydantic DTO
        reply=response.choices[0].message.content or "",  # 取第一个文本回答
        usage=Usage(  # 把 SDK usage 转换成本地 Usage 模型
            prompt_tokens=response.usage.prompt_tokens,  # 输入消息消耗的 token 数
            completion_tokens=response.usage.completion_tokens,  # 回答消耗的 token 数
            total_tokens=response.usage.total_tokens,  # 本次请求总 token 数
        ),
    )


async def chat(
    request: ChatRequest,
    client: AsyncOpenAI,
    *,
    history: Sequence[ConversationMessage] = (),
) -> ChatResponse:
    response = await client.chat.completions.create(
        model=_required_env("LLM_MODEL"),
        messages=_build_messages(request, history),
        temperature=request.temperature,
    )

    if not response.choices:
        raise RuntimeError("LLM 响应异常：缺失 choices")
    if response.usage is None:
        res_usage = None
    else:
        res_usage = Usage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    return ChatResponse(
        reply=response.choices[0].message.content or "", usage=res_usage
    )


def chat_sync(  # 封装故意用于并发对照实验的同步、非流式调用
    request: ChatRequest,  # 当前聊天请求 DTO
    client: OpenAI,  # 由 FastAPI Depends 注入的同步单例客户端
) -> ChatResponse:  # 返回与异步基线完全相同的响应 DTO
    """Create a completion with the synchronous SDK for the experiment."""
    response = client.chat.completions.create(  # 同步等待完整模型回答
        model=_required_env("LLM_MODEL"),  # 与异步基线使用同一个模型
        messages=_build_messages(request, ()),  # 实验路由固定为无状态单轮请求
        temperature=request.temperature,  # 与异步基线使用相同随机度
    )
    return _to_chat_response(response)  # 使用与异步基线完全相同的响应映射


async def stream_chat(
    request: ChatRequest,
    client: AsyncOpenAI,
    *,
    history: Sequence[ConversationMessage] = (),
) -> AsyncGenerator[str, None]:
    stream = await client.chat.completions.create(
        model=_required_env("LLM_MODEL"),
        messages=_build_messages(request, history),
        temperature=request.temperature,
        stream=True,
        stream_options={"include_usage": True},
    )

    async with stream:
        async for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content


async def close_llm_client() -> None:
    """清理连接池和缓存"""
    if get_llm_client.cache_info().currsize == 0:
        return

    client = get_llm_client()
    get_llm_client.cache_clear()
    await client.close()


def close_sync_llm_client() -> None:  # 在应用关闭时释放同步单例客户端资源
    """Close and clear the cached synchronous client."""  # 清理同步连接池和缓存
    if get_sync_llm_client.cache_info().currsize == 0:  # 尚未创建时无需关闭
        return  # 避免停机阶段反而创建一个同步客户端

    client = get_sync_llm_client()  # 取得当前已经缓存的同步客户端
    get_sync_llm_client.cache_clear()  # 清空缓存，允许后续创建全新客户端
    client.close()  # 同步关闭底层 HTTP 连接池


__all__ = [
    "ConversationMessage",
    "chat",
    "close_llm_client",
    "close_sync_llm_client",
    "get_llm_client",
    "stream_chat",
    "validate_config",
]
