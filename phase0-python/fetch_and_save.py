"""进阶篇 6/7《常用标准库与生态》· 动手任务 2

任务：用 httpx GET https://httpbingo.org/json，
      配置 logging 记录请求耗时，
      把响应 JSON 用 pathlib 写到 data/out.json（目录不存在则自动创建）。

提示：Path("data").mkdir(exist_ok=True)；写文件记得 encoding="utf-8"。
"""

from pathlib import Path
import httpx
import json
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_url() -> str:
    start = time.perf_counter()
    res = httpx.get("https://httpbingo.org/json")
    #     return res.text 简单返回方法，留作记录
    use_time = time.perf_counter() - start
    logger.info("请求耗时：%s s", format(use_time, ".4f"))
    return json.dumps(res.json(), ensure_ascii=False, indent=2)


def main():

    p = Path(__file__).parent
    f = p / "data" / "out.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    res = fetch_url()
    f.write_text(res, encoding="utf-8")


if __name__ == "__main__":
    main()
