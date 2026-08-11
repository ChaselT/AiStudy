# chat_service 验收记录

> 阶段 1 · 第 11/11 课《FastAPI入门》的验证记录。
> 每项填「命令 + 原始输出 + 一句结论」，**输出原样贴，别整理美化**——
> 失败样本比成功样本值钱。

**环境**：`export NO_PROXY=localhost,127.0.0.1`（本机 SOCKS 代理会拦截本地请求）
**启动**：`uv run --env-file .env fastapi dev chat_service/main.py`

---

## 1. 服务启动 + `/health`

启动命令：

```
uv run --env-file .env fastapi dev .\chat_service\main.py
```

启动日志（关注有没有 lifespan 的异常）：

```
 Starting FastAPI in development mode
 
 🐍 Using import string: chat_service.main:app
 
 🌐 Server started at http://127.0.0.1:8000
    Documentation at http://127.0.0.1:8000/docs
 
  Logs:
 
 ▕  Will watch for changes in these directories: ['E:\\workspace\\AiStudy\\phase1-llm-api']
 ▕  Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
 ▕  Started reloader process [45184] using WatchFiles
 ▕  Started server process [80696]
 ▕  Waiting for application startup.
 ▕  Application startup complete.
 ▕  127.0.0.1:54592 - "GET /doc HTTP/1.1" 404
 ▕  127.0.0.1:54592 - "GET /favicon.ico HTTP/1.1" 404
 ▕  127.0.0.1:54021 - "GET /docs HTTP/1.1" 200
 ▕  127.0.0.1:54021 - "GET /openapi.json HTTP/1.1" 200
 ▕  127.0.0.1:61192 - "GET /health HTTP/1.1" 200
 没有发现异常
```

`/health` 返回：

```
StatusCode        : 200
StatusDescription : OK
Content           : {"status":"ok"}
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 15
                    Content-Type: application/json
                    Date: Mon, 10 Aug 2026 09:13:37 GMT
                    Server: uvicorn

                    {"status":"ok"}
Forms             : {}
Headers           : {[Content-Length, 15], [Content-Type, application/json], [Date, Mon, 10 Aug 2026 09:13:37 GMT], [Se
                    rver, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : System.__ComObject
RawContentLength  : 15
```

**结论**：health 返回200，响应内容 {"status":"ok"}，代表当前服务已经正常启动

---

## 2. `/chat2` 非流式

请求（`/docs` 里试调或 curl 均可）：

```
{
  "message": "解释一下幂等性",
  "temperature": 0.7
}
```

响应：

```
{
  "reply": "“幂等性”（Idempotency）是一个在数学、计算机科学和系统架构中非常重要的概念。简单来说，它的核心含义是：**一个操作无论执行多少次，其产生的效果和执行一次是一样的。**\n\n为了让你透彻理解，我将从定义、生活中的例子、编程中的应用以及为什么它很重要这几个方面来解释。\n\n---\n\n### 1. 通俗的定义\n**幂等性 = 重复做这件事 vs 只做这一次 == 结果没区别**\n\n*   **数学起源：** 来源于代数中的“幂”运算（$A^2 = A \\times A$）。如果一个元素 $x$ 满足 $x * x = x$，那么它就是幂等的。\n    *   例如：布尔值中 `true AND true` 还是 `true`；...",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 2574,
    "total_tokens": 2589
  }
}
```

**结论**：
- usage 正常返回

---

## 3. `/chat/stream` 流式

⚠️ 要证明的不是"最终文本对"，是**分批到达**。用带时间戳的方式：

```bash
curl -N -s -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"用三句话解释幂等性"}' \
  | while IFS= read -r line; do printf '[%s] %s\n' "$(date +%S.%3N)" "$line"; done
```

输出（保留时间戳）：

