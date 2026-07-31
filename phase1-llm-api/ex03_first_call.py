"""阶段 1 · 《Chat Completions API》· 动手任务 1

任务：完成人生第一次 LLM API 调用。
1. 用 openai SDK 发一次 chat completions 请求
2. 打印模型回复内容
3. 打印 `resp.usage`（prompt_tokens / completion_tokens / total_tokens）
4. 给 client 配上 `timeout` 和 `max_retries`
5. **把模型名故意写错一次**，捕获 `NotFoundError` 并打印友好提示
   —— 体会"4xx 是请求本身有问题，重试多少次都没用，不该重试"

要求/提示：
- 密钥**必须**走环境变量，先复制 `.env.example` 为 `.env` 填进去
- 后端三件套（LLM_BASE_URL / LLM_API_KEY / LLM_MODEL）已在 .env 里，读它们而不是硬编码
- 完成标准：终端能看到回复正文和 usage 三个数字；错误模型名那次能捕获并友好提示；
  `.env` 不出现在 `git status` 里
"""

# .env 文件内容:  DEEPSEEK_API_KEY=sk-xxxx
# pip install python-dotenv
import os

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def main() -> None:
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {"role": "system", "content": "你是一个乐于助人的助手。"},
            {"role": "user", "content": "用一句话解释什么是幂等性。"},
        ],
    )
    if resp.usage:  # 收窄：这个分支里 resp.usage 一定是 CompletionUsage
        print(resp.choices[0].message.content)
        print(
            f"prompt_tokens:{resp.usage.prompt_tokens},completion_tokens:{resp.usage.completion_tokens},total_tokens:{resp.usage.total_tokens}"
        )
    else:
        print("该后端未返回 usage")

    # 模型错误演示
    try:
        resp = client.chat.completions.create(
            model="gpt-5.8",
            messages=[
                {"role": "system", "content": "你是一个乐于助人的助手。"},
                {"role": "user", "content": "用一句话解释什么是幂等性。"},
            ],
        )
    except openai.RateLimitError as e:  # 429：限流，等一下再来
        retry_after = e.response.headers.get("retry-after", "5")
        print(f"限流，{retry_after}s 后重试")
    except openai.APITimeoutError:  # 超时：可重试
        print("超时，重试或降级到小模型")
    except openai.APIStatusError as e:  # 其他非 2xx
        if e.status_code >= 500:
            print(f"服务端错误 {e.status_code}，可重试")
        else:
            print(f"请求有问题（{e.status_code}），重试也没用：{e.message}")
    except openai.APIConnectionError:  # 网络层失败（代理挂了常见）
        print("连不上，检查网络/代理")


if __name__ == "__main__":
    main()

# 幂等性是指一个操作执行一次或重复执行多次，产生的最终结果都相同。
# prompt_tokens:30,completion_tokens:28,total_tokens:58
# 请求有问题（404），重试也没用：Error code: 404 - {'error': {'message': 'Model "gpt-5.8" is not supported by any configured account in this group', 'type': 'model_not_found'}}
