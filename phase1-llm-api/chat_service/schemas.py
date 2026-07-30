"""阶段 1 · 《FastAPI入门》· chat_service 的 DTO 层

本文件职责：定义请求/响应的 pydantic 模型（类比 Java 的 DTO / VO）。

至少需要：
- `ChatRequest`：message、temperature（给默认值）、可选 session_id
- `ChatResponse`：reply，以及你想暴露的 usage 信息

要求/提示：
- 用 `Field` 加约束和描述——描述会直接出现在 `/docs` 的 Swagger 文档里，
  类比 Bean Validation 注解 + Swagger 注解，但只写一遍
- 想清楚 temperature 的合法区间，让框架帮你校验，别在路由里写 if
"""
