"""阶段 1 · 《多模态视觉API》· 动手任务 3

任务：两组对比实验。

A. 云端 vs 本地——**准确度**
   同一张图表图片（柱状图/折线图，带数字标签）分别发给云端和本地模型，
   要求提取图中数据，逐个数字核对准确度。

B. 图片大小 vs 成本
   同一张图压缩到 1000px 和保持原图各跑一次，对比 `usage.prompt_tokens`
   的差距——体会"图片很贵"。

要求/提示：
- 两组都是对照实验：除了要验证的那一个变量，**其余全部保持一字不动**
  （模型/prompt/temperature/图片内容）。ex07 的 0.5b 对照做得很干净，照那个来
- A 组要有客观判据：先把图里的真实数字抄下来当 ground truth，再逐个比对，
  别凭"感觉差不多"下结论
- B 组注意：图片 token 数与分辨率相关，不同后端的换算规则不同，
  记下你测的是哪个后端
- 压缩用 Pillow（`blog/make_cover.py` 里有现成用法可参考）
- 图片放本目录下的 `data/`（已被根 `.gitignore` 忽略）
- 完成标准：A 组给出"本地模型在哪类图上够用、在哪类上不行"的结论；
  B 组给出压缩前后的 token 数字对比；两组结论都写进本文件注释
"""

import base64
import json
import os
import pathlib
import re
from io import BytesIO
from typing import NamedTuple

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from PIL import Image

from chart_fixture import CHART_DATA


def strip_code_block(text: str) -> str:
    text = text.strip()

    match = re.fullmatch(r"```(?:\w+)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=600.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def img_to_data_url(path: pathlib.Path) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.suffix[1:].lower()
    return f"data:image/{'jpeg' if ext == 'jpg' else ext};base64,{b64}"


def compress_image_to_base64(
    input_path: str | pathlib.Path,
    target_long_side: int = 1000,
) -> str:
    with Image.open(input_path) as opened:
        img: Image.Image = opened.copy()

    width, height = img.size
    scale = target_long_side / max(width, height)

    new_size = (
        round(width * scale),
        round(height * scale),
    )

    img = img.resize(new_size, Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="PNG", optimize=True)

    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{image_base64}"


def build_messages(image_url: str) -> list[ChatCompletionMessageParam]:
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "帮我提取是这张图片的数据,返回格式为dict[str, list[int]]，输出JSON，"
                        "不要返回其他解释信息"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                    },
                },
            ],
        }
    ]


def analysis_chart() -> ChatCompletion:
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=build_messages(
            img_to_data_url(
                pathlib.Path(__file__).parent / "data" / "chart_labeled.png"
            )
        ),
        temperature=0,
    )
    return resp


def compress_analysis_chart(width: int) -> ChatCompletion:
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=build_messages(
            compress_image_to_base64(
                pathlib.Path(__file__).parent / "data" / "chart_labeled.png",
                width,
            )
        ),
        temperature=0,
    )
    return resp


class CompareResult(NamedTuple):
    missing_keys: set[str]
    extra_keys: set[str]
    length_mismatch: dict[str, tuple[int, int]]
    correct: int
    compared: int

    @property
    def accuracy(self) -> float:
        return self.correct / self.compared * 100 if self.compared else 0.0


def compare_chart_data(
    pred: dict[str, list[int]],
    truth: dict[str, list[int]],
) -> CompareResult:
    missing_keys = set(truth) - set(pred)
    extra_keys = set(pred) - set(truth)
    length_mismatch: dict[str, tuple[int, int]] = {}
    correct = 0
    compared = 0

    for key in set(pred) & set(truth):
        pred_values = pred[key]
        truth_values = truth[key]

        if len(pred_values) != len(truth_values):
            length_mismatch[key] = (len(pred_values), len(truth_values))

        for pred_value, truth_value in zip(pred_values, truth_values):
            if pred_value == truth_value:
                correct += 1
            compared += 1

    return CompareResult(
        missing_keys=missing_keys,
        extra_keys=extra_keys,
        length_mismatch=length_mismatch,
        correct=correct,
        compared=compared,
    )


def get_response_text(resp: ChatCompletion) -> str:
    content = resp.choices[0].message.content
    if content is None:
        raise ValueError("模型没有返回文本内容")
    return content


def main() -> None:
    resp = analysis_chart()
    print(f"识别结果:{resp.choices[0].message.content}")
    content = get_response_text(resp)
    result = compare_chart_data(
        json.loads(strip_code_block(content)),
        CHART_DATA,
    )

    if result.missing_keys:
        print(f"缺失键：{sorted(result.missing_keys)}")
    if result.extra_keys:
        print(f"多余键：{sorted(result.extra_keys)}")
    if result.length_mismatch:
        print(f"长度不符：{result.length_mismatch}")

    print(f"准确率为：{result.accuracy:.2f}% ({result.correct}/{result.compared})")

    if resp.usage is not None:
        print(f"输入token消耗：{resp.usage.prompt_tokens}")
        print(f"总token消耗：{resp.usage.total_tokens}")
    for width in [1000, 600, 300]:
        resp = compress_analysis_chart(width)
        print(f"{width}识别结果:{resp.choices[0].message.content}")
        content = get_response_text(resp)
        result = compare_chart_data(
            json.loads(strip_code_block(content)),
            CHART_DATA,
        )

        if result.missing_keys:
            print(f"{width}缺失键：{sorted(result.missing_keys)}")
        if result.extra_keys:
            print(f"{width}多余键：{sorted(result.extra_keys)}")
        if result.length_mismatch:
            print(f"{width}长度不符：{result.length_mismatch}")

        print(
            f"{width}准确率为：{result.accuracy:.2f}% ({result.correct}/{result.compared})"
        )

        if resp.usage is not None:
            print(f"{width}输入token消耗：{resp.usage.prompt_tokens}")
            print(f"{width}总token消耗：{resp.usage.total_tokens}")