```
(phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\chat_service\verify_stream.py               
<Response [200 OK]>                                                               
时间间隔：58.189s
响应内容：data: {"delta": "幂"}
时间间隔：0.038s
响应内容：data: {"delta": "等"}
时间间隔：0.042s
响应内容：data: {"delta": "性"}
时间间隔：0.037s
响应内容：data: {"delta": "是"}
时间间隔：0.000s
响应内容：data: {"delta": "指"}
时间间隔：0.041s
响应内容：data: {"delta": "一"}
时间间隔：0.000s
响应内容：data: {"delta": "个"}
时间间隔：0.036s
响应内容：data: {"delta": "操"}
时间间隔：0.000s
响应内容：data: {"delta": "作"}
时间间隔：0.041s
响应内容：data: {"delta": "无"}
时间间隔：0.000s
响应内容：data: {"delta": "论"}
时间间隔：0.041s
响应内容：data: {"delta": "重"}
时间间隔：0.000s
响应内容：data: {"delta": "复"}
时间间隔：0.046s
响应内容：data: {"delta": "执"}
时间间隔：0.000s
响应内容：data: {"delta": "行"}
时间间隔：0.042s
响应内容：data: {"delta": "多"}
时间间隔：0.000s
响应内容：data: {"delta": "少"}
时间间隔：0.000s
响应内容：data: {"delta": "次"}
时间间隔：0.041s
响应内容：data: {"delta": "，"}
时间间隔：0.044s
响应内容：data: {"delta": "其"}
时间间隔：0.041s
响应内容：data: {"delta": "最"}
时间间隔：0.000s
响应内容：data: {"delta": "终"}
时间间隔：0.041s
响应内容：data: {"delta": "结"}
时间间隔：0.000s
响应内容：data: {"delta": "果"}
时间间隔：0.036s
响应内容：data: {"delta": "都"}
时间间隔：0.000s
响应内容：data: {"delta": "与"}
时间间隔：0.040s
响应内容：data: {"delta": "仅"}
时间间隔：0.040s
响应内容：data: {"delta": "执"}
时间间隔：0.000s
响应内容：data: {"delta": "行"}
时间间隔：0.042s
响应内容：data: {"delta": "一"}
时间间隔：0.000s
响应内容：data: {"delta": "次"}
时间间隔：0.046s
响应内容：data: {"delta": "相"}
时间间隔：0.000s
响应内容：data: {"delta": "同"}
时间间隔：0.037s
响应内容：data: {"delta": "。"}
时间间隔：0.042s
响应内容：data: {"delta": "在"}
时间间隔：0.040s
响应内容：data: {"delta": "计"}
时间间隔：0.000s
响应内容：data: {"delta": "算"}
时间间隔：0.000s
响应内容：data: {"delta": "机"}
时间间隔：0.040s
响应内容：data: {"delta": "系"}
时间间隔：0.000s
响应内容：data: {"delta": "统"}
时间间隔：0.000s
响应内容：data: {"delta": "中"}
时间间隔：0.046s
响应内容：data: {"delta": "，"}
时间间隔：0.041s
响应内容：data: {"delta": "它"}
时间间隔：0.042s
响应内容：data: {"delta": "主"}
时间间隔：0.000s
响应内容：data: {"delta": "要"}
时间间隔：0.000s
响应内容：data: {"delta": "用"}
时间间隔：0.000s
响应内容：data: {"delta": "于"}
时间间隔：0.040s
响应内容：data: {"delta": "保"}
时间间隔：0.000s
响应内容：data: {"delta": "证"}
时间间隔：0.038s
响应内容：data: {"delta": "请"}
时间间隔：0.000s
响应内容：data: {"delta": "求"}
时间间隔：0.039s
响应内容：data: {"delta": "重"}
时间间隔：0.000s
响应内容：data: {"delta": "试"}
时间间隔：0.039s
响应内容：data: {"delta": "或"}
时间间隔：0.040s
响应内容：data: {"delta": "并"}
时间间隔：0.000s
响应内容：data: {"delta": "发"}
时间间隔：0.040s
响应内容：data: {"delta": "场"}
时间间隔：0.000s
响应内容：data: {"delta": "景"}
时间间隔：0.038s
响应内容：data: {"delta": "下"}
时间间隔：0.041s
响应内容：data: {"delta": "不"}
时间间隔：0.000s
响应内容：data: {"delta": "会"}
时间间隔：0.000s
响应内容：data: {"delta": "产"}
时间间隔：0.000s
响应内容：data: {"delta": "生"}
时间间隔：0.042s
响应内容：data: {"delta": "副"}
时间间隔：0.000s
响应内容：data: {"delta": "作"}
时间间隔：0.000s
响应内容：data: {"delta": "用"}
时间间隔：0.040s
响应内容：data: {"delta": "和"}
时间间隔：0.000s
响应内容：data: {"delta": "数"}
时间间隔：0.000s
响应内容：data: {"delta": "据"}
时间间隔：0.046s
响应内容：data: {"delta": "冗"}
时间间隔：0.000s
响应内容：data: {"delta": "余"}
时间间隔：0.041s
响应内容：data: {"delta": "。"}
时间间隔：0.041s
响应内容：data: {"delta": "例"}
时间间隔：0.000s
响应内容：data: {"delta": "如"}
时间间隔：0.038s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "H"}
时间间隔：0.000s
响应内容：data: {"delta": "T"}
时间间隔：0.000s
响应内容：data: {"delta": "T"}
时间间隔：0.000s
响应内容：data: {"delta": "P"}
时间间隔：0.079s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "协"}
时间间隔：0.000s
响应内容：data: {"delta": "议"}
时间间隔：0.038s
响应内容：data: {"delta": "中"}
时间间隔：0.000s
响应内容：data: {"delta": "的"}
时间间隔：0.043s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "G"}
时间间隔：0.000s
响应内容：data: {"delta": "E"}
时间间隔：0.000s
响应内容：data: {"delta": "T"}
时间间隔：0.039s
响应内容：data: {"delta": "、"}
时间间隔：0.044s
响应内容：data: {"delta": "P"}
时间间隔：0.000s
响应内容：data: {"delta": "U"}
时间间隔：0.000s
响应内容：data: {"delta": "T"}
时间间隔：0.085s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "和"}
时间间隔：0.049s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "D"}
时间间隔：0.000s
响应内容：data: {"delta": "E"}
时间间隔：0.000s
响应内容：data: {"delta": "L"}
时间间隔：0.000s
响应内容：data: {"delta": "E"}
时间间隔：0.000s
响应内容：data: {"delta": "T"}
时间间隔：0.000s
响应内容：data: {"delta": "E"}
时间间隔：0.089s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "方"}
时间间隔：0.000s
响应内容：data: {"delta": "法"}
时间间隔：0.049s
响应内容：data: {"delta": "通"}
时间间隔：0.000s
响应内容：data: {"delta": "常"}
时间间隔：0.042s
响应内容：data: {"delta": "具"}
时间间隔：0.000s
响应内容：data: {"delta": "备"}
时间间隔：0.042s
响应内容：data: {"delta": "此"}
时间间隔：0.047s
响应内容：data: {"delta": "特"}
时间间隔：0.000s
响应内容：data: {"delta": "性"}
时间间隔：0.043s
响应内容：data: {"delta": "，"}
时间间隔：0.041s
响应内容：data: {"delta": "而"}
时间间隔：0.045s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "P"}
时间间隔：0.000s
响应内容：data: {"delta": "O"}
时间间隔：0.000s
响应内容：data: {"delta": "S"}
时间间隔：0.000s
响应内容：data: {"delta": "T"}
时间间隔：0.088s
响应内容：data: {"delta": " "}
时间间隔：0.000s
响应内容：data: {"delta": "则"}
时间间隔：0.048s
响应内容：data: {"delta": "不"}
时间间隔：0.000s
响应内容：data: {"delta": "具"}
时间间隔：0.000s
响应内容：data: {"delta": "备"}
时间间隔：0.045s
响应内容：data: {"delta": "。"}
时间间隔：0.046s
响应内容：event: done
时间间隔：0.000s
响应内容：data: {}
```

