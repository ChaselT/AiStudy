"""进阶篇 6/7《常用标准库与生态》· 动手任务 2

任务：用 httpx GET https://httpbin.org/json，
      配置 logging 记录请求耗时，
      把响应 JSON 用 pathlib 写到 data/out.json（目录不存在则自动创建）。

提示：Path("data").mkdir(exist_ok=True)；写文件记得 encoding="utf-8"。
"""
