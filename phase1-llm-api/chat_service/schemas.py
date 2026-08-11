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

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=10000,
        description="用户消息，即用户输入的内容，如果传了session_id是追问，不传是新对话",
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="控制输出的随机性。信息抽取、分类等要求稳定的场景用 0；创意写作用 0.7~1.0。",
    )
    session_id: str | None = Field(
        default=None,
        description="会话标识。相同 session_id 的请求共享对话历史，实现多轮上下文；不传则每次都是新对话",
    )


class Usage(BaseModel):
    prompt_tokens: int = Field(
        description="提示词消耗token量，可能会包含推理过程消耗的token量"
    )
    completion_tokens: int = Field(description="响应消耗token量")
    total_tokens: int = Field(description="总消耗token量")


class ChatResponse(BaseModel):
    reply: str = Field(description="回复的消息")
    usage: Usage | None = Field(
        default=None, description="token消耗量,部分后端可能不返回该值"
    )
