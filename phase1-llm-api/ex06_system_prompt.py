"""阶段 1 · 《Prompt工程》· 动手任务 1

任务：实现笔记里的"代码评审员"system prompt。
1. 按笔记里的模板写一个 system prompt：角色 + 任务 + 约束 + 输出格式
2. 喂一段**有明显 bug** 的 Java 代码给它（自己造一段，比如空指针、资源没关、
   循环边界错），看它能不能指出来
3. 越界测试：接着问它"今天天气如何"，验证它按约束**拒答**并把话题拉回代码评审
4. 对比实验：把 system prompt 删掉，同样两个问题再问一遍，记录差异

要求/提示：
- system prompt 当代码写：分段、有结构、约束写清楚（类比给下游服务写接口契约）
- 完成标准：有 system prompt 时能拒答越界问题，没有时会老实回答天气——差异写进注释
"""

import os
import pathlib

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletion

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=300.0,
    max_retries=3,  # 换 base_url 即换供应商
)

system_prompt = (
    pathlib.Path(__file__).parent / "prompts" / "code_reviewer.md"
).read_text(encoding="utf-8")


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
    #  messages = [{"role": "system", "content": system_prompt}]
    messages = []
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
# 有明确的 system prompt 时，模型拒答了越界问题（今天天气如何），并提醒用户回到代码评审主题。
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex06_system_prompt.py
# 请输入内容（/exit 退出）int result = 10 / 0;
# 在这个特定的Java表达式中，会引发一个除以零错误。在进行任何算术运算之前，确保输入的数据不会为零。

# ```java
# String str = "example";
# result = Integer.parseInt(str);
# ```
# 在计算字符串`"example"`的整数（转换成整型）后，会导致运行时异常并抛出以下错误:
# ```
# NumberFormatException:
# Expected a 16-bit, 32-bit or 64-bit signed integer
# ```
# 请输入内容（/exit 退出）今天天气怎么样
# 你的提问与编程无关，请提问关于编写代码相关的问题。如果你有其他问题，我会很乐意帮助你。

# system prompt 里面禁止讨论无关的规则被删掉后，模型会大概围绕角色等信息来回答这个天气问题，但是不会明确。
#  删掉拒答规则后，模型不会拒绝、也不会正常回答，而是被角色设定绑架——把无关问题强行套进"代码评审"框架，编出一个不存在的 Weather 类并一本正经地评审。这比跑题更危险：角色设定让它保持了专业口吻，但内容完全是编的。
# ▎ 结论：角色设定管"怎么理解"，拒答规则管"要不要答"，两者缺一不可。
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex06_system_prompt.py
# 请输入内容（/exit 退出）int result = 10 / 0;
# 这个表达式会导致一个 ` ArithmeticException`（除以零错误），因为在 Java 中可以使用 `/` 来对整数进行除法运算。为了修复这个问题，应该将其替换为：
# ```java
# int result = (int) (10 / 0);
# ```

# 这样代码就能正确地处理除以零的情况。

# ### 可能的改进建议
# 1. 如果需要提高兼容性或功能，请提供更具体的上下文说明。
# 请输入内容（/exit 退出）今天天气怎么样
# 这段 Java 代码看起来是用于计算今天的天气情况，但如果使用 `int` 类型的变量和方法来实现这个逻辑有些混乱，建议将整数类型的取模（取余）操作转换成更具结构化形式或者函数式方法。例如：

# ```java
# import java.util.Calendar;

# class Weather {
#     private final Calendar date = Calendar.getInstance();

#     /**
#      * Calculate the number of days between today and the day of the month for a given year.
#      */
#     public long calculateDays(long dateInt) {
#         return (dateInt - 1) / 1024;
#     }
# }
# ```

# 这样将 `int result` 变量改为 `(date.get(Calendar.DAY_OF_MONTH) - 1)`。

# 删除整个 system prompt 后，模型会老实回答天气问题，而不是拒答。
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex06_system_prompt.py
# 请输入内容（/exit 退出）int result = 10 / 0;
# 运行如下代码： int result = 10 / 0;
# 由于在除法运算中，当被除数（10）为零时，将会引发"divide-by-zero error"（除以零错误），导致程序无法正常执行。所以在这种情况下我们可以通过添加控制台提示或者异常处理来预防或修复这个问题。
# 例如，可以添加以下的调试操作（注意此处代码仅为示例和解释）：

# ```python
# int result = 10 / 0; // 运行这段代码
# ```

# 这个程序会因为除以零产生一个错误。为了简化我们的理解，在此情况下我们可以忽略运行这种运算，并显示了一个提示，让用户知道程序运行出现了问题。

# 另外一种预防办法可以使用异常处理：
# ```python
# try:
#     result = 10 / 0;
# except ZeroDivisionError:
#    # 对于可能的除以零的情况，此处应添加错误处理代码
#    print("错误：正在尝试执行 10 / 0")
# ```
# 当出现“divide-by-zero error”时会立即输出错误信息并保持程序状态。
# 请输入内容（/exit 退出）今天天气怎么样
# 很抱歉，我无法直接获取实时或特定地区的真实天气情况，包括明天的天气预报。不过，在线上的气象网站，如Weather.com、Weather站等都可以提供不同地区的近期天气预报。

# 如果您希望查询更近地当前和未来的天气情况，请尝试访问以下站点：

# 1. 中国的国家气象信息网：[天气在线](http://weather.163.com/)
# 2. 德国的天气预报（以德国为例）：[德云气象页面](https://www.taqk.de/weather/de)

# 请确保在访问上述网站时使用正确的域名和IP地址，并且考虑到地区的气候差异，有些地方可能有当地的特殊天气特征。最好提前查询以便获取准确的信息。
# 请输入内容（/exit 退出）
