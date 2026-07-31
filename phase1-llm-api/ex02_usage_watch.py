"""阶段 1 · 《Token与上下文窗口》· 动手任务 2 + 任务 3

⚠️ **前置依赖：本题需要先学完下一课《Chat Completions API》**
   （messages 数组结构、role 三种角色、多轮对话怎么拼、client 怎么建——本课都没讲）
   建议顺序：本课先做完 ex02_token_count.py → 学《Chat Completions API》→ 回头做本题。

任务 2：观察多轮对话的 token 膨胀。
1. 连续进行 5 轮对话（可以是脚本里写死的 5 个问题，不必手动 input）
2. 每轮打印 `resp.usage.prompt_tokens`
3. 观察输入 token 随轮次**线性增长**的现象，把数字记进注释

任务 3：实现历史截断。
1. 在任务 2 的基础上写一个 `trim_history`：保留 system 消息 + 最近 6 条对话消息
2. 再跑 5 轮以上，确认 `prompt_tokens` 不再无限增长（会稳定在一个区间）
3. 注释里对比截断前后的 prompt_tokens 曲线

要求/提示：
- 记住 API 是**无状态**的：历史要自己维护并每轮全量带上（Java 里没有 HttpSession 帮你）
- `trim_history` 要小心别把 system 消息一起截掉
- 完成标准：两组数字对比明显，能解释"为什么第 5 轮比第 1 轮贵"
"""

import os

import openai
from dotenv import load_dotenv
from openai.types.chat import ChatCompletion

load_dotenv()  # 之后 os.environ["DEEPSEEK_API_KEY"] 即可读到

QUESTIONS = [
    "用一句话解释什么是幂等性",
    "举一个 HTTP 方法里天然幂等的例子",
    "那 POST 为什么不幂等",
    "怎么让 POST 接口变成幂等的",
    "你刚说的方案在分布式环境下有什么问题",
    "用 Redis 实现的话要注意什么",
    "回到最开始，我问的第一个问题是什么",  # ← 探针：测长期记忆
    "把我们讨论过的要点用三句话总结",  # ← 探针：测全局记忆
]

client = openai.OpenAI(
    api_key=os.environ["LLM_API_KEY"],  # 从环境变量读，绝不硬编码
    base_url=os.environ["LLM_BASE_URL"],
    timeout=60.0,
    max_retries=3,  # 换 base_url 即换供应商
)


def trim_history(messages: list[dict], max_messages: int = 7) -> list[dict]:
    """滑动窗口：保留 system + 最近 max_messages 条"""
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    return system + rest[-max_messages:]


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
    sys_message = {"role": "system", "content": "你是一个助手。每次回答不超过50字"}
    messages = [sys_message]
    no_trim_input_all = 0
    no_trim_out_all = 0
    no_trim_all = 0
    trim_input_all = 0
    trim_out_all = 0
    trim_all = 0
    for i, w in enumerate(QUESTIONS, start=1):
        message = {"role": "user", "content": w}
        messages.append(message)
        resp = llm_call(messages)
        if isinstance(resp, str):
            print(resp)
        else:
            if resp.choices:
                print(f"无截断第{i}次对话响应：{resp.choices[0].message.content}")
                messages.append(
                    {
                        "role": "assistant",
                        "content": resp.choices[0].message.content or "",
                    }
                )
            if resp.usage:
                print(
                    f"无截断第{i}次对话消耗，prompt_tokens:{resp.usage.prompt_tokens},completion_tokens:{resp.usage.completion_tokens},total_tokens:{resp.usage.total_tokens}"
                )
                no_trim_input_all += resp.usage.prompt_tokens
                no_trim_out_all += resp.usage.completion_tokens
                no_trim_all += resp.usage.total_tokens
    messages = [sys_message]
    for i, w in enumerate(QUESTIONS, start=1):
        message = {"role": "user", "content": w}
        messages.append(message)
        messages = trim_history(messages)
        resp = llm_call(messages)
        if isinstance(resp, str):
            print(resp)
        else:
            if resp.choices:
                print(f"有截断第{i}次对话响应：{resp.choices[0].message.content}")
                messages.append(
                    {
                        "role": "assistant",
                        "content": resp.choices[0].message.content or "",
                    }
                )
            if resp.usage:
                print(
                    f"有截断第{i}次对话消耗，prompt_tokens:{resp.usage.prompt_tokens},completion_tokens:{resp.usage.completion_tokens},total_tokens:{resp.usage.total_tokens}"
                )
                trim_input_all += resp.usage.prompt_tokens
                trim_out_all += resp.usage.completion_tokens
                trim_all += resp.usage.total_tokens
    print(
        f"无截断总消耗：输入-{no_trim_input_all},输出-{no_trim_out_all},总和-{no_trim_all}"
    )
    print(f"有截断总消耗：输入-{trim_input_all},输出-{trim_out_all},总和-{trim_all}")


