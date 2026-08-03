"""阶段 1 · 《流式输出与SSE》· 动手任务 2

任务：把多轮对话改造成流式版。
1. 以 `ex03_multi_turn.py` 为基础，把每轮回复改成流式逐字输出
2. 关键点：流式模式下没有现成的完整回复字符串，你要**自己把 chunk 拼起来**
   再回填进 messages，否则历史里存的是空的
3. 验证：报名字 → 下一轮问名字，确认记忆正常

要求/提示：
- 这是最容易踩的坑：流式打印爽了，忘了拼接回填，于是模型每轮都失忆
- 完成标准：流式输出正常 + 多轮记忆正常，两件事同时成立
"""

import asyncio
import os

import openai
from dotenv import load_dotenv

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

client = openai.AsyncOpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=600.0,
    max_retries=3,  # 换 base_url 即换供应商
)


async def llm_call(message: list) -> list[str] | str:
    # 模型错误演示
    try:
        resp: list[str] = []
        stream = await client.chat.completions.create(
            model=os.environ["LLM_MODEL"],
            messages=message,
            stream=True,
        )
        async for chunk in stream:  # 注意是 async for
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
                resp.append(delta)
        print()
        return resp
    except openai.APIConnectionError:
        print(f"\n[流中断，已收到 {len(''.join(resp))} 字，可选择重试或用已有内容降级]")
        return f"\n[流中断，已收到 {len(''.join(resp))} 字，可选择重试或用已有内容降级]"


async def main() -> None:
    messages = [{"role": "system", "content": "你是一个助手。"}]
    while True:
        text = input("请输入内容（/exit 退出）")
        if text.lower() == "/exit":
            break
        message = {"role": "user", "content": text}
        messages.append(message)
        resp = await llm_call(messages)
        if isinstance(resp, str):
            print(resp)
            continue
        else:
            messages.append({"role": "assistant", "content": "".join(resp) or ""})


if __name__ == "__main__":
    asyncio.run(main())

# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex05_stream_chat.py
# 请输入内容（/exit 退出）帮我取一个昵称
# 没问题！取昵称主要看你喜欢的风格和使用场景。为了给你推荐更合适的，我把它们分成了几类，你可以看看有没有一眼相中的：

# ### 🍬 可爱俏皮风（适合社交、游戏）
# 1. **软糖星球** (甜度满分)
# 2. **口袋里的喵** (萌宠感)
# 3. **橘子汽水味** (夏日清新)
# 4. **咕噜小鱼干** (呆萌活泼)
# 5. **月亮私奔计划** (有点小脑洞)

# ### 🌙 文艺古风（适合读书、朋友圈）
# 1. **听风吟雪** (意境深远)
# 2. **云深几许** (清冷神秘)
# 3. **墨染山河** (大气磅礴)
# 4. **半盏流年** (时光感)
# 5. **扶苏** / **子衿** (取自诗经，典雅)

# ### ❄️ 简约高冷风（适合职场、商务）
# 1. **零度** (冷淡疏离)
# 2. **北野** (干净利落)
# 3. **默然** (少言寡语)
# 4. **极光以北** (遥远美好)
# 5. **K.** (单字母，极简酷感)

# ### 😂 搞怪有趣风（适合游戏、群聊）
# 1. **幼儿园老大** (反差萌)
# 2. **干饭第一名** (实在接地气)
# 3. **睡不醒的考拉** (咸鱼属性)
# 4. **对方正在输入...** (恶作剧感)
# 5. **退堂鼓一级演奏家** (自嘲有趣)

# ### 🌟 英文/双语系（适合邮箱、国际社交）
# 1. **Starry** (星光般的)
# 2. **Echo** (回声，念念不忘之意)
# 3. **Ivy** (常春藤，象征生命力)
# 4. **BlueMoon** (稀有难得)
# 5. **Aura** (气场/光晕)

# ---

# 💡 **小贴士：如何打造专属昵称？**
# *   **加特殊符号：** 比如 `☁️云朵`、`_小呆.` 或 `[Momo]`。
# *   **结合爱好：** 如果你爱咖啡，可以叫“拿铁不加糖”；喜欢音乐，可以是“第 N 个音符”。
# *   **谐音梗：** 比如把名字里某个字换成同音的有趣词（如：钱进 -> 贱人...划掉 -> 简宁）。

# **你更倾向于哪种风格？** 或者你可以告诉我你的性别、年龄范围，或者是想在什么平台用（微信、游戏、小红书？），我可以为你定制几个更精准的！
# 请输入内容（/exit 退出）直接帮我取一个
# 给你定了一个：

# **「拾光者」** ✨

# *寓意：收集生活中的美好时光，温暖又不失格调。如果不喜欢这个风格（比如太文艺或太长），随时告诉我，我马上换一个！*
# 请输入内容（/exit 退出）可以，还不错
# 太好了！很高兴你满意～ 😊

# 这个名字自带温暖的感觉，寓意也不错。**如果你想让它更不容易重名**，可以稍微加一点点“装饰”，比如：

# *   ➖ **拾光者-** (极简线条感)
# *   ✨ **拾光者.** (加点小点缀)
# *   🗝️ **KeyTo拾光** (中英文结合)

# 祝你的新昵称能带来好心情！如果有其他需要随时喊我～
# 请输入内容（/exit 退出）你给我取的昵称是什么
# 我刚才给你取的是：

# **「拾光者」** ✨

# （意思是“收集生活中闪光的美好瞬间”，感觉挺有温度名字的，你印象里有这个吗？😄）
# 请输入内容（/exit 退出）

# 记忆正常
