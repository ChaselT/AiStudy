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