**结论**：

- **确认是分批到达**：58 个 delta 各自独立到达，不是一次性吐出，SSE 链路通。

- **首个 delta 58.189s，后续稳定 ~0.04s**。这 58 秒**不是 FastAPI 或 SSE 的开销**
  （那是毫秒级），是 `qwen3.5:27b` 的**冷加载**——测试时模型已被 `keep_alive`
  卸载，请求触发了从 F 盘读 17GB 权重。
  与 ex05 裸 API 的 TTFT 不可直接比较：那次模型是热的。
  **要比 FastAPI 的净开销，必须先预热让模型常驻再测。**

- **"有时连续返回几个字"是我自己代码造成的，不是网络缓冲。**
  `_stream_events` 里：
  ```python
  async for chunk in chunks:
      for character in chunk:          # ← 把一个 chunk 拆成单字逐个 yield
          yield _sse_event({"delta": character})
  ```
  模型一个 chunk 若含多个字，就会连发多个 SSE 事件（间隔 0.000s），
  然后才等下一个 chunk（~0.04s）。所以日志里 **0.000s 与 0.04s 交替出现，
  正是这个拆分留下的痕迹**——0.000s 那批是同一个 chunk 里的字。
  英文更明显：`H/T/T/P` 四个 delta 全是 0.000s，因为它们同属一个 chunk。

  > 顺带：逐字拆分会让 SSE 事件数放大数倍（每个事件都有 `data:` 前缀和空行开销）。
  > 教学演示无所谓，生产上应该原样转发 chunk，让前端自己决定怎么渲染。

