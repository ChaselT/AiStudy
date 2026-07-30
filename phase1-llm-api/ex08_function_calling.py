"""阶段 1 · 《Function Calling》· 动手任务 1 + 任务 3

任务 1：跑通笔记里的 function calling 示例。
1. 定义 `get_weather` 和 `calculator` 两个工具的 tools schema，实现对应的 Python 函数
2. 实现完整闭环：模型返回 tool_calls → 你执行函数 → 把结果以 role="tool" 回传 → 模型继续
3. 提问"北京和上海温度差几度"，观察它如何触发 **天气 → 天气 → 计算器** 的多轮调用链
4. 把每一轮的 messages 打印出来，看清楚 tool_call_id 是怎么配对的

任务 3：破坏性实验。
1. 把 `get_weather` 的 description 改成含糊的"一个函数"
2. 同样的问题再问一次，观察模型还能不能正确选择工具
3. 恢复后对比，把结论写进注释——体会 description 就是给模型看的 API 文档

要求/提示：
- 这是 Agent 的基石，闭环的每一步都要自己写一遍，别抄
- 注意循环终止条件：模型不再返回 tool_calls 时才算结束，否则会无限套娃
- `finish_reason == "tool_calls"` 是判断依据之一（回顾 ex04）
- 完成标准：一次提问触发 3 次工具调用并给出正确答案；破坏实验前后行为差异可复现
"""
