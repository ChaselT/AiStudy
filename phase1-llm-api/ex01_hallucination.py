"""阶段 1 · 《大语言模型工作原理速览》· 动手任务 2

任务：诱导并对比**两类幻觉**。

【第一类：编造型幻觉】—— 问根本不存在的东西
1. 想三个**完全编造**的问题喂给模型，例如：
   - "介绍一下 Java 的 `@FastLoop` 注解"
   - "Spring Boot 的 `application-turbo.yml` 配置文件怎么用"
   - "Python 3.14 新增的 `itertools.zipmap` 函数签名是什么"
2. 观察它的反应。⚠️ **2026 年的模型多半会明确否认存在**（比早期模型进步很大），
   但**别就此收工**——幻觉往往转移到了回答的其他部分：
   **逐行核对它顺带提到的"真实" API、库、归属、版本号**，那里才是重灾区
   （实测发现：模型拒绝编造 @FastLoop，却把 Java Vector API 的类型名和方法全编了，
     还把 JMH 说成"Google 的框架"——实为 OpenJDK 项目）

【第二类：过期型幻觉】—— 问训练截止之后才发生的事
3. 用下面这批**已核实的 2026 年 6-7 月事实**当探针（有确定答案，可对质）：
   - 2026-07-28：MCP 规范做了什么重大改动？（答案：无状态化，移除 initialize 握手与 session-id）
   - 2026-07-24：deepseek-chat / deepseek-reasoner 还能用吗？（答案：当日退役，改名 deepseek-v4-flash / -pro）
   - 2026-07-09：OpenAI 最新 GPT 系列型号？（答案：gpt-5.6-sol / terra / luna）
   - 2026-06-12：Spring AI 2.0 的运行要求？（答案：Spring Boot 4 + Java 21）
   用**二分法**从近往远问，找到"开始答对"的那个点 —— 那附近就是训练截止边界
4. 附加实验：直接问它"你的训练数据截止到什么时候"，
   拿你测出的真实边界对照 —— **它很可能答错，这就是"模型连自己都不了解"的实证**

【对比与结论】
5. 把两类幻觉的回答与观察写成注释留在本文件里，重点回答：
   - 幻觉具体藏在哪里？（是"编造不存在的东西"，还是"真实东西的细节写错"？）
   - 哪一类更危险？为什么？

要求/提示：
- 密钥走环境变量（读 `.env` 里的 LLM_* 三件套），绝不硬编码
- 云端（中转站）和本地 `qwen3.5:27b` **两个都试更有意思**（大小模型的幻觉形态不同）
- 提问必须问**有确定答案的具体事实**（版本号/日期/专有名词），别问开放性问题
  —— 否则无法判断它是"知道"还是"编得像"
- 完成标准：能用自己的话回答"为什么 next token prediction 必然产生幻觉"，
  并**指出至少一处你亲手核对出来的、藏在可信回答里的错误细节**
"""
# 使用模型`qwen3.5:27b` 本地ollama
#问题一回答：
# 在标准的 **Java JDK（官方 Java 开发工具包）** 和主流开源库中，**并不存在名为 `@FastLoop` 的注解**。

# 如果你在某段代码、项目文档或教程中看到它，通常只有以下几种可能性。为了确保你获得准确的信息，我们需要分情况讨论：

# ### 1. 它是自定义/内部框架的注解 (最常见)
# 很多公司内部的中间件框架、性能优化库或者教学示例中，会定义一个名为 `@FastLoop` 的**自定义注解**。它的具体功能完全由
# 开发者自己决定。通常用于以下目的：
# *   **字节码增强（Bytecode Enhancement）：** 通过 AOP（面向切面编程）或 Java Agent/ASM/Javassist 技术，在编译期或运
# 行期自动对标记了该注解的方法进行循环展开、向量化优化等。
# *   **性能监控埋点：** 仅仅用来标识这段代码是热点路径，方便后续的日志追踪或 APM（应用性能管理）工具统计耗时。
# *   **教学演示：** 在讲解 Java 泛型擦除、注解处理器 (APT) 原理时，作者为了演示而虚构的注解。

# **如果你遇到了这种自定义注解：**
# 你需要查看该项目的源码定义（`@interface FastLoop`），看看它上面是否配合了元注解 `@Retention(RUNTIME)` 或
# `@Target(METHOD/TYPE)`，以及是否有配套的拦截器处理器来实现所谓的"Fast Loop"逻辑。

# ---