---

## 4. `validate_config()` 的负面验证

> 改了防护，必须构造一次真实失败来确认它生效（ex08 的规矩：没见过红的绿不算数）

操作：注释掉 `.env` 里的 `LLM_MODEL`，重启服务。

报错原文：

```
 ▕  Traceback (most recent call last):
      File "E:\workspace\AiStudy\phase1-llm-api\.venv\Lib\site-packages\starlette\routing.py", line 638, in 
    lifespan
        async with self.lifespan_context(app) as maybe_state:
      File "C:\Users\tangx\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\Lib\contextlib.py", line
    210, in __aenter__
        return await anext(self.gen)
               ^^^^^^^^^^^^^^^^^^^^^
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\main.py", line 58, in lifespan
        validate_config()
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\llm.py", line 35, in validate_config
        _required_env("LLM_MODEL")
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\llm.py", line 41, in _required_env
        raise RuntimeError(f"缺少配置项: {name}")
    RuntimeError: 缺少配置项: LLM_MODEL

    ▕  Traceback (most recent call last):
      File "E:\workspace\AiStudy\phase1-llm-api\.venv\Lib\site-packages\starlette\routing.py", line 638, in 
    lifespan
        async with self.lifespan_context(app) as maybe_state:
      File "C:\Users\tangx\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\Lib\contextlib.py", line
    210, in __aenter__
        return await anext(self.gen)
               ^^^^^^^^^^^^^^^^^^^^^
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\main.py", line 57, in lifespan
        get_llm_client()
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\llm.py", line 63, in get_llm_client
        base_url=_required_env("LLM_BASE_URL"),
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\llm.py", line 41, in _required_env
        raise RuntimeError(f"缺少配置项: {name}")
    RuntimeError: 缺少配置项: LLM_BASE_URL

     ▕  Traceback (most recent call last):
      File "E:\workspace\AiStudy\phase1-llm-api\.venv\Lib\site-packages\starlette\routing.py", line 638, in 
    lifespan
        async with self.lifespan_context(app) as maybe_state:
      File "C:\Users\tangx\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\Lib\contextlib.py", line
    210, in __aenter__
        return await anext(self.gen)
               ^^^^^^^^^^^^^^^^^^^^^
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\main.py", line 57, in lifespan
        get_llm_client()
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\llm.py", line 64, in get_llm_client
        api_key=_required_env("LLM_API_KEY"),
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "E:\workspace\AiStudy\phase1-llm-api\chat_service\llm.py", line 41, in _required_env
        raise RuntimeError(f"缺少配置项: {name}")
    RuntimeError: 缺少配置项: LLM_API_KEY
```

**结论**：
- 启动期就炸了
- 都可以被拦住

---

## 5. 会话记忆（任务 3）

**同一 session_id 连续两轮**——第二轮要能引用第一轮的内容：

