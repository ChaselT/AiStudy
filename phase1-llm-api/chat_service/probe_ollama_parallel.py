"""并发实验的前置基线检查：Ollama 服务端本身能不能并行处理请求。

为什么需要它：
    任务 4 要测的是「阻塞调用会不会堵死 FastAPI 的事件循环」。但如果 Ollama 侧
    只有一个并发槽（OLLAMA_NUM_PARALLEL=1），那么**三组路由都会串行**——
    你会看到三份一模一样的数据，并把 Ollama 的排队误判成事件循环被堵。

    基线不成立，后面三组数据全部没有意义。所以正式实验前先跑这个。
    （同 ex08 的规矩：先证明有漏洞的版本会失败，绿灯才可信）

用法：
    uv run python chat_service/probe_ollama_parallel.py
    uv run python chat_service/probe_ollama_parallel.py qwen3.5:27b   # 指定模型

判读：
    ratio ≈ 1.0  → 完全并行
    ratio ≈ 2.0  → 完全串行，需要设 OLLAMA_NUM_PARALLEL 并重启 Ollama

设置方法（PowerShell，改完必须**完全退出** Ollama 托盘图标再重启，
再**新开终端**——旧终端继承的是旧环境快照，这个坑 ex10 踩过）：
    [Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "4", "User")

⚠️ 别用 emoji 打印：Windows 控制台默认 GBK，会抛 UnicodeEncodeError。
"""

import asyncio
import os
import sys
import time

import httpx

os.environ["NO_PROXY"] = "localhost,127.0.0.1"  # 本机 SOCKS 代理会拦截本地请求

URL = "http://127.0.0.1:11434/api/chat"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3-vl:8b"
PROMPT = "写一段300字的散文"
NUM_PREDICT = 300  # 固定输出长度，让每次调用耗时可比


async def _one(client: httpx.AsyncClient, tag: str, t0: float) -> float:
    start = time.perf_counter() - t0
    resp = await client.post(
        URL,
        json={
            "model": MODEL,
            "stream": False,
            "messages": [{"role": "user", "content": PROMPT}],
            "options": {"num_predict": NUM_PREDICT},
        },
        timeout=600,
    )
    end = time.perf_counter() - t0
    tokens = resp.json().get("eval_count")
    print(f"  {tag}: start {start:5.2f}s  end {end:5.2f}s  dur {end - start:5.2f}s  tokens={tokens}")
    return end - start


async def main() -> None:
    print(f"model = {MODEL}")
    # trust_env=False：绕开系统代理，别让 SOCKS 插一脚
    async with httpx.AsyncClient(trust_env=False) as client:
        print("warmup (排除模型加载与首次推理的 kernel 编译，见错题本 E48)...")
        await client.post(
            URL,
            json={
                "model": MODEL,
                "stream": False,
                "messages": [{"role": "user", "content": "hi"}],
                "options": {"num_predict": 1},
            },
            timeout=600,
        )

        print("solo:")
        t0 = time.perf_counter()
        solo = await _one(client, "req0", t0)

        print("concurrent x2:")
        t0 = time.perf_counter()
        await asyncio.gather(_one(client, "req1", t0), _one(client, "req2", t0))
        wall = time.perf_counter() - t0

        ratio = wall / solo
        print(f"\nsolo={solo:.2f}s  concurrent_wall={wall:.2f}s  ratio={ratio:.2f}")
        print("VERDICT:", "PARALLEL" if ratio < 1.5 else "SERIALIZED (set OLLAMA_NUM_PARALLEL)")


if __name__ == "__main__":
    asyncio.run(main())
