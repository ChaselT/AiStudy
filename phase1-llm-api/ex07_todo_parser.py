"""阶段 1 · 《结构化输出》· 动手任务 3（实战）

任务：把口语化的任务描述解析成结构化 Todo。
1. 定义 pydantic 模型 `Todo(title, deadline, priority)`
   - `deadline` 用 `datetime`，`priority` 建议用 Enum 或 Literal 限定取值
2. 输入示例："明天下午三点前把周报发给王总，很急"
3. 输出应为：title="把周报发给王总"、deadline=明天 15:00 的具体时间、priority=高
4. 再自己造 4~5 个说法各异的输入测试鲁棒性
   （"下周一之前"、"这两天吧"、"月底前搞定"、"不急"…）

要求/提示：
- 相对时间是难点：模型不知道"今天"是几号，你得把当前时间写进 prompt 告诉它
- 模糊表达（"这两天"）解析不出来时应该怎么办？想清楚是兜底默认值还是让它返回 null
- 完成标准：5+ 个用例全部解析成合法的 `Todo` 对象并打印；
  mypy 检查零报错（`uv run mypy ex07_todo_parser.py`）
"""