# ### 2. 你可能记错了名字 (混淆的可能性)
# 有些性能相关的注解名称比较像，可能是你记忆出现了偏差：
# *   **JMH (@Benchmark, @State):** Google 的性能基准测试框架 JMH (Java Microbenchmark Harness) 是优化和测量循环性能的
# 黄金标准。它没有 `@FastLoop`，但有复杂的控制逻辑来防止 JIT（即时编译器）过早优化或消除死代码。
# *   **GraalVM / JVMCI:** GraalVM 有一些特定的注解用于帮助编译器的向量化优化，但通常不是这个名称。
# *   **Spring Batch / Parallel Computing:** Spring 或其他并发框架可能有类似的批处理注解。

# ---

# ### 3. Java 中如何实现真正的“快速循环” (核心干货)
# 如果你是想在 Java 代码中**真正提升循环性能**，而不依赖某个不存在的标准注解，以下是工业界通用的优化方案：

# #### A. 信任 JIT (即时编译器) - 首选策略
# 现代 JVM（HotSpot, ZGC 等）非常智能。对于普通的 `for`/`while` 循环：
# *   **不要手动加注解**试图强制展开或向量化，通常会导致维护成本增加且收益不稳定。
# *   **保持逻辑简单：** JIT 很难优化包含复杂虚方法调用、异常抛出或不可预测分支的循环。尽量让编译器能进行逃逸分析（
# Escape Analysis）和标量替换。

# #### B. Java Vector API (SIMD 向量化) - JDK 17+ / Preview
# 这是目前官方提供的**最接近“硬件级加速”**的手段，利用 CPU SIMD 指令一次性处理多个数据：
# ```java
# import jdk.incubator.vector.*; // Note: Package may vary by version

# VectorSpec spec = VectorSpecies.INT_SPEC;
# IntVector v1 = IntVector.broadcast(spec, val);
# // ... vector operations ...
# v1.loop(...); // This is not @FastLoop but actual vector logic
# ```
# *注意：这是 JDK 的 Experimental/Incubator API，需关注 OpenJDK Project Panama / Vectorization 状态。*

# #### C. Parallel Streams (并行流) - CPU 多核优化
# 如果循环计算量大且无依赖关系（数据独立），可以使用 Stream API 开启并行处理：
# ```java
# // 不推荐在简单 for 循环中直接加注解替代，而是改写逻辑
# arrayList.parallelStream().forEach(...);
# // 或者更底层的 ForkJoinPool.invoke()
# ```

# #### D. 避免对象创建 (Allocation Reduction)
# 在高性能要求的循环中，最致命的性能杀手往往是**频繁的对象分配和 GC**。
# *   **错误示范：** `list.add(new Object());` 放在热循环里。
# *   **优化方案：** 使用池化技术（Object Pool）或复用数组/缓冲区，减少垃圾回收压力。

# ### 总结建议

# 1.  **确认来源**：请再次检查你看到该注解的代码库。如果它是你自己公司内部的代码，请直接询问架构师它的定义和拦截逻辑；
# 如果是开源项目，去 GitHub/GitLab 搜索该项目下 `@interface FastLoop` 的定义文件。
# 2.  **不要寻找 JDK API**：它不是 Java 原生特性，尝试在官方文档里找是徒劳的。
# 3.  **关注真实优化**：如果你是为了解决性能瓶颈，建议优先排查算法复杂度、GC 频率和 CPU 缓存命中率（Cache Locality），
# 而不是依赖所谓的“魔法注解”。

# 如果你有包含该注解的具体代码片段或上下文链接，可以提供给我，我可以帮你具体分析它的实现逻辑。

# 问题2回答：
# 首先需要明确一点：**Spring Boot 官方并没有名为 `turbo` 的标准 Profile（环境配置）**。标准的 Profile 通常是 `dev`, `test`, `prod`, `uat` 等。

# 如果在你的项目中出现了 `application-turbo.yml`，这通常意味着以下两种情况之一：
# 1.  **公司内部或团队自定义的规范**：用于特定的优化模式、压测场景或特定环境。
# 2.  **第三方框架/中间件引入的配置**：某些性能监控工具（如 TurboCharge）或内部脚手架可能约定了这个名字。

# 无论它是什么，它在 Spring Boot 中的使用逻辑遵循标准的 **Profile 机制**。以下是详细的使用指南：

# ---

# ### 1. 确认文件位置
# Spring Boot 的配置文件必须放在正确的目录下才能被自动扫描加载。通常路径为：
# *   `src/main/resources/application-turbo.yml` (Java Main)
# *   `src/test/resources/application-turbo.yml` (如果是测试类使用，较少见)

# ### 2. 如何激活该配置（关键步骤）
# 仅仅创建文件是不够的，你必须告诉 Spring Boot **当前要加载 `turbo` 这个环境**。你可以通过以下几种方式之一来激活它：

