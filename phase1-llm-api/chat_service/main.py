"""阶段 1 · 《FastAPI入门》· 动手任务 1 + 2 + 3（app 创建与路由挂载）

本文件职责：创建 FastAPI app、挂载路由。相当于 Spring Boot 的启动类 + Controller。

任务 1：搭起服务。
1. 按 `chat_service/` 结构搭起服务（main.py / schemas.py / llm.py）
2. 实现 `/health` 健康检查
3. 实现 `/chat2`：接收 pydantic 请求体，用 `Depends` 注入 LLM 客户端，连本地 Ollama
4. 启动后在 `http://localhost:8000/docs` 里直接试调（自动生成的 Swagger UI）

任务 2：SSE 流式接口。
1. 实现 `/chat/stream`，用 `StreamingResponse` + `text/event-stream` 逐字下发
2. 用 `curl -N` 验证真的是逐字到达（`-N` 关缓冲，否则看不出流式）
3. 对照实验：故意把路由改成同步 `def` + 同步 client，
   开两个终端并发请求，感受第二个请求被阻塞的差异——这是 FastAPI 最经典的性能事故

任务 3（进阶）：服务端有状态会话。
1. 给 `/chat2` 增加 `session_id` 参数
2. 用内存 dict 维护多会话历史（复用 ex03 的多轮逻辑）
3. 验证：同一个 session_id 连续请求有记忆，换一个 session_id 就是新对话

要求/提示：
- 启动命令：`uv run uvicorn chat_service.main:app --reload --port 8000`
- 路由用 `async def` + `AsyncOpenAI`，别在 async 路由里写阻塞调用（Java 背景最容易踩）
- 内存 dict 存会话在生产里是错的（多 worker 不共享），注释里写清楚为什么，阶段 2 会换掉
- 完成标准：`/health`、`/chat2`、`/chat/stream` 三个接口在 `/docs` 或 curl 下均可用；
  同步版与异步版的并发差异有实测记录
"""
