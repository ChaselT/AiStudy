r"""阶段 1 · 《Ollama本地模型》· 动手任务（2026-08-06 按实际进度裁剪）

⚠️ 任务 1、2 已在前面几课中完成，不重做。证据：
    连本地 Ollama（base_url + 占位 key）  → ex03_switch_backend.py
    非流式调用                            → ex03 / ex07 / ex09
    流式输出                              → ex05_stream_basic / _chat / _async
    usage 是否返回                        → ex07_json_mode（并挖出 E41：
                                            prompt_eval_count 会混入 thinking token）
    OLLAMA_MODELS 外置 / 拉取 27b          → 环境搭建时完成
    ollama ps 显存 vs 估算公式             → 错题本 E34（Q4_K_M 混合精度）
                                            + 「ollama ps 与 nvidia-smi 不可混用」
    OLLAMA_HOST=0.0.0.0 导致 CLI 连不上     → Obsidian「Ollama安装与配置」

────────────────────────────────────────────────────────────
本课唯一要做的：把 KV cache 从「定性认知」变成「可用来估算的系数」
────────────────────────────────────────────────────────────

你现在关于 KV cache 只有一句定性结论（"随 num_ctx 与生成长度增长"），
没有任何数字。而阶段 4 做 QLoRA 微调时，能不能塞下、batch 开多大、
序列长度设多少，全靠"每 1K 上下文吃多少显存"这个系数估算——现在不测，
到那时只能靠试错撞。

本机已知基线（2026-08-06 实测，别再当"默认值"猜）：
    当前生效的 num_ctx = 16384
        ← 这是**你之前在桌面端改的**，落库在 %LOCALAPPDATA%\Ollama\db.sqlite
          的 settings 表，不是 Ollama 出厂默认。写结论时直接写数字，别写"默认"
    qwen3.5:27b：训练上下文 262144（256K）、Q4_K_M、27.8B 参数、权重约 17 GB
        ← 也就是说 16384 只用到它上下文能力的 6%
    可用显存 22 GB - 权重 17 GB ≈ 5 GB 留给 KV cache

任务 A：num_ctx → 显存 的定量关系
1. 同一个模型（qwen3.5:27b），num_ctx 取四档：
   **4096 / 8192 / 16384 / 32768**
   —— 为什么从 4K 起步：算系数需要多个**没溢出**的点。16384 已接近本机极限，
      若从它往上排，大概率三档都掉到 CPU，只剩一个可用点连不成线。
      低档位保证落在纯 GPU 区间，最高那档负责去撞天花板
   —— 不用手动改桌面端设置：每次调用显式传 options.num_ctx 就会覆盖它
2. 每档用 `ollama ps` 记录 SIZE 与 CONTEXT 两列
   —— 若某档 CONTEXT 显示的值**小于你传的值**，说明桌面端的 16384 是硬上限，
      那时才需要去 db.sqlite 那个设置里抬高它
   —— CONTEXT 列是**实际生效值**，先确认它真的变了再读显存（E36：
      参数没报错不等于生效）
3. 盯住 PROCESSOR 列：**一旦出现 CPU，说明有层被卸载到内存，那一档就是上限。
   爆掉的那一档本身就是最重要的数据点**，别跳过它
4. 算出「每 1K 上下文 ≈ 多少 MB」，并回答：**这个关系是线性的吗？**
   —— 四档才看得出线性与否，两档只能连出一条直线（ex09 刚验证过这点）
5. 用系数反推 22 GB 下的 num_ctx 上限，与第 3 步实测的爆点对照：
   **估算值和实测值差多少？差值说明你的模型里漏了什么？**

任务 B：27b vs 8b 的速度账（顺手做，成本很低）
1. 拉 `qwen3-vl:8b`（6.1 GB），同一个 prompt 分别跑两个模型
2. 记录 tokens/s（用 `total_tokens / 耗时`，或 `ollama run --verbose` 的统计）
3. 回答一个实际问题：**日常开发调试该常驻哪个？**
   —— 你在 ex07/ex09 已经有精度侧的数据（0.5b 崩、27b 满分），
      补上速度侧就能做取舍

要求/提示：
- **改 num_ctx 走 Ollama 原生端点 `/api/chat` 的 `options` 字段**
  （`{"options": {"num_ctx": 32768}}`）。OpenAI 兼容层 `/v1/chat/completions`
  不认这个字段。实测确认：传 options 会自动触发模型按新 num_ctx 重载，
  不用改环境变量、不用重启服务，而且写在代码里天然可复现
  —— 桌面端点选也能改，但 GUI 操作留不下痕迹，正式测量别用
- 🚨 **每换一档前必须先 `ollama stop <model>`**：不传或复用已加载实例时
  Ollama 不会重载，`ollama ps` 读到的是**上一档的残留**。Claude 演示时
  就踩了这个，差点把 16384 当成出厂默认报出来。
  与 E47（重构丢了循环内赋值 → 三档复用旧结果）是同一个失效模式：
  **状态没刷新，假数据看起来完全合理**
- 用 subprocess 调 `ollama ps` 时，子进程环境要带 `OLLAMA_HOST=127.0.0.1:11434`
  —— 用户级变量是 `0.0.0.0`，CLI 拿它当连接目标会直接失败（本机已知坑，
  报错信息误导性地指向"服务端日志"）
- 显存一律以 `nvidia-smi` 为准，本机 WMI 会误报 4 GB
- `ollama ps` 只统计 Ollama 自身占用，`nvidia-smi` 统计整卡（含桌面合成），
  **同一组实验里别混用两个来源**
- 动手前先在注释里写下**你的预测**：显存与 num_ctx 是什么关系？
  先有假设再测量，才分得清"验证了"和"事后编故事"

完成标准：
- 四档的 CONTEXT / SIZE / PROCESSOR 三列数字 + 每 1K 上下文的 MB 系数
  + 线性与否的判断
- 22 GB 下 27b 的 num_ctx 上限：估算值 vs 实测爆点，以及差值的解释
- 27b / 8b 的 tokens/s 对比 + 一句"常驻哪个"的结论
"""

