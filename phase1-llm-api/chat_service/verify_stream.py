import time

import httpx

t0 = time.perf_counter()

with httpx.stream(
    "POST",
    "http://localhost:8000/chat/stream",
    json={"message": "用三句话解释幂等性"},
    timeout=None,
) as resp:
    resp.raise_for_status()
    print(resp)

    last_time = t0

    for line in resp.iter_lines():
        if not line:
            continue

        now = time.perf_counter()
        print(f"时间间隔：{now - last_time:.3f}s")
        print(f"响应内容：{line}")
        last_time = now
