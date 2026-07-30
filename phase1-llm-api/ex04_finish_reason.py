"""阶段 1 · 《采样参数详解》· 动手任务 2

任务：制造并检测截断。
1. 问一个需要长回答的问题（如"详细讲讲 JVM 垃圾回收"）
2. 故意把 `max_tokens` 设得很小（如 30），让回答被硬生生截断
3. 检测 `resp.choices[0].finish_reason == "length"`，命中时打印醒目告警
4. 对比：把 max_tokens 调大后 finish_reason 变成什么

要求/提示：
- `finish_reason` 的常见取值都记进注释（stop / length / tool_calls / content_filter）
- 这是生产代码里必查的字段——用户看到半截话时你得知道是被截断了还是模型自己说完了
- 完成标准：两次运行分别打出 length 和 stop，告警逻辑生效
"""