if __name__ == "__main__":
    main()
# 响应
# 无截断第1次对话响应：幂等性是指同一操作无论执行一次还是多次，产生的结果都相同。
# 无截断第1次对话消耗，prompt_tokens:25,completion_tokens:28,total_tokens:53
# 无截断第2次对话响应：例如 `GET /users/123`：无论请求一次还是多次，都只是获取同一用户信息，不会改变服务器资源状态，因此是幂等的。
# 无截断第2次对话消耗，prompt_tokens:71,completion_tokens:40,total_tokens:111
# 无截断第3次对话响应：因为同一个 `POST` 请求重复提交时，服务器通常会多次创建资源或触发操作，例如重复调用 `POST /orders` 可能生成多笔订单，所以其结果不一定与只提交一次相同；不过可以通过幂等键等机制让特定 `POST` 接口实现幂等。
# 无截断第3次对话消耗，prompt_tokens:124,completion_tokens:74,total_tokens:198
# 无截断第4次对话响应：可以通过 **幂等键（Idempotency-Key）** 让 `POST` 接口幂等：

# 1. 客户端为一次业务操作生成唯一键，例如 UUID，并放在请求头中：
#    ```http
#    POST /orders
#    Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
#    ```
# 2. 服务端首次收到该键时执行操作，并保存“幂等键、请求参数摘要、处理结果”。
# 3. 再次收到相同键时，不重复执行，而是直接返回首次结果。
# 4. 用数据库唯一索引和事务处理并发请求，避免同一键同时创建多条数据。

# 此外，也可以使用订单号等**业务唯一标识**并建立唯一约束；同时应检查相同幂等键对应的请求参数是否一致，防止误复用。
# 无截断第4次对话消耗，prompt_tokens:215,completion_tokens:251,total_tokens:466
# 无截断第5次对话响应：在分布式环境中，幂等键方案主要有这些问题：

# 1. **多实例并发竞争**：相同请求可能同时到达不同实例，如果幂等记录只保存在本地缓存，两个实例都会执行；需要共享存储，并通过唯一索引或原子操作抢占幂等键。
# 2. **“记录”和“业务操作”不原子**：先执行业务再保存幂等结果，宕机可能导致业务已完成但没有记录；先保存记录再执行业务，宕机又可能留下永久的“处理中”状态。应尽量使用同一数据库事务、事务消息或状态机解决。
# 3. **下游副作用难以回滚**：即使本地订单只创建一次，调用支付、发短信、发消息等下游服务时仍可能重复；幂等键需要沿调用链传递，每个有副作用的下游也要支持幂等。
# 4. **消息投递通常是至少一次**：事务提交后重复发消息或消费者重复消费都可能产生副作用，需要 Outbox、消息唯一 ID 和消费者去重。
# 5. **跨库、跨地域一致性问题**：不同地域可能同时接受同一个键，而复制存在延迟，普通唯一约束未必能提供全局唯一性，需要确定统一写入点、全局一致存储或业务分区策略。
# 6. **结果缓存与超时问题**：服务端已成功但响应丢失时，客户端会重试；服务端必须保存并返回首次结果，而不只是返回“重复请求”。
# 7. **幂等键过期问题**：TTL 太短会让迟到的重试再次执行，太长则增加存储成本；应根据客户端最大重试周期和业务生命周期设置。
# 8. **键被错误复用**：同一个幂等键可能对应不同请求参数，因此应同时保存请求摘要；键相同但参数不同应拒绝。
# 9. **分布式锁并非万能**：锁可能因超时、网络分区或进程暂停而失效，导致并发执行；通常数据库唯一约束比单纯依赖分布式锁更可靠。

# 常见实现是：在共享数据库中对 `(调用方, Idempotency-Key)` 建唯一索引，原子写入 `PROCESSING` 状态，业务操作与状态更新尽量放在同一事务中，并通过 Outbox 保证下游消息可靠且可去重。
# 无截断第5次对话消耗，prompt_tokens:433,completion_tokens:620,total_tokens:1053
# 无截断第6次对话响应：用 Redis 实现 `POST` 幂等时，重点注意以下问题：

