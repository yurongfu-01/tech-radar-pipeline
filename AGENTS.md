# 工作区通用规则：Agent 自动化工作流执行规范

在本工作区（`d:\Agent视频学习录`）中，**智能体 (Agent) 的核心定位是“工作流执行中枢”：只负责按既定工作流执行批量扫描、采集、提炼与知识库沉淀任务，严禁擅自偏离工作流主线**。

> 核心规范文档：[开发者经验分析与Agent自动化执行规范.md](./开发者经验分析与Agent自动化执行规范.md)  
> 资产总索引看板：[README.md](./README.md)  
> 桌面归档目标库：[`C:\Users\jiang\Desktop\开发经验\开发者经验分析-Agent`](file:///C:/Users/jiang/Desktop/开发经验/开发者经验分析-Agent)

---

## 1. 核心定位与执行铁律 (Execution Dogma)

1. **工作流驱动，职责单一 (Workflow-Driven Only)**：
   - 本工作区不进行发散式需求设计或临时造轮子，Agent 严格依照内置的 `TechRadar-Pipeline` 工作流及标准化作业程序 (SOP) 运行。
2. **免下载轻量化摄取 (Zero Heavy Video Download)**：
   - 针对长视频/大会录播，优先通过 Atom/RSS 探测，调用字幕 API / VTT 秒级抓取文本，杜绝无节制下载数 GB 视频文件造成带宽与磁盘浪费。
3. **严格增量去重门禁 (SHA-256 Deduplication Gate)**：
   - 所有 URL 进行 SHA-256 哈希计算并持久化至 `data/state_store.db`，确保一次处理、永久跳过，杜绝重复抓取与 Token 消耗。
4. **结构化六段式深度提炼 (Six-Stage Deep Synthesis)**：
   - 每一篇研读产物必须满足高价值知识标准：涵盖核心概述 (Mermaid)、机理拆解、工业级高危盲区 (Gotchas)、实战工程载荷 (代码/配置) 与准出自检清单 (Checklist)。
5. **强制同步至桌面 Agent 经验库 (Mandatory Sync)**：
   - 每次工作流执行完毕后，必须无缝同步沉淀至桌面经验库：`C:\Users\jiang\Desktop\开发经验\开发者经验分析-Agent`，并保持双层访问保障机制（根目录独立直读报告 + topics 专题子库 + 全局看板）。

---

## 2. 常用执行指令 (Workflow CLI Commands)

在工作区终端中，统一使用 Python 虚拟环境执行调度：

```powershell
# 1. 运行单轮雷达巡检与深度研读任务（默认每个源处理 1 条最新动态）
& "D:\PythonProject\.venv\Scripts\python.exe" cli.py run --max-items 1

# 2. 查看当前监控中的权威源矩阵（顶级大会、播客、大厂博客）
& "D:\PythonProject\.venv\Scripts\python.exe" cli.py list-sources

# 3. 查看知识库累计入库统计
& "D:\PythonProject\.venv\Scripts\python.exe" cli.py stats

# 4. 执行桌面经验库强一致同步（自动更新根目录独立报告与全局看板）
& "D:\PythonProject\.venv\Scripts\python.exe" sync_to_desktop.py
```

---

## 3. 产物交付与质检门禁 (Pre-flight Checklist)

每次执行完成后，输出产物必须通过以下 5 项核验：
- [ ] Frontmatter 具备完整字段（title, source_url, platform, author, date, type, tags, status）；
- [ ] 包含合法渲染的 Mermaid 图表（架构拓扑图、时序图或流程图）；
- [ ] 剖析了生产环境下的真实高危盲区与反模式（网络超时、幂等性、并发冲突）；
- [ ] 提供了可直接复制执行的代码/配置工程载荷；
- [ ] 目标目录 `C:\Users\jiang\Desktop\开发经验\开发者经验分析-Agent` 保持强一致同步。
