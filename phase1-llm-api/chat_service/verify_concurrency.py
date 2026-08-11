"""一次运行完成三个 /chat2 路由各三轮的并发对照实验。"""

import asyncio  # 使用 gather 同时发出请求 A 和请求 B
from time import perf_counter  # 使用高精度单调时钟记录发出和返回时刻

import httpx  # 通过真实 HTTP 请求访问正在运行的 FastAPI 服务

BASE_URL = "http://127.0.0.1:8000"  # FastAPI 服务地址
ROUNDS = 3  # 每个路由重复三轮，判断结果是否稳定
PARALLEL_GAP_THRESHOLD = 0.3  # 两个耗时的相对差值小于 30% 就视为并行
SERIALIZED_RATIO = 2.0  # 串行时较长耗时预计约为较短耗时的两倍
SERIALIZED_RATIO_TOLERANCE = 0.3  # “约两倍”允许相对目标值 30% 的误差
ROUTES = [  # 三组实验依次运行，避免不同组互相争抢模型资源
    ("基线：async def + AsyncOpenAI", "/chat2"),
    ("错误：async def + OpenAI", "/chat2_blocking"),
    ("线程池：def + OpenAI", "/chat2_threadpool"),
]
REQUEST_BODY = {  # 三组和 A/B 都使用完全相同的无状态请求体
    "message": "请用约五百字解释异步编程，只输出正文。",
    "temperature": 0.0,
}
WARMUP_BODY = {  # 预热只建立连接和唤醒模型，不参与正式计时
    "message": "只回复：预热完成。",
    "temperature": 0.0,
}


async def warm_up(timeout: httpx.Timeout) -> None:  # 正式实验前依次预热三个执行路径
    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=timeout, trust_env=False
    ) as client:
        print("开始预热（预热请求不计入实验结果）")
        for title, path in ROUTES:
            response = await client.post(path, json=WARMUP_BODY)  # 短请求消除冷启动噪声
            response.raise_for_status()  # 预热失败就停止，避免输出失真的实验数据
            print(f"预热完成：{title}  {path}")


async def send_chat(  # 发送一个普通、非流式聊天请求并记录完整耗时
    name: str,  # 请求名称：A 或 B
    client: httpx.AsyncClient,  # A 和 B 各自使用独立客户端连接
    path: str,  # 当前被测路由
    started: float,  # 当前组的统一计时起点
) -> dict[str, float | int | str]:  # 返回计时和生成工作量
    sent_at = perf_counter() - started  # 记录请求真正开始发送的时刻
    response = await client.post(path, json=REQUEST_BODY)  # 等待完整 JSON 响应
    returned_at = perf_counter() - started  # 记录完整响应到达的时刻
    response.raise_for_status()  # 4xx/5xx 时立即报告实验失败

    body = response.json()  # 解析与 ChatResponse 对应的 JSON
    usage = body.get("usage", {})  # 读取 token 数，检查三组工作量是否接近
    if not isinstance(body.get("reply"), str) or not isinstance(usage, dict):
        raise TypeError(f"请求{name}返回结构不是 ChatResponse：{body}")

    return {  # 保存课程要求的发出、返回和耗时
        "name": name,
        "sent_at": sent_at,
        "returned_at": returned_at,
        "duration": returned_at - sent_at,
        "completion_tokens": int(usage.get("completion_tokens", 0)),
    }


async def run_route(  # 同时发送当前路由的请求 A 和请求 B
    path: str,  # 当前被测路由
    timeout: httpx.Timeout,  # 所有组使用同一超时配置
) -> dict[str, object]:  # 返回 A、B 和总墙钟结果
    async with (  # A 和 B 各自持有独立连接
        httpx.AsyncClient(
            base_url=BASE_URL, timeout=timeout, trust_env=False
        ) as client_a,
        httpx.AsyncClient(
            base_url=BASE_URL, timeout=timeout, trust_env=False
        ) as client_b,
    ):
        started = perf_counter()  # A 和 B 共用同一个计时起点
        request_a, request_b = await asyncio.gather(  # A、B 在这里同时并发执行
            send_chat("A", client_a, path, started),
            send_chat("B", client_b, path, started),
        )
        wall_clock = perf_counter() - started  # 等 A 和 B 都结束后的总墙钟时间

    return {  # 不写文件，直接交给打印函数显示
        "request_a": request_a,
        "request_b": request_b,
        "wall_clock": wall_clock,
    }