# 1. **原子占位**
#    使用一条原子命令，而不是先 `GET` 再 `SET`：
#    ```redis
#    SET idem:{clientId}:{key} processing NX EX 60
#    ```
#    返回成功才执行业务；失败说明该请求已存在。

# 2. **区分处理状态**
#    幂等记录通常包含：
#    - `PROCESSING`：正在处理
#    - `SUCCESS`：已完成，并保存响应结果
#    - `FAILED`：失败，标明是否允许重试

#    重复请求遇到 `SUCCESS` 时直接返回首次结果；遇到 `PROCESSING` 时可返回 `409/202`，而不是再次执行。

# 3. **避免误删其他请求的锁**
#    占位值中写入随机 `ownerToken`，释放或更新时用 Lua 脚本验证 token，不能直接 `DEL`，否则超时后可能删掉另一个请求新获得的占位。

# 4. **正确设置 TTL**
#    - `PROCESSING` 的 TTL 必须覆盖正常执行时间，并在长任务中续期。
#    - `SUCCESS` 的 TTL 应覆盖客户端最大重试周期。
#    - TTL 太短会导致请求再次执行；太长会增加内存占用。
#    续期和状态更新也要验证 `ownerToken`。

# 5. **检查请求内容是否一致**
#    Redis 中同时保存请求参数摘要，例如：
#    ```text
#    hash = SHA256(method + path + body + caller)
#    ```
#    相同幂等键但摘要不同，应拒绝请求，防止客户端误复用键。

# 6. **Redis 与业务数据库无法天然保持原子性**
#    典型风险是：
#    - Redis 占位成功，但业务执行前服务宕机；
#    - 数据库提交成功，但 Redis 还没写 `SUCCESS` 就宕机。

#    因此 Redis 通常只能作为快速去重层，关键业务仍应在数据库中建立业务唯一约束；必要时配合本地事务、Outbox 和状态恢复任务。

# 7. **考虑 Redis 故障与主从切换**
#    Redis 异步复制时，主节点写入成功后若立刻故障，幂等记录可能尚未同步到副本，切换后重复请求可能再次执行。不能把普通 Redis 锁当作严格的“恰好一次”保证；支付、订单等场景应以数据库唯一约束或强一致存储兜底。

# 8. **结果写入要原子更新**
#    从 `PROCESSING` 更新为 `SUCCESS` 时，应使用 Lua 脚本同时校验状态和 `ownerToken`，避免过期请求覆盖新请求的处理结果。

# 9. **限制键的作用域和资源消耗**
#    幂等键应包含调用方或租户，避免不同用户冲突；同时限制键长度、请求频率和缓存响应大小，防止恶意请求造成 Redis 内存耗尽或热点键问题。

# 一个常见流程是：

# ```text
# SET key {PROCESSING, ownerToken, requestHash} NX EX 60
#   ├─ 成功：执行业务，数据库用唯一约束兜底，再原子写入 SUCCESS 和响应
#   └─ 失败：
#        ├─ requestHash 不同：拒绝
#        ├─ SUCCESS：返回首次响应
#        └─ PROCESSING：告知处理中，稍后重试
# ```

# 核心原则是：**Redis 负责快速拦截重复请求，数据库唯一约束负责最终正确性，不要只依赖 Redis 保证关键业务幂等。**
# 无截断第6次对话消耗，prompt_tokens:1000,completion_tokens:948,total_tokens:1948
# 无截断第7次对话响应：你问的第一个问题是：“用一句话解释什么是幂等性”。
# 无截断第7次对话消耗，prompt_tokens:1848,completion_tokens:23,total_tokens:1871
# 无截断第8次对话响应：幂等性是指同一操作执行一次或多次产生的结果相同，例如 `GET` 天然幂等，而 `POST` 通常会重复创建资源。
# 可以通过幂等键、请求摘要、状态记录和数据库唯一约束，让重复的 `POST` 请求返回首次结果而不重复执行业务。
# 在分布式环境中需处理并发竞争、事务原子性、下游重复调用及故障恢复；使用 Redis 时应原子占位、合理设置 TTL、校验 owner token，并以数据库约束保障最终正确性。
# 无截断第8次对话消耗，prompt_tokens:1888,completion_tokens:155,total_tokens:2043
# 有截断第1次对话响应：幂等性是指同一操作执行一次或多次，产生的结果都相同。
# 有截断第1次对话消耗，prompt_tokens:25,completion_tokens:26,total_tokens:51
# 有截断第2次对话响应：例如 `GET /users/123`：无论调用一次还是多次，都只是获取用户 123 的信息，不会改变服务器状态，因此是天然幂等的。
# 有截断第2次对话消耗，prompt_tokens:69,completion_tokens:41,total_tokens:110
# 有截断第3次对话响应：因为 `POST` 通常用于创建资源或触发操作，同一个请求重复发送可能会创建多条记录或多次执行副作用，例如重复提交两次订单会生成两个订单，所以它默认不幂等；不过可以通过幂等键等机制让特定的 `POST` 接口具备幂等性。
# 有截断第3次对话消耗，prompt_tokens:123,completion_tokens:77,total_tokens:200
# 有截断第4次对话响应：常见做法是使用**幂等键（Idempotency-Key）**：