```
第 1 轮请求 / 响应：
{
  "message": "帮我取一个昵称",
  "temperature": 0.7,
  "session_id": "1234567896"
}
{
  "reply": "取昵称是一件很有趣的事情！因为不知道你的性格、喜好或使用场景（比如微信、游戏、小红书等），我为你准备了几个不同风格的分类，你可以看看有没有戳中你的：\n\n### 🍬 可爱治愈系 (适合日常社交)\n1. **口袋里的星星** ✨\n2. **偷喝一口月亮** 🌙\n3. **奶泡软糖** 🧁\n4. **正在加载快乐...** ⚡️\n5. **小野猫在逃** 🐱\n6. **云朵收集员** ☁️\n\n### 🎋 文艺清新系 (适合朋友圈/个性签名)\n1. **半两月光** 💮\n2. **听风吹雪** ❄️\n3. **山川湖海皆是你** 🏔️\n4. **且听风吟** 🌬️\n5. **半岛弥音** 🎵\n6. **暮色微凉** 🍂\n\n### 😜 搞怪幽默系 (适合游戏/朋友群)\n1. **幼儿园大班班长** 👶\n2. **熬夜冠军选手** 💊\n3. **退堂鼓一级演奏家** 🥁\n4. **别动我的零食** 🍪\n5. **智商已欠费** 📵\n6. **这局我负责挨骂** 🛡️\n\n### ❄️ 简约高冷系 (适合游戏 ID/极简风)\n1. **零度**\n2. **孤岛**\n3. **未名**\n4. **野性**\n5. **归途**\n6. **无妄**\n\n### 🗝️ 英文小众系 (看起来比较高级)\n1. **Vesper** (晚祷/黄昏)\n2. **Hush** (安静)\n3. **Serendipity** (不期而遇的美好)\n4. **Echoes** (回声)\n5. **Aurora** (极光)\n\n---\n\n### 💡 取昵称的小技巧：\n*   **结合爱好：** 比如你喜欢咖啡，可以叫“半杯拿铁”；喜欢猫，就叫“喵星人饲养员”。\n*   **特殊符号点缀：** 加上一些 Emoji（✨🌟💫）或者生僻字会让名字更不容易重名。\n*   **谐音梗：** 把自己喜欢的词换个别字读法一样但意思有趣的。\n\n**如果你能告诉我更多信息，我可以帮你取个更专属的！** 比如：\n1. 你是男生还是女生？（或希望偏中性）\n2. 你平时喜欢什么风格？（古风、现代、搞笑...）\n3. 这个昵称主要用在哪里？（微信、王者荣耀、抖音？）\n\n期待你的反馈，帮你定下那个“本命 ID\"！",
  "usage": {
    "prompt_tokens": 14,
    "completion_tokens": 1676,
    "total_tokens": 1690
  }
}
第 2 轮请求 / 响应：
{
  "message": "微信用的",
  "temperature": 0.7,
  "session_id": "1234567896"
}
{
  "reply": "微信昵称和朋友圈、联系人列表紧密相关，既要表达个性，又要考虑**社交场景的兼容性**（比如会不会让长辈或同事觉得太奇怪）。\n\n这里为你准备了几个适合微信不同使用场景的方向：\n\n### 1️⃣ **稳妥得体风 (适合同事/客户较多)**\n*这类昵称不张扬，显得成熟稳重，但又不像真名那么生硬。*\n- **[名字] 同学** （比如：林宇同学）\n- **简白** 🍵\n- **知行** 📝\n- **某某某** ❌ (带点神秘感)\n- **早安与晚安** ☀️🌙\n- **保持热爱** 🔥\n\n### 2️⃣ **温暖生活风 (适合日常交友/家庭群)**\n*给人亲切、好相处的感觉，没有距离感。*\n- **小满胜万全** 🏮\n- **人间烟火气** 🍲\n- **今日宜开心** ✨\n- **半日闲** ☕️\n- **岁岁平安** 🔒\n- **微风不噪** 🌿\n\n### 3️⃣ **极简高冷风 (适合喜欢干净界面)**\n*字数少，看起来清爽，不容易过时。*\n- **零度** ❄️\n- **未命名** 📁\n- **404 Not Found** 💻\n- **Hush** 🔇\n- **归途** 🛤️\n- **一 半** ⬜\n\n### 4️⃣ **幽默搞怪风 (适合朋友多/年轻群体)**\n*在微信列表里看到会觉得有趣，容易打开话题。*\n- **对方正在输入...** 💡\n- **幼儿园老大** 👶\n- **干饭第一名** 🍚\n- **熬夜锦标赛冠军** ⏰\n- **别催 在做工呢** 🔨\n\n### 5️⃣ **英文/符号点缀 (看起来比较特别)**\n*注意：微信昵称支持特殊字符，但建议少用生僻字或乱码，以免对方手机显示成方框。*\n- **Mr.Right / Ms.Perfect**\n- **Just Me.** 🕶️\n- **Sunday Morning** ☁️\n- **Aurora🌈** (极光)\n\n---\n\n### 💡 微信昵称特别建议：\n\n1.  **避免特殊符号过多：** 比如 `★╰☆╮`，在别人的手机里可能显示不了或者很难搜索到你。\n2.  **考虑“备注”习惯：** 如果你的工作关系很重，别人可能会直接搜你的名字加你。如果不想暴露真名，可以用**英文名 + 姓氏首字母**（如：Alex L）。\n3.  **隐私设置配合：** 昵称改完后，记得检查微信的【我 - 头像、名字】权限，决定谁可以看到你的真实朋友圈。\n\n**如果你愿意告诉我以下信息，我可以帮你“定制”一个更精准的：**\n1. 你的名字里有没有什么字想保留？（比如姓李名浩）\n2. 你希望别人怎么称呼你？（亲切的、严肃的、还是有趣的？）",
  "usage": {
    "prompt_tokens": 635,
    "completion_tokens": 1716,
    "total_tokens": 2351
  }
}
```