def classify_result(duration_a: float, duration_b: float) -> str:
    longer = max(duration_a, duration_b)  # 找出较长耗时作为相对差值的分母
    shorter = min(duration_a, duration_b)  # 找出较短耗时用于计算长短倍数
    if shorter <= 0:  # 正常 HTTP 请求耗时应大于零，异常数据不强行分类
        return "无法判断"

    relative_gap = (longer - shorter) / longer  # 计算两个耗时的相对差值
    if relative_gap < PARALLEL_GAP_THRESHOLD:  # 差值小于 30% 视为同时完成
        return "并行"

    duration_ratio = longer / shorter  # 计算较长耗时是较短耗时的多少倍
    ratio_error = abs(duration_ratio - SERIALIZED_RATIO) / SERIALIZED_RATIO
    if ratio_error < SERIALIZED_RATIO_TOLERANCE:  # 接近两倍就视为串行
        return "串行"

    return "无法判断"  # 既不接近也不约等于两倍时保留不确定结论


def print_result(  # 打印单轮的两个请求结果并返回自动判定
    title: str,
    path: str,
    round_number: int,
    result: dict[str, object],
) -> str:
    print(f"\n{title}  {path}  第 {round_number} 轮")  # 显示实验组和轮次
    request_a = result["request_a"]  # 取出请求 A 的计时结果
    request_b = result["request_b"]  # 取出请求 B 的计时结果
    assert isinstance(request_a, dict)  # 帮助类型检查器理解字典结构
    assert isinstance(request_b, dict)  # 帮助类型检查器理解字典结构

    for request in (request_a, request_b):  # 依次打印 A、B
        print(
            f"请求{request['name']}："
            f"发出 t={request['sent_at']:.3f}s  "
            f"返回 t={request['returned_at']:.3f}s  "
            f"耗时 {request['duration']:.3f}s  "
            f"completion_tokens={request['completion_tokens']}"
        )

    print(f"两者总墙钟时间：{result['wall_clock']:.3f}s")
    duration_a = float(request_a["duration"])  # 读取请求 A 的完整耗时
    duration_b = float(request_b["duration"])  # 读取请求 B 的完整耗时
    longer = max(duration_a, duration_b)  # 用于显示本轮实际相对差值
    shorter = min(duration_a, duration_b)  # 用于显示本轮实际耗时倍数
    relative_gap = (longer - shorter) / longer  # 两个耗时的相对差值
    duration_ratio = longer / shorter  # 较长耗时与较短耗时的倍数
    verdict = classify_result(duration_a, duration_b)  # 按统一判据自动分类
    print(
        f"自动判定：{verdict}  "
        f"相对差值={relative_gap:.3f}  "
        f"长短倍数={duration_ratio:.3f}"
    )
    return verdict  # 交给三轮汇总判断结果是否稳定


def summarize_rounds(verdicts: list[str]) -> str:  # 汇总一个路由的三轮判定
    if all(verdict == "并行" for verdict in verdicts):
        return "稳定并行"  # 三轮全部并行才认定为稳定并行
    if all(verdict == "串行" for verdict in verdicts):
        return "稳定串行"  # 三轮全部串行才认定为稳定串行
    return (  # 结果不一致或包含不确定时归为混合结果
        "结果混合 / 无法判断  "
        f"并行={verdicts.count('并行')}  "
        f"串行={verdicts.count('串行')}  "
        f"无法判断={verdicts.count('无法判断')}"
    )


async def main() -> None:  # 一次启动依次跑完三组，每组连续执行三轮
    timeout = httpx.Timeout(600.0, connect=5.0)  # 长 prompt 允许模型充分生成

    await warm_up(timeout)  # 所有执行路径预热完毕后，再开始正式计时

    for title, path in ROUTES:  # 一个路由跑完三轮后才开始下一个路由
        verdicts: list[str] = []  # 保存当前路由三轮的自动判定
        for round_number in range(1, ROUNDS + 1):  # 当前路由连续执行三轮
            result = await run_route(path, timeout)  # 每轮内部 A/B 同时执行
            verdicts.append(  # 保存本轮判定供三轮稳定性汇总
                print_result(title, path, round_number, result)
            )
        print(f"\n{title}  三轮汇总：{summarize_rounds(verdicts)}")


if __name__ == "__main__":  # 直接运行本文件时才开始实验
    asyncio.run(main())