# 1. 客户端为一次业务操作生成唯一键，例如 UUID，并放到请求头：
#    ```http
#    POST /orders
#    Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
#    ```
# 2. 服务端首次收到请求时，原子地保存“幂等键 + 请求参数摘要 + 处理结果”并执行业务。
# 3. 再次收到相同幂等键时，不重复创建订单，而是直接返回第一次的结果。
# 4. 如果相同幂等键对应不同参数，则拒绝请求，避免误用。

# 实现时还应配合数据库唯一索引、事务或分布式锁，防止并发请求同时执行；也可以用订单号、支付流水号等业务唯一标识建立唯一约束。
# 有截断第4次对话消耗，prompt_tokens:217,completion_tokens:302,total_tokens:519
# 有截断第5次对话响应：在分布式环境下，仅仅“查一下幂等键，没处理过就执行”会遇到不少问题：

# 1. **并发竞态**
#    两个实例同时收到相同请求，都发现幂等键不存在，于是都执行了创建订单。

#    **解决**：利用数据库唯一索引、Redis `SET NX`、条件写等原子操作抢占幂等键，不能用普通的“先查再写”。

# 2. **幂等记录与业务操作不原子**
#    - 先写幂等记录，再执行业务：业务失败后，重试可能被误认为已经成功。
#    - 先执行业务，再写幂等记录：业务成功但记录写入失败，重试会再次执行业务。

#    **解决**：如果在同一个数据库中，把幂等记录和业务数据放进同一事务；跨服务时可使用业务唯一约束、Outbox、状态机或最终一致性方案。

# 3. **处理中状态难以判断**
#    第一个节点拿到幂等键后宕机，键一直处于 `PROCESSING`。其他请求不知道应该等待、重试还是重新执行。

#    **解决**：设置租约/超时和明确状态，例如：
#    ```text
#    PROCESSING -> SUCCEEDED / FAILED
#    ```
#    但超时后重新执行仍需依靠业务唯一约束兜底，因为原请求可能实际上还在运行。

# 4. **分布式锁并不等于业务幂等**
#    Redis 锁过期后，第一个请求可能还没完成，第二个请求又获得锁，导致两者同时执行；网络分区也可能造成锁归属判断错误。

#    **解决**：锁只用于降低并发，最终应依赖数据库唯一索引或业务侧条件更新；必要时使用 fencing token（递增令牌）拒绝旧执行者。

# 5. **缓存或副本一致性问题**
#    如果幂等键存储在本地缓存、异步复制的 Redis 副本或不同地域中，请求切换节点后可能读不到刚写入的记录。

#    **解决**：使用共享且具备强一致写入能力的存储；关键判断避免读取延迟副本。多地域系统还要明确幂等键的归属地域或使用全局唯一约束。

# 6. **响应结果丢失**
#    服务端已成功创建订单，但响应在网络中丢失。客户端重试时，服务端需要返回第一次的订单，而不能只返回“重复请求”。

#    **解决**：保存幂等键对应的资源 ID、状态码和必要响应数据，重试时返回语义一致的结果。

# 7. **相同幂等键被用于不同请求**
#    客户端可能错误地复用幂等键，例如第一次创建订单 A，第二次却用同一个键创建订单 B。

#    **解决**：保存请求参数的规范化摘要；同一键但摘要不同时返回冲突，例如 `409 Conflict`。

# 8. **过期时间难以设置**
#    TTL 太短，客户端晚到的重试可能重复执行；TTL 太长，会占用大量存储，也可能阻止业务上合法的再次操作。

