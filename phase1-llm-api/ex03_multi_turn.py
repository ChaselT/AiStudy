"""阶段 1 · 《Chat Completions API》· 动手任务 2

任务：实现终端多轮对话循环。
1. 用 `while True` + `input()` 做一个可以连续聊天的终端程序
2. 维护 messages 列表：每轮把用户输入 append 进去，把模型回复也 append 回去
3. 验证记忆：先告诉它"我叫 XXX"，下一轮问"我叫什么"，确认它记得
4. 破坏性实验：故意注释掉**回填 assistant 消息**的那一行，再跑一次，
   观察"失忆"现象，把结论写进注释

要求/提示：
- 加个退出条件（如输入 `/exit` 或 `quit` 时 break），别让自己 Ctrl+C 退出
- 核心认知：API 无状态，"记忆"完全是你每次把历史重发一遍造出来的假象
- 完成标准：正常版记得名字，注释掉回填的版本记不住；两种现象都亲眼看到
"""

import os

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletion

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def llm_call(message: list) -> ChatCompletion | str:
    # 模型错误演示
    try:
        resp = client.chat.completions.create(
            model=os.environ["LLM_MODEL"], messages=message
        )
        return resp
    except openai.RateLimitError as e:  # 429：限流，等一下再来
        retry_after = e.response.headers.get("retry-after", "5")
        print(f"限流，{retry_after}s 后重试")
        return "限流了，请稍后再试"
    except openai.APITimeoutError:  # 超时：可重试
        print("超时，重试或降级到小模型")
        return "请稍后再试"
    except openai.APIStatusError as e:  # 其他非 2xx
        if e.status_code >= 500:
            print(f"服务端错误 {e.status_code}，可重试")
            return "请稍后再试"
        else:
            print(f"请求有问题（{e.status_code}），重试也没用：{e.message}")
            return "请求失败，请检查参数"
    except openai.APIConnectionError:  # 网络层失败（代理挂了常见）
        print("连不上，检查网络/代理")
        return "请求失败，请检查网络"


def main() -> None:
    messages = [{"role": "system", "content": "你是一个助手。"}]
    while True:
        text = input("请输入内容（/exit 退出）")
        if text.lower() == "/exit":
            break
        message = {"role": "user", "content": text}
        messages.append(message)
        resp = llm_call(messages)
        if isinstance(resp, str):
            print(resp)
            continue
        else:
            print(resp.choices[0].message.content)
            messages.append(
                {"role": "assistant", "content": resp.choices[0].message.content or ""}
            )


if __name__ == "__main__":
    main()

# 注释掉assistant，然后复现失忆bug，表现为帮我取外号麦仔，再次询问我外号是什么，变成了麦芒
# 请输入内容（/exit 退出）你好，我是mike
# 你好，Mike！很高兴认识你。有什么我可以帮你的吗？
# 请输入内容（/exit 退出）我是谁
# 你是 Mike。
# 请输入内容（/exit 退出）你帮我取一个外号
# 你是 Mike！我给你取个外号叫 **“麦仔”**，听起来亲切又好记 😄
# 请输入内容（/exit 退出）我的代号是什么
# 你的代号是：**麦芒** 🌾
# 取自 Mike 的“麦”，寓意锋芒与活力。

# 正常对话
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex03_multi_turn.py
# 请输入内容（/exit 退出）你好，帮我取一个外号
# 当然！先送你一个百搭又好听的外号：**「小满」**——寓意恰到好处、常有欢喜，也很亲切。

# 如果你告诉我你的**性格、名字、爱好**，以及想要的风格（可爱、霸气、搞笑、酷炫、文艺），我还能帮你定制几个更适合的。
# 请输入内容（/exit 退出）我的外号是什么
# 你的外号是：**小满** 🌱
# 请输入内容（/exit 退出）/exit
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api>
