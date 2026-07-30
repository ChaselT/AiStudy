"""阶段 1 · 《Ollama本地模型》· 动手任务 2（含任务 1、3 的记录）

任务 2（主任务）：用 openai SDK 连本地 Ollama。
1. 把 base_url 指向本地 Ollama 的 OpenAI 兼容端点，api_key 随便填一个占位串
2. 跑通普通（非流式）调用
3. 跑通流式输出
4. 打印 usage，看看本地模型返不返回 token 统计

任务 1（环境准备，结论记在下面注释里）：
1. 安装 Ollama，设置 `OLLAMA_MODELS` 到**非 C 盘**（模型动辄十几 G）
2. 拉取 `qwen2.5:14b`，用 `ollama run` 先对话一次
3. 用 `ollama ps` 记录显存占用，与你在 notes_01 里的估算公式对比

任务 3（压力测试，结论记在下面注释里）：
1. 拉 `qwen2.5:32b-instruct-q4_K_M`
2. 观察 `ollama ps` 与 `nvidia-smi`（本机 22G 显存，32B-Q4 属于勉强能跑）
3. 记录 tokens/s 的体感差异（与 14b 对比），结论写进本文件注释

要求/提示：
- 本机 WMI 会误报显存 4GB，**一律以 nvidia-smi 为准**
- 如果 32b 明显变慢，先看是不是有部分层被卸载到 CPU（ollama ps 的 PROCESSOR 列）
- 完成标准：普通调用 + 流式都跑通；注释里有 14b / 32b 两组显存与速度实测数据
"""