#    **解决**：根据客户端最大重试窗口和业务生命周期设置 TTL。支付、订单等场景更适合长期保存业务唯一号，而不只依赖短期缓存。

# 一个较稳妥的实现通常是：

# ```text
# 客户端幂等键
#     + 服务端原子插入/唯一索引
#     + 请求参数摘要校验
#     + 幂等记录与业务写入同事务
#     + 业务唯一约束兜底
#     + 保存首次处理结果
# ```

# 核心原则是：**幂等键记录不能只作为一个分布式锁；最终必须让业务数据本身也具备“重复写不会产生第二份结果”的约束。**
# 有截断第5次对话消耗，prompt_tokens:397,completion_tokens:928,total_tokens:1325
# 有截断第6次对话响应：用 Redis 做 `POST` 幂等，最重要的是：**Redis 只能负责请求去重，不能单独保证业务操作“恰好执行一次”**。Redis 与数据库之间没有原子事务，仍需业务唯一约束兜底。

# ## 1. 原子抢占，避免“先查再写”

# 不要这样做：

# ```text
# GET key
# 如果不存在：
#     SET key
#     执行业务
# ```

# 并发请求可能都读到不存在。

# 应使用原子命令：

# ```redis
# SET idem:{userId}:{idempotencyKey} processing NX EX 60
# ```

# - 返回 `OK`：当前请求获得执行权
# - 返回空：已有请求正在执行或已完成

# 如果判断逻辑复杂，使用 Lua 脚本原子完成。

# ---

# ## 2. 保存状态，而不只是一个锁

# 建议保存：

# ```text
# status: PROCESSING | SUCCEEDED | FAILED
# request_hash: 请求参数摘要
# owner_token: 本次执行者唯一标识
# resource_id: 创建出的业务资源 ID
# response: 必要的响应数据
# ```

# 处理流程：

# ```text
# 第一次请求：
#   原子创建 PROCESSING
#   -> 执行业务
#   -> 更新为 SUCCEEDED 并保存结果

# 重复请求：
#   SUCCEEDED  -> 返回第一次结果
#   PROCESSING -> 返回“处理中”，或短暂等待后查询
#   FAILED     -> 根据错误类型决定是否允许重试
# ```

# 不能只在成功后写 Redis，否则两个并发请求仍可能同时执行业务。

# ---

# ## 3. 校验请求参数摘要

# 相同幂等键必须对应相同业务请求。可对规范化后的参数计算摘要：

# ```text
# request_hash = SHA-256(method + path + user_id + normalized_body)
# ```

# 如果键相同但摘要不同，应返回：

# ```http
# 409 Conflict
# ```

# 注意：

# - JSON 字段顺序、空白、默认值需要规范化
# - 幂等键通常要和用户、租户或商户绑定
# - 不要让不同用户共享同一幂等键命名空间

# ---

# ## 4. TTL 要区分“执行租约”和“结果保留时间”

# 不要用一个很短的 TTL 同时承担两种职责。

# - `PROCESSING`：相当于执行租约，TTL 应覆盖正常最大执行时间
# - `SUCCEEDED`：保存时间应覆盖客户端最大重试窗口，通常更长

# 例如：

# ```text
# PROCESSING：5 分钟
# SUCCEEDED：24 小时或按业务生命周期保存
# ```

# 风险：

# - TTL 太短：第一个请求仍在执行，键已过期，第二个请求再次执行
# - TTL 太长：节点宕机后，其他请求长期停留在处理中
# - 执行时间不可预测：可续租，但续租必须校验 `owner_token`

# 即使有租约和续租，也不能完全排除重复执行，因此仍需要数据库唯一约束。

# ---

# ## 5. 更新或释放时校验 owner token

# 不要直接：

# ```redis
# DEL idem:key
# ```

# 因为锁可能已过期，并被另一个请求重新获得；旧请求再删除时会误删新请求的锁。

# 每个执行者生成唯一 token：

# ```text
# owner_token = UUID
# ```

# 通过 Lua 脚本校验 token 后再更新、续租或删除：

# ```lua
# if redis.call("HGET", KEYS[1], "owner_token") == ARGV[1] then
#     return redis.call("EXPIRE", KEYS[1], ARGV[2])
# end
# return 0
# ```

# 完成状态更新也应使用相同的所有权校验。

# ---

# ## 6. Redis 与业务数据库之间存在一致性空隙

# 这是最关键的问题。

# ### 情况一：数据库成功，Redis 更新失败