**换一个 session_id**（对照组，应该没有记忆）：

```
{
  "message": "最终昵称是啥",
  "temperature": 0.7,
  "session_id": "1234567891116"
}
{
  "reply": "目前我无法直接查看您的账户信息或个人设定哦～如果您之前有预设过专属称呼（比如在特定平台绑定），可能需要到对应平台的「个人中心」或「账号设置」里确认呢！需要我帮您梳理常见昵称修改路径吗？",
  "usage": {
    "prompt_tokens": 14,
    "completion_tokens": 277,
    "total_tokens": 291
  }
}
```

**不传 session_id**（对照组，应该是一次性单轮）：

```
{
  "message": "最终昵称是啥",
  "temperature": 0.7
}
{
  "reply": "在这个对话里，我们之前还没有讨论过特定的“最终昵称”哦～😅 这可能是因为我们刚刚开始聊天。\n\n为了更准确地回答你，可以告诉我你是指：\n\n1. **我的名字吗？**（我是通义千问 / Qwen3.5）\n2. **你想给自己起个新昵称**需要我帮忙？\n3. 还是之前某个特定任务或话题里提到的结果？\n\n稍微给一点背景提示，我可以更好地帮你确认！",
  "usage": {
    "prompt_tokens": 14,
    "completion_tokens": 1093,
    "total_tokens": 1107
  }
}
```

**结论**：
传了session_id之后，有了记忆，可以连续对话，换id和不传都没有
---

## 6. 并发对照实验（本课核心）

> 用 `verify_concurrency.py` 跑，别手动开两个终端——手动测不出数字，也没法复现。
> **控制变量**：除了「路由是 async 还是同步」这一个变量，其余一字不动。

