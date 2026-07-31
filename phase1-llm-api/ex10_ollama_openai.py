"""阶段 1 · 《Ollama本地模型》· 动手任务 2（含任务 1、3 的记录）

任务 2（主任务）：用 openai SDK 连本地 Ollama。
1. 把 base_url 指向本地 Ollama 的 OpenAI 兼容端点，api_key 随便填一个占位串
2. 跑通普通（非流式）调用
3. 跑通流式输出
4. 打印 usage，看看本地模型返不返回 token 统计

任务 1（环境准备，结论记在下面注释里）：
1. 安装 Ollama、`OLLAMA_MODELS` 设到非 C 盘、拉取 `qwen3.5:27b`——**均已完成**
   （踩坑记录见 Obsidian「Ollama安装与配置」：`OLLAMA_HOST=0.0.0.0` 会让 CLI 连不上）
2. 用 `ollama ps` 记录显存占用，与 notes_01 里的估算公式对比
   —— 官方标 17 GB，你实测多少？**差值由什么构成？**

任务 3（对比实验，结论记在下面注释里）：
1. 再拉一个小模型 `qwen3-vl:8b`（6.1 GB），同一个 prompt 分别跑 27b 和 8b，
   记录 tokens/s 与回答质量的差异
2. 把 `num_ctx` 从默认调到 16384，观察 `ollama ps` 里显存的变化
   —— 这就是 KV cache 的实测大小

要求/提示：
- 本机有 SOCKS 代理，**必须处理 NO_PROXY 绕过**，否则连不上本地服务（.env 里已配）
- 本机 WMI 会误报显存 4GB，一律以 `nvidia-smi` 为准
- 如果模型明显变慢，先看是不是有层被卸载到 CPU（`ollama ps` 的 PROCESSOR 列）
- 完成标准：普通调用 + 流式都跑通；注释里有 27b / 8b 两组实测数据 + num_ctx 前后的显存对比
"""
