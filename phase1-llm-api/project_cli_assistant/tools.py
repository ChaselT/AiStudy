"""阶段 1 · 项目①：CLI 智能助手 · 工具定义与注册表

本文件职责：定义各工具的 JSON schema、实现对应的 Python 函数、维护名字到函数的注册表。

至少 3 个工具（MOC 要求）：
- `get_current_time`：查询当前时间
- `calculator`：数学计算，**安全求值，不要裸 `eval`**
  （想想为什么：用户可以让模型构造出 `__import__('os').system(...)`）
- `read_file` 或 `search_web`：读本地文件（需路径校验，复用 ex08_more_tools 的做法）
  或联网搜索（本机走 SOCKS 代理，httpx 已装 socks extra）

要求/提示：
- 注册表设计：一个 dict 把工具名映射到函数，schema 列表一并导出，
  新增工具时**只改本文件**，llm.py 和 main.py 都不用动（这是设计质量的检验标准）
- 每个工具的 description 认真写——它就是给模型看的 API 文档，写糊了模型就选错工具
- 工具执行必须捕获异常并返回**结构化的错误信息**给模型，绝不让异常冒泡到主循环
- 加分项"工具并行调用"：模型一次返回多个 tool_calls 时用 asyncio.gather 并发执行
"""
