# prompts/ —— prompt 模板目录

阶段 1 ·《Prompt工程》· 动手任务 3

任务：把练习里写的 prompt 从 Python 代码里抽出来，各存成一个 `.md` 文件放在本目录，
由代码在运行时加载（读文件），体验 **prompt 与代码分离**。

建议至少抽出这几个：

- `code_reviewer.md` —— `ex06_system_prompt.py` 的代码评审员 system prompt
- `jd_extract_fewshot.md` —— `ex06_fewshot_vs_zeroshot.py` 的 few-shot 抽取 prompt
- 后续 ex07 / ex08 / 项目① 里的 prompt 也陆续搬进来

要求/提示：

- 加载方式自己定（`pathlib.Path.read_text(encoding="utf-8")` 是最直接的一种），
  注意 Windows 下必须显式指定编码，否则中文 prompt 会乱码
- 想清楚这样做的好处：改 prompt 不用改代码、不用重新发版、可以做 A/B、可以进 code review
  （类比 Java 把 SQL 抽到 mapper.xml、把文案抽到 messages.properties）
- 完成标准：`ex06_*.py` 里不再出现硬编码的长 prompt 字符串，改 `.md` 文件即可改变行为