if __name__ == "__main__":
    main()

# data/chart_labeled.png 这类图使用本地模型就够用了，识别依旧能达到100%,两类图本地都够用，未能测试出边界
# 云端
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run  .\ex09_vision_compare.py
# 识别结果:{"产品A":[20,30,50,60,80,90,100,110,120,140,150,160],"产品B":[90,100,100,90,80,70,60,50,40,30,30,20],"产品C":[50,70,40,80,60,90,40,90,60,100,50,110]}
# 准确率为：100.00%
# token消耗：1345

# 本地返回的带了代码块，所以加了一个正则处理
# 识别结果:```json
# {
#     "产品A": [20, 30, 50, 60, 80, 90, 100, 110, 120, 140, 150, 160],
#     "产品B": [90, 100, 100, 90, 80, 70, 60, 50, 40, 30, 30, 20],
#     "产品C": [50, 70, 40, 80, 60, 90, 40, 90, 60, 100, 50, 110]
# }
# ```
# 准确率为：100.00%
# token消耗：1067


# data/chart_unlabeled.png 此图本地模型也做到100%识别，
# 本地
# 识别结果:```json
# {
#     "产品A": [
#         20,
#         30,
#         50,
#         60,
#         80,
#         90,
#         100,
#         110,
#         120,
#         140,
#         150,
#         160
#     ],
#     "产品B": [
#         90,
#         100,
#         100,
#         90,
#         80,
#         70,
#         60,
#         50,
#         40,
#         30,
#         30,
#         20
#     ],
#     "产品C": [
#         50,
#         70,
#         40,
#         80,
#         60,
#         90,
#         40,
#         90,
#         60,
#         100,
#         50,
#         110
#     ]
# }
# ```
# 准确率为：100.00%
# token消耗：106

# 线上
# 识别结果:{"产品A":[20,30,50,60,80,90,100,110,120,140,150,160],"产品B":[90,100,100,90,80,70,60,50,40,30,30,20],"产品C":[50,70,40,80,60,90,40,90,60,100,50,110]}
# 准确率为：100.00%
# token消耗：1345


# 使用线上模型进行压缩测试，发现压缩到300的时候，正确率不是100%了，但是随着图片的压缩，消耗的token也逐步下降，所以从成本层面考虑，可以适当压缩图片，但是压缩过头之后，模型就会不确定，输出就变啰嗦，导致输出token变多
# 600px → 总 504 tokens，准确率 100%
# 300px → 总 1582 tokens，准确率 88.89%

# 压到 300px 的总成本是 600px 的 3.1 倍，精度还更差。 所以不是"可以适当压缩"，而是存在一个最优点，600px 就是它——再往下压，省下的输入 token 被暴涨的输出 token 反噬有余。

# 识别结果:{"产品A":[20,30,50,60,80,90,100,110,120,140,150,160],"产品B":[90,100,100,90,80,70,60,50,40,30,30,20],"产品C":[50,70,40,80,60,90,40,90,60,100,50,110]}
# 准确率为：100.00% (36/36)
# 输入token消耗：1345
# 总token消耗：1431
# 1000识别结果:{"产品A":[20,30,50,60,80,90,100,110,120,140,150,160],"产品B":[90,100,100,90,80,70,60,50,40,30,30,20],"产品C":[50,70,40,80,60,90,40,90,60,100,50,110]}
# 1000准确率为：100.00% (36/36)
# 1000输入token消耗：803
# 1000总token消耗：889
# 600识别结果:{"产品A":[20,30,50,60,80,90,100,110,120,140,150,160],"产品B":[90,100,100,90,80,70,60,50,40,30,30,20],"产品C":[50,70,40,80,60,90,40,90,60,100,50,110]}
# 600准确率为：100.00% (36/36)
# 600输入token消耗：308
# 600总token消耗：504
# 300识别结果:{"产品A":[20,30,50,60,70,90,100,110,125,140,150,160],"产品B":[80,100,100,90,80,70,60,50,40,30,30,20],"产品C":[20,70,40,80,60,90,40,90,60,100,50,110]}
# 300准确率为：88.89% (32/36)
# 300输入token消耗：107
# 300总token消耗：1582


# 300px 的失效识别错误，产品A 的80识别成了70,120识别成了125，产品B 第 1 月（90→80）和产品C 第 1 月（50→20），4 个错格里 2 个都在第 1 个月——最左边贴着 Y 轴的位置，marker 和轴线粘连，所以还是不能压缩太狠，