import json
import os
import urllib.request

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

llm_client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)

url = "http://127.0.0.1:11434/api/chat"


def load_model_with_ctx(num_ctx: int) -> None:

    payload = {
        "model": "qwen3.5:27b",
        "messages": [
            {
                "role": "user",
                "content": "你好，帮我测试一下这个请求。",
            }
        ],
        "stream": False,
        "options": {
            "num_ctx": num_ctx,
        },
    }
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=600) as response:
        response_text = response.read().decode("utf-8")

    result = json.loads(response_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    #  4096 / 8192 / 16384 / 32768 / 65536 / 98304 / 131072
    load_model_with_ctx(81920)


if __name__ == "__main__":
    main()

# 4096
# NAME           ID              SIZE     PROCESSOR    CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    16 GB    100% GPU     4096       4 minutes from now


# 8192
# NAME           ID              SIZE     PROCESSOR    CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    16 GB    100% GPU     8192       4 minutes from now

# 16384
# NAME           ID              SIZE     PROCESSOR    CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    17 GB    100% GPU     16384      4 minutes from now

# 32768
# NAME           ID              SIZE     PROCESSOR    CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    18 GB    100% GPU     32768      4 minutes from now

# 65536
# NAME           ID              SIZE     PROCESSOR    CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    20 GB    100% GPU     65536      4 minutes from now

# 81920
# NAME           ID              SIZE     PROCESSOR          CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    22 GB    11%/89% CPU/GPU    81920      4 minutes from now

# 98304
# NAME           ID              SIZE     PROCESSOR          CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    23 GB    15%/85% CPU/GPU    98304      4 minutes from now

# 131072
# NAME           ID              SIZE     PROCESSOR          CONTEXT    UNTIL
# qwen3.5:27b    7653528ba5cb    26 GB    23%/77% CPU/GPU    131072     4 minutes from now

# 计算1k上下文占用多少M显存，以16384 和 32768 65536 计算
# 16384 ≈ 16k | 17G ≈ 17408M
# 32768 ≈ 32k | 18G ≈ 18432M 增加1024M 计算得 64M/k
# 65536 ≈ 64k | 20G ≈ 20480M 增加2048M 计算的 64M/k
# 在纯 GPU 区间内（16K~64K），显存随 num_ctx 呈线性增长，系数 64 MB/1K

# 溢出之后表观系数变了（98304→131072 算出来是 96 MB/K，不是 64）。溢出区间的数字受四舍五入和 CPU 侧分配策略影响，不适合用来求系数——求系数只能用纯 GPU 的点。

# 计算实际可以用显存 以 98304 和 131072 计算
# 98304 23*0.85 ≈ 19.55G
# 131072 26*0.77 ≈ 20.02

# 以22G显存为例，实际使用建议使用32768 ，因为 65536 已经到达临界值，需要预留显存给其他的应用，浏览器等，

# 按照如上计算结果 ，实际可用显存约为19.78

# 预测81920 会不会爆
# 81920-65536 ≈ 16k | 20G + ((16*64)/1024) ≈ 21G 会超过可用显存

# 实际跑出来是22G 误差来源于显示为G 时候的四舍五入

# 空载时候的 nvidia-smi 显示有桌面应用程序占用约2.2G，符合可用显存的预测
# Fri Aug  7 13:21:25 2026
# +-----------------------------------------------------------------------------------------+
# | NVIDIA-SMI 591.86                 Driver Version: 591.86         CUDA Version: 13.1     |
# +-----------------------------------------+------------------------+----------------------+
# | GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
# |                                         |                        |               MIG M. |
# |=========================================+========================+======================|
# |   0  NVIDIA GeForce RTX 2080 Ti   WDDM  |   00000000:01:00.0  On |                  N/A |
# |  0%   51C    P0             67W /  300W |    2274MiB /  22528MiB |     25%      Default |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+


# 任务B
# qwen3-vl:8b num_ctx:32768 "解释一下幂等性"
# total duration:       26.7041061s
# load duration:        113.265ms
# prompt eval count:    60 token(s)
# prompt eval duration: 57.655ms
# prompt eval rate:     1040.67 tokens/s
# eval count:           1654 token(s)
# eval duration:        26.514279s
# eval rate:            62.38 tokens/s

# qwen3.5:27b num_ctx:32768 "解释一下幂等性"
# total duration:       1m37.3260017s
# load duration:        186.8892ms
# prompt eval count:    47 token(s)
# prompt eval duration: 324.255ms
# prompt eval rate:     144.95 tokens/s
# eval count:           2066 token(s)
# eval duration:        1m36.72847s
# eval rate:            21.36 tokens/s

# 总耗时 26 vs 97
# 两个模型耗差异还是比较明显的，prefill 的差距（7.2x）比生成的差距（2.9x）大得多, 8b 能获得更快的体验
# 初步验证调通为目标的话，使用8B能更快验证
# 验证最终效果，难度较高任务，使用27b 更合适