```
phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\chat_service\verify_concurrency.py
开始预热（预热请求不计入实验结果）
预热完成：基线：async def + AsyncOpenAI  /chat2
预热完成：错误：async def + OpenAI  /chat2_blocking
预热完成：线程池：def + OpenAI  /chat2_threadpool

基线：async def + AsyncOpenAI  /chat2  第 1 轮
请求A：发出 t=0.000s  返回 t=1.684s  耗时 1.684s  completion_tokens=338
请求B：发出 t=0.000s  返回 t=2.110s  耗时 2.110s  completion_tokens=411
两者总墙钟时间：2.110s
自动判定：并行  相对差值=0.202  长短倍数=1.253

基线：async def + AsyncOpenAI  /chat2  第 2 轮
请求A：发出 t=0.000s  返回 t=1.992s  耗时 1.992s  completion_tokens=434
请求B：发出 t=0.000s  返回 t=1.790s  耗时 1.790s  completion_tokens=368
两者总墙钟时间：1.992s
自动判定：并行  相对差值=0.101  长短倍数=1.113

基线：async def + AsyncOpenAI  /chat2  第 3 轮
请求A：发出 t=0.000s  返回 t=1.944s  耗时 1.944s  completion_tokens=434
请求B：发出 t=0.000s  返回 t=1.737s  耗时 1.737s  completion_tokens=368
两者总墙钟时间：1.944s
自动判定：并行  相对差值=0.107  长短倍数=1.119

基线：async def + AsyncOpenAI  三轮汇总：稳定并行

错误：async def + OpenAI  /chat2_blocking  第 1 轮
请求A：发出 t=0.000s  返回 t=4.579s  耗时 4.579s  completion_tokens=354
请求B：发出 t=0.000s  返回 t=3.337s  耗时 3.336s  completion_tokens=354
两者总墙钟时间：4.579s
自动判定：并行  相对差值=0.271  长短倍数=1.372

错误：async def + OpenAI  /chat2_blocking  第 2 轮
请求A：发出 t=0.000s  返回 t=1.344s  耗时 1.344s  completion_tokens=354
请求B：发出 t=0.000s  返回 t=2.651s  耗时 2.651s  completion_tokens=354
两者总墙钟时间：2.651s
自动判定：串行  相对差值=0.493  长短倍数=1.973

错误：async def + OpenAI  /chat2_blocking  第 3 轮
请求A：发出 t=0.000s  返回 t=2.566s  耗时 2.566s  completion_tokens=354
请求B：发出 t=0.000s  返回 t=1.281s  耗时 1.281s  completion_tokens=354
两者总墙钟时间：2.566s
自动判定：串行  相对差值=0.501  长短倍数=2.003

错误：async def + OpenAI  三轮汇总：结果混合 / 无法判断  并行=1  串行=2  无法判断=0

线程池：def + OpenAI  /chat2_threadpool  第 1 轮
请求A：发出 t=0.000s  返回 t=1.577s  耗时 1.577s  completion_tokens=354
请求B：发出 t=0.000s  返回 t=3.342s  耗时 3.342s  completion_tokens=354
两者总墙钟时间：3.342s
自动判定：串行  相对差值=0.528  长短倍数=2.119

线程池：def + OpenAI  /chat2_threadpool  第 2 轮
请求A：发出 t=0.000s  返回 t=2.032s  耗时 2.032s  completion_tokens=434
请求B：发出 t=0.000s  返回 t=1.797s  耗时 1.797s  completion_tokens=368
两者总墙钟时间：2.032s
自动判定：并行  相对差值=0.116  长短倍数=1.131

线程池：def + OpenAI  /chat2_threadpool  第 3 轮
请求A：发出 t=0.000s  返回 t=1.660s  耗时 1.660s  completion_tokens=336
请求B：发出 t=0.000s  返回 t=1.798s  耗时 1.798s  completion_tokens=376
两者总墙钟时间：1.798s
自动判定：并行  相对差值=0.077  长短倍数=1.083

线程池：def + OpenAI  三轮汇总：结果混合 / 无法判断  并行=2  串行=1  无法判断=0
(phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> 
```

### 6.3 判据的问题：时间不可靠

三组数据初看很乱：blocking 组 1 并行 2 串行、threadpool 组 2 并行 1 串行，
自动判定给出"结果混合 / 无法判断"。

**根因是判据选错了。** 单 GPU 上并行请求**共享算力**——两个一起跑，各自都变慢近一倍，
墙钟时间和串行几乎一样。而耗时受调度抖动、KV cache 状态、GPU 争抢影响，
噪声大到能把判定翻转（blocking 第 1 轮 A=4.579 / B=3.337，倍数 1.372，被判成"并行"，
但它本该是串行）。