# #### 方法 A: 在启动参数中指定 (推荐/最常用)
# 在项目启动时添加 JVM 参数或命令行参数。这是运维部署时的标准做法。

# *   **Maven / Spring Boot CLI:**
#     ```bash
#     java -jar my-app.jar --spring.profiles.active=turbo
#     # 或者简写
#     mvn spring-boot:run -Dspring-boot.run.profiles=turbo
#     ```
# *   **IDEA 中运行配置 (Run Configuration):**
#     *   VM Options: `-Dspring.profiles.active=turbo`

# #### 方法 B: 在主配置文件 `application.yml` / `.properties` 中指定
# 在你的主入口配置文件中，设置激活的 profile。这通常用于开发环境快速切换。

# ```yaml
# # src/main/resources/application.yml
# server:
#   port: 8080

# spring:
#   profiles:
#     # 激活 turbo 模式
#     active: turbo 
# ```

# #### 方法 C: 通过环境变量 (Environment Variable)
# 在 Linux/Unix/Docker/Kubernetes 环境中：
# *   **System Property:** `-Dspring.profiles.active=turbo`
# *   **Env Var:** `SPRING_PROFILES_ACTIVE=turbo`

# ### 3. 配置文件内容示例 (`application-turbo.yml`)
# 这个文件用于**覆盖或补充**主配置文件中的属性。它应该只包含特定于 "turbo" 模式的设置（比如开启缓存、调整线程池、使用高性能数据库驱动等）。

# ```yaml
# # src/main/resources/application-turbo.yml
# spring:
#   datasource:
#     # Turbo 模式可能连接专门的优化库或主库
#     url: jdbc:mysql://high-perf-db.turboboot.com/db_optimized
    
# server:
#   servlet:
#     context-path: /turbo

# # 自定义业务配置示例
# myapp:
#   turbo-mode: true
#   cache-enabled: true
  
# logging:
#   level:
#     com.example.app: DEBUG # Turbo模式下可能需要更详细的调试日志或反之调至OFF以提高性能
# ```

# ### 4. 常见加载顺序与优先级说明
# Spring Boot 配置加载遵循一定规则，`turbo.yml` **不会**完全覆盖 `application.yml`。
# 1.  Spring Boot 先读取 `application.properties/yml` (默认值)。
# 2.  然后查找当前激活 Profile 的配置（即 `application-turbo.yml`）。
# 3.  `application-turbo.yml` 中的相同键值会**覆盖**主配置中的设置。

# ### 5. 排查：如果没生效怎么办？
# 如果你在代码里读取 `@Value("${xxx}")`，发现值没有变，请按以下步骤检查：

# 1.  **确认文件后缀：** Spring Boot 默认支持 `.properties`, `.yml`, `.yaml`。确保你创建的是 `.yml` 且名字完全匹配（区分大小写）。
# 2.  **确认路径：** 在 Maven/Gradle build 后，确认该文件被打包进了 `target/classes/application-turbo.yml` (或 jar 包根目录)。有时候 IDE 缓存会导致资源没更新。
# 3.  **检查 Profile ID:** 
#     *   文件名必须为：`application-{profileId}.yml` (如 `application-turbo`)。
#     *   激活时必须指定：`active: turbo`。**如果写成了 `turbo.yml`，那启动时也必须配 `-Dspring.profiles.active=turbo`**。（注意中间没有横杠）。
# 4.  **查看日志:** Spring Boot 启动时会打印 "The following profiles are active"。确认输出中是否包含 `turbo`。

# ### 6. 特殊情况排查 (关于 "Turbo")
# 如果这是一个特定库的要求（例如某些性能增强插件），请注意：
# *   **检查依赖：** 你的 `pom.xml` 或 `build.gradle` 里是否有引入类似 `com.example:turbo-boot-starter` 的包？有些第三方 Starter 可能会强制要求该配置文件存在，否则报错。
# *   **搜索代码库：** 在项目中全局搜索 "turbo"，看是否有自定义配置加载器（ConfigurationProperties）或者启动监听器专门检查这个文件是否存在。

# ### 总结
# **`application-turbo.yml` 只是一个名为 `turbo` 的自定义 Spring Profile。** 
# 要使用它：
# 1. 确保文件在 resources 目录下。
# 2. 通过 `-Dspring.profiles.active=turbo` 激活该环境。
# 3. 在该文件中配置特定于“加速/优化”场景的参数（如 DB、缓存开关）。

# 如果这是你公司内部的脚手架，建议优先查看团队的 **内部开发文档** 或询问导师关于 `turbo` profile 的具体业务含义。


#问题3回答：