# ```text
# 订单已创建
# -> Redis 连接失败，仍是 PROCESSING 或键过期
# -> 客户端重试
# -> 可能再次创建订单
# ```

# ### 情况二：Redis 写入 SUCCEEDED，但数据库事务最终失败

# 客户端会收到一个并不存在的成功结果。

# 因此：

# - 订单表使用 `client_request_id` 唯一索引
# - 支付表使用商户支付流水号唯一索引
# - 状态变更使用条件更新
# - 扣减类操作使用业务流水表或唯一事件 ID

# 例如：

# ```sql
# CREATE UNIQUE INDEX uk_order_request
# ON orders(tenant_id, client_request_id);
# ```

# 创建订单时：

# ```sql
# INSERT INTO orders (..., client_request_id)
# VALUES (..., ?);
# ```

# 如果违反唯一约束，则查询并返回已存在订单，而不是再创建一份。

# **Redis 用于快速去重和缓存结果，数据库唯一约束才是最终防线。**

# ---

# ## 7. Redis 故障切换并不保证绝对不重复

# Redis 主从复制通常是异步的：

# 1. 幂等键写入主节点
# 2. 尚未复制到从节点，主节点宕机
# 3. 从节点提升为主节点
# 4. 刚写入的幂等键丢失
# 5. 重试请求再次执行

# `WAIT` 可以降低风险，但不能替代业务唯一约束，也不能提供 Redis 与业务数据库之间的原子性。

# 还要考虑：

# - Redis 重启时是否开启 AOF/RDB
# - AOF 的刷盘策略
# - 集群故障切换和数据丢失窗口
# - 不要从延迟副本读取幂等状态
# - Redis 不可用时选择“拒绝请求”还是“依赖数据库约束继续处理”

# 关键业务通常应明确降级策略，而不是默认放行。

# ---

# ## 8. `PROCESSING` 状态的重复请求怎么返回

# 常见策略有三种：

# ### 立即返回处理中

# ```http
# HTTP/1.1 409 Conflict
# Retry-After: 2
# ```

# 或者：

# ```http
# HTTP/1.1 202 Accepted
# ```

# 返回查询地址：

# ```json
# {
#   "status": "processing",
#   "statusUrl": "/operations/123"
# }
# ```

# ### 短暂等待

# 轮询 Redis 几百毫秒，若首次请求完成，就返回相同结果。要设置超时，避免大量连接堆积。

# ### 发布通知

# 通过消息或通知机制唤醒等待者。实现更复杂，而且 Redis Pub/Sub 消息本身不持久，不能作为最终状态存储。

# ---

# ## 9. 不要缓存过大的完整响应

# 可以保存：

# ```json
# {
#   "status": "SUCCEEDED",
#   "httpStatus": 201,
#   "resourceId": "order-123"
# }
# ```

# 重试时根据 `resourceId` 查询数据库并重建响应。

# 如果要缓存完整响应，需要注意：

# - Redis 内存占用
# - 响应中是否包含敏感信息
# - 数据是否会过时
# - 响应压缩和大小限制
# - 是否需要保存状态码和部分响应头

# 通常不应缓存 `Set-Cookie`、动态签名、一次性令牌等内容。

# ---

# ## 10. Redis Cluster 下的键设计

# 如果 Lua 脚本或事务同时操作多个 key，Redis Cluster 要求它们位于同一个 hash slot，可以使用 hash tag：

# ```text
# idem:{tenantId:key}:state
# idem:{tenantId:key}:result
# ```

# 更简单的方式是将状态和结果存到同一个 Hash 中，减少多 key 原子操作问题。

# 还要防止：

# - 某个租户产生热点 key
# - 幂等键过短、可预测导致恶意碰撞
# - 客户端提交超长 key 消耗内存

# 应限制 key 长度，并可对外部幂等键计算哈希后作为 Redis key。

# ---

# ## 11. 失败状态要分类

# 并非所有失败都应该缓存：

# - 参数错误、业务规则拒绝：可以保存最终失败结果
# - Redis/数据库超时：结果可能未知，不宜简单标记为可重试失败
# - 第三方支付超时：可能已成功，应通过业务流水号查询确认
# - 进程崩溃：保留 `PROCESSING`，之后按租约和业务数据恢复

# 特别要避免：

# ```text
# 调用支付渠道超时
# -> 删除幂等键
# -> 客户端重试
# -> 再次扣款
# ```

# 第三方调用同样要传稳定的业务唯一号或对方支持的幂等键。

