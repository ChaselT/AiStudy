"""阶段 0 测试 · B 卷实操（60 分）——并发网站体检工具

═══════════════════════════════════════════════════════════════
考试规则
  · 可查官方文档（httpx / pydantic / asyncio）
  · 不可用 AI 生成代码，不可看自己以前作业里的成品实现
  · 卡住超过 15 分钟可以向 Claude 要"方向性提示"（不给代码）
  · 预计用时 60-90 分钟
  · A 卷已得 35.5/40，本卷 ≥44.5 分即通过阶段 0（总分 ≥80）
═══════════════════════════════════════════════════════════════

题目：实现一个并发网站体检工具。

1.（15 分）定义 pydantic 模型 `SiteReport`，字段：
       url: str
       status: int
       elapsed_ms: float
       ok: bool          # status 为 2xx/3xx 时为 True

2.（20 分）用 httpx.AsyncClient + asyncio.gather **并发**检测至少 5 个网站，
       每个站产出一个 SiteReport；
       单站超时 5 秒；超时或任何异常**都不许让程序崩溃**（该站 status 记 0）。

3.（10 分）实现装饰器 `@timed`，打印整个检测流程的总耗时。

4.（10 分）结果按 elapsed_ms **升序**输出为**对齐的表格**，
       并把 JSON 写入 report.json（用 model_dump）。

5.（5 分）全文件类型注解完整，`uv run exam_site_checker.py` 直接可跑。

═══════════════════════════════════════════════════════════════
评分维度：功能正确 + 代码 Pythonic（推导式 / f-string / pathlib，别写 Java 味 Python）
          + 异常处理得当

交卷前自查（说"完成了"之前逐条对照——老规矩）：
  □ 5 个评分点逐条看过，没有漏项
  □ `uv run exam_site_checker.py` 跑通，亲眼看到表格输出
  □ `uv run mypy exam_site_checker.py` 零报错
  □ report.json 真的生成了，内容正确
  □ 故意塞一个不存在的域名进去，程序**不崩**、该站 status 为 0
═══════════════════════════════════════════════════════════════
"""

from typing import Self
from pydantic import BaseModel, Field, model_validator
import httpx
import time
import asyncio
from functools import wraps
import json
from pathlib import Path


def timed(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await fn(*args, **kwargs)
        print(f"{fn.__name__} took {time.perf_counter() - start:.4f}s")
        return result

    return wrapper


class SiteReport(BaseModel):
    url: str
    status: int = Field(ge=0)
    elapsed_ms: float
    ok: bool = Field(default=False, validate_default=True)

    @model_validator(mode="after")
    def calculate_ok(self) -> Self:
        self.ok = 200 <= self.status < 400
        return self


async def check_web_one(client: httpx.AsyncClient, url: str) -> SiteReport:

    start = time.perf_counter()
    res_status = 0
    try:
        res = await client.get(url)
        res_status = res.status_code
    except Exception as e:
        print(e)

    use_time = round(
        (time.perf_counter() - start) * 1000,
        4,
    )
    return SiteReport(url=url, status=res_status, elapsed_ms=use_time)


@timed
async def check_web_mul(urls: list[str]) -> list[SiteReport]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        tasks = [check_web_one(client, w) for w in urls]
        return list(await asyncio.gather(*tasks))


async def main() -> None:
    urls = [
        "http://baidu.com",
        "https://www.hi-code.cc",
        "https://www.bejson.com",
        "https://ip.net.coffee/",
        "https://fo1xcode.rjj.cc/",
    ]
    res_list = await check_web_mul(urls)
    res_list = sorted(res_list, key=lambda report: report.elapsed_ms)
    print(f"|{'url':^100}|{'status':^8}|{'elapsed_ms':^14}|{'is_ok':^8}|")
    for res in res_list:
        print(f"|{res.url:^100}|{res.status:^8}|{res.elapsed_ms:^14}|{res.ok:^8}|")
    file_list = [r.model_dump() for r in res_list]

    Path("report.json").write_text(
        json.dumps(
            file_list,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(main())