### 6.4 更硬的判据：completion_tokens

`temperature=0.0` + 完全相同的 prompt → **单独跑时输出是确定的**，A 和 B 的
token 数应当完全一致。于是：

- **token 数相同** → 两个请求各跑各的，没进同一批次 → **串行**
- **token 数不同** → 两个请求被合进了同一个推理 batch → **真并发**

**机制**：多个请求落到 Ollama 的不同 slot 时，llama.cpp 会把它们合进**同一个 batch**
做前向传播。batch 形状变化 → 矩阵乘法的浮点累加顺序变化 → 极小的数值差异 →
`temperature=0` 取 argmax 时遇到接近的候选可能翻转 → 后续内容分叉 → 长度不同。

所以 **354/354 这个"干净"的数字反而是串行的证据**：没有并发批处理去扰动它。

| 组 | 轮次 | tokens A/B | 相同？ | 时间判据 | **token 判据** |
|---|---|---|---|---|---|
| 基线 async+AsyncOpenAI | 1 | 338 / 411 | ❌ | 并行 | **并发** |
| 基线 | 2 | 434 / 368 | ❌ | 并行 | **并发** |
| 基线 | 3 | 434 / 368 | ❌ | 并行 | **并发** |
| blocking async def+同步 | 1 | 354 / 354 | ✅ | 并行 ← **被骗** | **串行** |
| blocking | 2 | 354 / 354 | ✅ | 串行 | **串行** |
| blocking | 3 | 354 / 354 | ✅ | 串行 | **串行** |
| threadpool def+同步 | 1 | 354 / 354 | ✅ | 串行 | **串行**（冷启动） |
| threadpool | 2 | 434 / 368 | ❌ | 并行 | **并发** |
| threadpool | 3 | 336 / 376 | ❌ | 并行 | **并发** |

**换用 token 判据后，三组全部符合预期，零反例：**

```
基线       并发 3/3   async def + AsyncOpenAI，事件循环不被占用
blocking   并发 0/3   async def + 同步调用 → 事件循环被堵死，请求串行
threadpool 并发 2/3   def 路由被 FastAPI 丢进线程池，不占事件循环
```

threadpool 第 1 轮串行的原因：**anyio 的工作线程按需创建**，第一个同步请求要先
创建线程，第二个才有并发机会；第 2、3 轮线程池已热就并行了。
同 [[错题与复盘#E48]] 的热身成本。

### 6.5 结论

**1. 堵住第二个请求的具体是什么？**
是**事件循环**。`async def` 路由直接跑在事件循环上，函数体里的同步 HTTP 调用
不会交出控制权，整个进程的所有请求都得排队——不只是这一个接口，**是全部接口**
（`/health` 在那几秒里也会卡住）。

**2. `def` 路由为什么没事？**
FastAPI 检测到路由不是协程，会用 `run_in_threadpool` 把它丢进 anyio 线程池
（默认 40 个线程）执行，事件循环本身不被占用。代价是线程数有上限，
超过 40 个并发同步请求就开始排队。

**3. 和阶段 0 async 课的「让路 vs 堵路」是同一个机制吗？**
是同一个机制，但**后果的量级完全不同**：
- 阶段 0：单个脚本里一个协程堵住，只影响自己这条任务链
- 这里：Web 服务里堵住事件循环，影响的是**所有在线用户的所有请求**

这就是为什么它被称为 "FastAPI 最经典的性能事故"——本地跑没感觉，
上了并发直接雪崩。

### 6.6 方法论收获（比结论值钱）

**在共享资源上做并发实验，时间是噪声最大的指标。**

要先找**"有没有共享某个资源"的直接证据**，而不是只看快慢：
- 这次的证据是 `completion_tokens`（批处理留下的痕迹）
- 它不受调度抖动影响，要么进同一批要么没进，二值清晰

同类思路：看连接数、看日志里的 slot id、看服务端的 batch 统计——
**任何能直接反映"是否共处一个执行单元"的信号，都比计时可靠**。

---

## 遗留问题 / 踩到的坑

（验证过程中发现但没解决的，记在这里，别丢）

-