# ---

# ## 推荐实现结构

# ```text
# 1. 客户端发送 Idempotency-Key
# 2. 服务端计算 request_hash
# 3. Lua 原子创建 PROCESSING 状态
# 4. 若已存在：
#    - hash 不同：409
#    - SUCCEEDED：返回第一次结果
#    - PROCESSING：返回 202/409 或等待
# 5. 获得执行权后执行业务
# 6. 数据库通过业务唯一索引保证不会重复创建
# 7. Lua 校验 owner_token，更新为 SUCCEEDED 并保存 resource_id
# 8. 设置足够长的结果 TTL
# ```

# 最终保障层次应是：

# ```text
# Redis 原子抢占
#     + 状态和请求摘要
#     + owner token 与合理 TTL
#     + 数据库业务唯一约束
#     + 重试后查询既有业务结果
# ```

# 如果只做 `SET NX EX`，它最多是一个带过期时间的分布式锁，**不是完整的幂等方案**。
# 有截断第6次对话消耗，prompt_tokens:1228,completion_tokens:2248,total_tokens:3476
# 有截断第7次对话响应：你问的第一个问题是：**“怎么让 POST 接口变成幂等的”**。
# 有截断第7次对话消耗，prompt_tokens:3246,completion_tokens:28,total_tokens:3274
# 有截断第8次对话响应：让 POST 接口幂等的核心是使用幂等键、校验请求摘要并保存首次处理状态与结果，使重复请求返回同一业务结果。
# 在分布式环境中，要避免“先查再写”的竞态以及幂等记录和业务操作不一致，并用数据库唯一索引或条件写作为最终兜底。
# Redis 实现应采用原子抢占、`PROCESSING/SUCCEEDED/FAILED` 状态、合理 TTL 和 owner token，但 `SET NX` 或分布式锁本身不能保证业务恰好执行一次。
# 有截断第8次对话消耗，prompt_tokens:3071,completion_tokens:156,total_tokens:3227
# 无截断总消耗：输入-5604,输出-2139,总和-7743
# 有截断总消耗：输入-8376,输出-3806,总和-12182

# 响应消耗整理
# 无截断第1次对话消耗，prompt_tokens:25,completion_tokens:28,total_tokens:53
# 无截断第2次对话消耗，prompt_tokens:71,completion_tokens:40,total_tokens:111
# 无截断第3次对话消耗，prompt_tokens:124,completion_tokens:74,total_tokens:198
# 无截断第4次对话消耗，prompt_tokens:215,completion_tokens:251,total_tokens:466
# 无截断第5次对话消耗，prompt_tokens:433,completion_tokens:620,total_tokens:1053
# 无截断第6次对话消耗，prompt_tokens:1000,completion_tokens:948,total_tokens:1948
# 无截断第7次对话消耗，prompt_tokens:1848,completion_tokens:23,total_tokens:1871
# 无截断第8次对话消耗，prompt_tokens:1888,completion_tokens:155,total_tokens:2043
# 无截断总消耗：输入-5604,输出-2139,总和-7743

# 有截断第1次对话消耗，prompt_tokens:25,completion_tokens:26,total_tokens:51
# 有截断第2次对话消耗，prompt_tokens:69,completion_tokens:41,total_tokens:110
# 有截断第3次对话消耗，prompt_tokens:123,completion_tokens:77,total_tokens:200
# 有截断第4次对话消耗，prompt_tokens:217,completion_tokens:302,total_tokens:519
# 有截断第5次对话消耗，prompt_tokens:397,completion_tokens:928,total_tokens:1325
# 有截断第6次对话消耗，prompt_tokens:1228,completion_tokens:2248,total_tokens:3476
# 有截断第7次对话消耗，prompt_tokens:3246,completion_tokens:28,total_tokens:3274
# 有截断第8次对话消耗，prompt_tokens:3071,completion_tokens:156,total_tokens:3227
# 有截断总消耗：输入-8376,输出-3806,总和-12182

# 无截断的时候，每一次对话都会增加，消耗一直增加，有截断的增加到一定程度之后会开始趋于稳定，甚至因为较大的
# 一条记录或者响应被排除而变低很多
# 有截断总消耗多，是因为有一次响应特别的长
# 且截断之后会出现错觉，记错第一个问题是什么，是因为他看到的第一个问题已经变成了后面的问题

