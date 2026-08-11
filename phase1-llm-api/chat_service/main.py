"""阶段 1 · 《FastAPI入门》· 动手任务 1 + 2 + 3（app 创建与路由挂载）

本文件职责：创建 FastAPI app、挂载路由。相当于 Spring Boot 的启动类 + Controller。

任务 1：搭起服务。
1. 按 `chat_service/` 结构搭起服务（main.py / schemas.py / llm.py）
2. 实现 `/health` 健康检查
3. 实现 `/chat2`：接收 pydantic 请求体，用 `Depends` 注入 LLM 客户端，连本地 Ollama
4. 启动后在 `http://localhost:8000/docs` 里直接试调（自动生成的 Swagger UI）

任务 2：SSE 流式接口。
1. 实现 `/chat/stream`，用 `StreamingResponse` + `text/event-stream` 逐字下发
2. 验证真的是**分批到达**而不是一次性吐出——粘贴最终文本没有意义，
   要看每个 delta 的到达时刻（带时间戳的客户端脚本，见 verify.md 第 3 节）

任务 3（进阶）：服务端有状态会话。
1. 给 `/chat2` 增加 `session_id` 参数
2. 用内存 dict 维护多会话历史（复用 ex03 的多轮逻辑）
3. 验证：同一个 session_id 连续请求有记忆，换一个 session_id 就是新对话

任务 4：并发对照实验（本课最值钱的部分）
⚠️ 2026-08-11 订正：原先此实验挂在任务 2 下、且描述为"改成同步 def + 同步 client"，
   两处都不准——① 它测的是 async 路由能否被阻塞，与流式无关，在非流式的 /chat2 上
   做观测量更干净；② `def` 路由会被 FastAPI 丢进线程池（默认 40 个），**不会**堵事件循环，
   按原描述做复现不出事故。

在 /chat2 之外**并存**加两个临时路由（别改来改去，三组要能一次跑完）：

| 路由 | 声明 | 客户端 | 预期 |
|---|---|---|---|
| /chat2            | async def | AsyncOpenAI + await | 并发正常（基线） |
| /chat2_blocking   | async def | **同步 OpenAI**      | ❌ 事件循环被堵，请求串行 |
| /chat2_threadpool | **def**   | 同步 OpenAI          | 并发正常（走线程池） |

1. 用脚本同时发两个请求（asyncio.gather，别顺序发），记录各自的发出/返回时刻
2. prompt 要够长，让单次调用几秒起步，否则差异淹没在噪声里
3. **动手前先把三组的预期写进 verify.md**，再去测（先预测后测量）
4. 要回答：堵住第二个请求的具体是什么？`def` 路由为什么没事？
   这和阶段 0 async 课的「让路 vs 堵路」是同一个机制吗，差别在哪？

要求/提示：
- 启动命令：`uv run uvicorn chat_service.main:app --reload --port 8000`
- 路由用 `async def` + `AsyncOpenAI`，别在 async 路由里写阻塞调用（Java 背景最容易踩）
- 内存 dict 存会话在生产里是错的（多 worker 不共享），注释里写清楚为什么，阶段 2 会换掉
- 完成标准：`/health`、`/chat2`、`/chat/stream` 三个接口在 `/docs` 或 curl 下均可用；
  同步版与异步版的并发差异有实测记录
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import aclosing, asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI, OpenAI

from .llm import (
    ConversationMessage,  # 会话历史中单条消息的类型
    chat,  # 普通、非流式 LLM 调用
    chat_sync,  # 并发实验使用的同步、非流式 LLM 调用
    close_llm_client,  # 关闭单例客户端及其连接池
    close_sync_llm_client,  # 关闭同步单例客户端及其连接池
    get_llm_client,  # 获取由 lru_cache 缓存的单例客户端
    get_sync_llm_client,  # 获取由 lru_cache 缓存的同步单例客户端
    stream_chat,  # 流式 LLM 调用
    validate_config,
)
from .schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


@asynccontextmanager  # 将下面的异步生成器转换为 FastAPI lifespan 上下文
async def lifespan(_: FastAPI) -> AsyncIterator[None]:  # 定义应用启动和关闭生命周期
    try:  # 确保应用即使异常退出也会执行资源清理
        get_llm_client()  # 启动时预先创建异步客户端单例
        get_sync_llm_client()  # 同时预创建同步单例，避免并发首请求重复建池
        validate_config()
        yield  # yield 之前是启动阶段；执行到这里后应用开始接收请求
    finally:  # 应用停止时一定会进入 finally
        try:  # 即使异步客户端关闭失败，也继续尝试关闭同步客户端
            await close_llm_client()  # 异步关闭客户端并释放 HTTP 连接池
        finally:  # 保证两个连接池都得到清理机会
            await asyncio.to_thread(  # 不在事件循环线程中执行同步 close
                close_sync_llm_client  # 关闭同步客户端及其连接池
            )


app = FastAPI(title="chat_service", version="1.0.0", lifespan=lifespan)
LLMClient = Annotated[AsyncOpenAI, Depends(get_llm_client)]
SyncLLMClient = Annotated[
    OpenAI,
    Depends(get_sync_llm_client),
]
_sessions: dict[str, list[ConversationMessage]] = {}  # 按 session_id 保存进程内会话历史
_session_locks: dict[str, asyncio.Lock] = {}  # 为每个 session_id 保存一把异步锁
# 上面两个 dict 仅适合教学：多 worker 不共享、重启会丢失且数据不会自动过期。
# 生产环境应改用 Redis/数据库，并增加 TTL、历史长度或 token 数量限制。


def _get_session_lock(session_id: str) -> asyncio.Lock:
    # 已存在就复用，不存在就保存一把新锁
    return _session_locks.setdefault(session_id, asyncio.Lock())


def _sse_event(data: object, *, event: str | None = None) -> str:
    event_line = f"event: {event}\n" if event else ""
    payload = json.dumps(data, ensure_ascii=False)
    return f"{event_line}data: {payload}\n\n"


async def _stream_events(
    request: ChatRequest,
    client: AsyncOpenAI,
) -> AsyncIterator[str]:
    try:
        chunks = stream_chat(request, client)
        async with aclosing(chunks):
            async for chunk in chunks:
                for character in chunk:
                    yield _sse_event({"delta": character})
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("LLM stream failed")
        yield _sse_event({"message": "LLM stream failed"}, event="error")
        return

    yield _sse_event({}, event="done")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat2", response_model=ChatResponse, tags=["chat"])
async def chat2(request: ChatRequest, client: LLMClient) -> ChatResponse:
    if request.session_id is None:
        return await chat(request, client)

    lock = _get_session_lock(request.session_id)
    async with lock:
        history = _sessions.get(request.session_id, [])
        response = await chat(request, client, history=history)

        _sessions.setdefault(request.session_id, []).extend(
            [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": response.reply},
            ]
        )
        return response


# ──────────────────────────────────────────────────────────────────────
# 以下两个路由**仅供任务 4 的并发对照实验**，不是生产代码，别当范例抄。
# 保留它们是因为：结论（见 verify.md 第 6 节）需要可复现的证据，
# 删掉的话下次想验证还得重写一遍。
#
# 三组对照与实测结论（token 判据，n=3）：
#   /chat2            async def + AsyncOpenAI  → 并发 3/3   ✅ 正确写法
#   /chat2_blocking   async def + 同步 OpenAI  → 并发 0/3   ❌ 事故现场
#   /chat2_threadpool def       + 同步 OpenAI  → 并发 2/3   （第 1 轮线程冷启动）
#
# 判据用的是 completion_tokens 而非耗时：temperature=0 时单独跑输出确定，
# 两个请求被合进同一个推理 batch 会扰动浮点累加顺序，token 数就不同了。
# 单 GPU 上并行会共享算力，墙钟时间没有区分度——详见 verify.md 6.4。
# ──────────────────────────────────────────────────────────────────────


@app.post("/chat2_blocking", response_model=ChatResponse, tags=["experiment"])
async def chat2_blocking(
    request: ChatRequest,
    client: SyncLLMClient,
) -> ChatResponse:
    """[实验] async 路由里调同步客户端——FastAPI 最经典的性能事故。

    路由声明为 async def 意味着它直接跑在事件循环上；函数体里的同步 HTTP 调用
    不会交出控制权，于是**整个进程的所有请求**都被堵住（不只这个接口，
    /health 在那几秒里同样卡住）。生产代码绝不能这么写。
    """
    return chat_sync(request, client)


@app.post("/chat2_threadpool", response_model=ChatResponse, tags=["experiment"])
def chat2_threadpool(
    request: ChatRequest,
    client: SyncLLMClient,
) -> ChatResponse:
    """[实验] 同步路由——FastAPI 会丢进线程池，不占事件循环。

    注意是 `def` 不是 `async def`：FastAPI 检测到它不是协程，就用
    run_in_threadpool 交给 anyio 线程池（默认 40 线程）执行，事件循环不受影响。
    代价是线程数有上限，超过 40 个并发同步请求就开始排队。
    首次请求会有线程创建的冷启动开销（实验第 1 轮串行即因于此）。
    """
    return chat_sync(request, client)


@app.post(
    "/chat/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "流式响应",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        }
    },
    tags=["chat"],
)
async def chat_stream(
    request: ChatRequest,
    client: LLMClient,
) -> StreamingResponse:
    return StreamingResponse(
        _stream_events(request, client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
