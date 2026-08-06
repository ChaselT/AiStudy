"""阶段 1 · 《多模态视觉API》· 动手任务 1

任务：让模型看懂报错截图。
1. 截一张你 IDE 的报错图（真实报错，别用合成的）
2. 用本地 `qwen3.5:27b`（它原生支持看图）或云端 `qwen3.7-plus` 分析报错原因
3. 打印模型的分析，对照你自己的判断，看它说得对不对

要求/提示：
- 图片传参有两种方式：公网 URL 或 base64 data URI；本地图片走 base64
- 图片放本目录下的 `data/`（已被根 `.gitignore` 忽略），别用绝对路径指向
  其他盘符——换台机器就跑不了
- 完成标准：模型的分析与你自己的判断对照，结论写进注释

（对照实验见 `ex09_vision_compare.py`，OCR 结构化见 `ex09_ocr_json.py`）
"""

import base64
import os
import pathlib

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def img_to_data_url(path: pathlib.Path) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.suffix[1:].lower
    return f"data:image/{'jpeg' if ext == 'jpg' else ext};base64,{b64}"


def analysis_error_screenshot() -> str | None:
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这张报错截图是什么问题？给出排查步骤。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_to_data_url(
                                pathlib.Path(__file__).parent / "data" / "bug.png"
                            )
                        },
                    },
                ],
            }
        ],
    )
    return resp.choices[0].message.content


def main() -> None:
    print(analysis_error_screenshot())


if __name__ == "__main__":
    main()

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex09_vision_basic.py
# ## 问题原因

# 报错核心是：

# ```text
# KeyError: 'OPENAI_API_KEY'
# ```

# 出错代码：

# ```python
# client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
# ```

# 表示当前 Python 进程中没有名为 `OPENAI_API_KEY` 的环境变量。程序还没有真正调用 OpenAI API，因此不是图片、模型或网络导致的。

# ---

# ## 排查及解决步骤

# ### 1. 临时设置环境变量

# 在当前 PowerShell 中执行：

# ```powershell
# $env:OPENAI_API_KEY="你的_API_Key"
# ```

# 然后在**同一个 PowerShell 窗口**重新运行：

# ```powershell
# uv run .\ex09_vision_basic.py
# ```

# 验证变量是否已传给 `uv`，又不直接打印密钥：

# ```powershell
# uv run python -c "import os; print(bool(os.getenv('OPENAI_API_KEY')))"
# ```

# 输出 `True` 表示变量存在。

# ---

# ### 2. 使用 `.env` 文件

# 在项目根目录创建 `.env`：

# ```dotenv
# OPENAI_API_KEY=你的_API_Key
# ```

# 然后通过 `uv` 加载：

# ```powershell
# uv run --env-file .env .\ex09_vision_basic.py
# ```

# 如果希望代码自动加载 `.env`，安装依赖：

# ```powershell
# uv add python-dotenv
# ```

# 代码改为：

# ```python
# import os
# from dotenv import load_dotenv
# from openai import OpenAI

# load_dotenv()

# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise RuntimeError("未配置环境变量 OPENAI_API_KEY")

# client = OpenAI(api_key=api_key)
# ```

# 也可以简写为：

# ```python
# load_dotenv()
# client = OpenAI()
# ```

# OpenAI SDK 会自动读取 `OPENAI_API_KEY`。

# > `.env` 应加入 `.gitignore`，不要提交到 Git。

# ---

# ### 3. 永久设置 Windows 用户环境变量

# 在 PowerShell 中执行：

# ```powershell
# [Environment]::SetEnvironmentVariable(
#     "OPENAI_API_KEY",
#     "你的_API_Key",
#     "User"
# )
# ```

# 设置后需要：

# 1. 关闭当前 PowerShell/VS Code；
# 2. 重新打开终端；
# 3. 再运行脚本。

# 也可以在 Windows 的“系统属性 → 环境变量”中手动添加。

# ---

# ## 如果已经配置但仍然报错

# 依次检查：

# 1. 变量名是否完全一致：

#    ```text
#    OPENAI_API_KEY
#    ```

#    注意大小写、空格及拼写。

# 2. 是否在设置变量后换了终端窗口。
#    `$env:...` 只对当前 PowerShell 及其子进程有效。

# 3. `.env` 是否位于当前项目目录：

#    ```powershell
#    Get-Location
#    Test-Path .env
#    ```

# 4. `.env` 是否真的被加载。
#    Python 默认不会自动读取 `.env`，需要 `--env-file` 或 `python-dotenv`。

# 5. 检查 `uv` 子进程能否获取变量：

#    ```powershell
#    uv run python -c "import os; print('已配置' if os.getenv('OPENAI_API_KEY') else '未配置')"
#    ```

# ---

# ## 后续可能出现的错误

# 修复当前 `KeyError` 后，如果出现：

# - `401` / `AuthenticationError`：API Key 无效、过期或账号无权限；
# - `429`：额度不足或请求频率超限；
# - 连接超时：网络、代理或 `base_url` 配置问题；
# - 使用第三方兼容接口：除 API Key 外，通常还需配置对应的 `base_url` 和模型名。

# 不要把真实 API Key 写进截图、源码或提交到代码仓库中。
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api>

# 这个bug是因为我配置文件里面没有OPENAI_API_KEY配置，给出的排查也是对的