# 加了响应字数限制的结果
# (phase1-llm-api) PS E:\workspace\AiStudy\phase1-llm-api> uv run .\ex02_usage_watch.py
# 无截断第1次对话响应：幂等性指同一操作执行一次或多次，产生的最终结果相同。
# 无截断第1次对话消耗，prompt_tokens:32,completion_tokens:25,total_tokens:57
# 无截断第2次对话响应：例如 GET：重复请求同一资源，通常不会改变服务器状态。
# 无截断第2次对话消耗，prompt_tokens:75,completion_tokens:19,total_tokens:94
# 无截断第3次对话响应：因为重复 POST 可能多次创建资源或触发副作用，结果会累积。
# 无截断第3次对话消耗，prompt_tokens:107,completion_tokens:24,total_tokens:131
# 无截断第4次对话响应：使用唯一幂等键，服务端缓存首次结果，重复请求直接返回该结果。
# 无截断第4次对话消耗，prompt_tokens:148,completion_tokens:50,total_tokens:198
# 无截断第5次对话响应：会遇到并发竞态、缓存一致性、键过期，以及业务成功但结果未写入等问题。
# 无截断第5次对话消耗，prompt_tokens:191,completion_tokens:60,total_tokens:251
# 无截断第6次对话响应：用SET NX EX原子占位，合理设TTL，并处理宕机、主从切换及业务结果一致性。
# 无截断第6次对话消耗，prompt_tokens:235,completion_tokens:76,total_tokens:311
# 无截断第7次对话响应：你第一个问题是：“用一句话解释什么是幂等性”。
# 无截断第7次对话消耗，prompt_tokens:284,completion_tokens:21,total_tokens:305
# 无截断第8次对话响应：幂等性指重复操作结果一致。GET天然幂等，POST需幂等键去重。分布式下注意竞态、过期、故障与一致性。
# 无截断第8次对话消耗，prompt_tokens:322,completion_tokens:119,total_tokens:441
# 有截断第1次对话响应：幂等性是指同一操作执行一次或多次，产生的最终结果相同。
# 有截断第1次对话消耗，prompt_tokens:32,completion_tokens:45,total_tokens:77
# 有截断第2次对话响应：例如 GET：重复请求同一资源，服务器状态不会因此改变。
# 有截断第2次对话消耗，prompt_tokens:76,completion_tokens:39,total_tokens:115
# 有截断第3次对话响应：因为重复 POST 可能多次创建资源或触发副作用，结果会累积变化。
# 有截断第3次对话消耗，prompt_tokens:108,completion_tokens:43,total_tokens:151
# 有截断第4次对话响应：客户端传唯一幂等键；服务端记录首次结果，重复请求直接返回该结果。
# 有截断第4次对话消耗，prompt_tokens:150,completion_tokens:25,total_tokens:175
# 有截断第5次对话响应：并发请求落到不同节点会重复执行；需共享存储、唯一约束和原子写，并处理超时、重试与键过期。
# 有截断第5次对话消耗，prompt_tokens:152,completion_tokens:165,total_tokens:317
# 有截断第6次对话响应：用 SET NX EX 原子占位；缓存状态与结果；合理设 TTL；处理宕机、Redis 故障及业务库一致性。
# 有截断第6次对话消耗，prompt_tokens:168,completion_tokens:184,total_tokens:352
# 有截断第7次对话响应：你问的是：“怎么让 POST 接口变成幂等的”。
# 有截断第7次对话消耗，prompt_tokens:184,completion_tokens:20,total_tokens:204
# 有截断第8次对话响应：POST用幂等键去重并复用结果。分布式需共享状态和原子约束。Redis原子占位，注意TTL与一致性。
# 有截断第8次对话消耗，prompt_tokens:179,completion_tokens:336,total_tokens:515
# 无截断总消耗：输入-1394,输出-394,总和-1788
# 有截断总消耗：输入-1049,输出-857,总和-1906

# 虽然数据略微有差距，但是上面的结论不变


# 1. 成本结论分开看输入/输出（这条不变，输入省 25%、第 8 轮省 44%）
# 有截断第7次对话消耗，prompt_tokens:184,completion_tokens:20,total_tokens:204
# 有截断第8次对话消耗，prompt_tokens:179,completion_tokens:336,total_tokens:515
# 这组对比能看出来截断之后输入token降低
# 2. 按条数截断不可靠——证据换成有截断组内部的 1228 → 3246
# 即使截断了，但是由于最后一次加进去的数据变多，整体还变多了
# 3. 输出 token 反常增多记一笔现象
