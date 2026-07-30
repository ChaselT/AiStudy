"""阶段 1 · 《大语言模型工作原理速览》· 动手任务 2

任务：故意诱导幻觉。
1. 想三个**完全编造**的问题喂给模型，例如：
   - "介绍一下 Java 的 `@FastLoop` 注解"
   - "Spring Boot 的 `application-turbo.yml` 配置文件怎么用"
   - "Python 3.14 新增的 `itertools.zipmap` 函数签名是什么"
2. 观察它如何一本正经地编造：有没有给出"看起来很像真的"的用法、参数、版本号
3. 把三次回答与你的观察结论写成注释留在本文件里

要求/提示：
- 密钥走环境变量（`os.environ`）或 python-dotenv 读 `.env`，绝不硬编码
- 用云端 DeepSeek 或本地 Ollama 都行，能跑通即可
- 完成标准：能用自己的话在注释里回答"为什么 next token prediction 必然产生幻觉"，
  并指出这三个回答里哪些细节是模型凭空生成的
"""
