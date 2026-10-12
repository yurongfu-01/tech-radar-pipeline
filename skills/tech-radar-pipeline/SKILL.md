---
name: tech-radar-pipeline
description: 行业权威技术讲座、前沿播客与大厂工程博客自动化研读与知识雷达流水线（Harness通用版·适配Antigravity/ClaudeCode/Codex/Hermes）。无缝整合全球顶会录播(StrangeLoop, USENIX, QCon, GOTO)、顶尖AI播客(Latent Space, Dwarkesh, Lex Fridman, 硅谷101)与500+顶级大厂工程博客(OpenAI, Netflix, Stripe, Cloudflare)，支持免下载大视频的秒级字幕抓取、增量SHA256去重防刷、双模式深度研读提炼（模式A原貌切片/模式B六段式研读案）、以及Obsidian/Notion Dataview总看板自动沉淀。
---

# Tech-Radar-Pipeline 技术雷达与自动化研读规范 (Harness 通用版)

本规范定义了各类主流 Agent Harness（包括 Antigravity、Claude Code、OpenAI Codex、Hermes/HermesStudio）在执行行业权威讲座、前沿播客与大厂工程博客批量监控、采集、研读与知识库沉淀时的统一标准化作业程序。

---

## 1. 核心定位与原则

1. **破除冷启动痛点（Curated Authority Bootstrap）**：
   - 彻底解决“想让 Agent 分析行业权威内容但缺乏输入源”的问题。内置结构化权威源矩阵（涵盖顶级学术工业大会、硬核播客与全球大厂工程博客 OPML）。
2. **轻量极速摄取（Zero Heavy Video Download）**：
   - 针对 40~60 分钟的大会讲座，**严禁无节制下载数 GB 的视频文件**。优先通过 Atom Feed 极速探测，通过 `yt-dlp` / 字幕 API 秒级提取带时间戳的 VTT/SRT 字幕文本，零带宽浪费。
3. **严格增量排重（SHA-256 Deduplication Gate）**：
   - 所有 URL 进行标准 SHA-256 指纹计算并持久化于本地 SQLite 状态库，确保一次入库、永久跳过，杜绝重复爬取与 Token 浪费。
4. **双模式精准提炼（Dual-Mode Synthesis）**：
   - **模式 A【高保真原貌切片复刻档】**：零脑补，忠实记录时间戳分段与一手发言原意，文末附完整逐字稿。
   - **模式 B【六段式深度研读案】**：直击本质，提炼全景时间轴 (Mermaid timeline)、系统拓扑时序 (Mermaid sequenceDiagram)、3大工业高危盲区、工程落地载荷与准出自检清单 (Checklist)。
5. **知识库原生兼容 (PKM-Native)**：
   - 生成文档头部严格包含合规 YAML Frontmatter，并在知识库根目录维护开箱即用的 Obsidian Dataview 自动聚合总看板。
6. **跨 Harness 环境解耦 (Harness Agnostic)**：
   - 适配各类 Agent Harness 命令行调用，不绑定单一私有接口。

---

## 2. 自然语言意图路由规约 (Intent Routing)

当用户在任意 Harness 终端中表达以下意图时，自动路由激活本技能：

| 用户自然语言指令模式 | 意图识别 | 执行动作 |
| :--- | :--- | :--- |
| “扫描业内最新权威讲座/博客”、“跑一下技术雷达” | **全流程雷达巡检** | 执行 `python cli.py run --max-items 2`，全网扫描、抓取并提炼入库 |
| “我们监控了哪些权威大会和播客？”、“查看内容源” | **权威源资产检索** | 执行 `python cli.py list-sources` 并汇报当前覆盖的领域和评分 |
| “添加这个播客/频道到雷达：<URL>” | **动态源录入** | 执行 `python cli.py add-source --id ... --feed-url <URL>` |
| “把技术雷达的订阅源导出来” | **OPML 导出** | 执行 `python cli.py export-opml`，生成可供第三方阅读器订阅的 OPML 文件 |
| “查看知识库累计沉淀了多少篇” | **知识库状态盘点** | 执行 `python cli.py stats`，输出入库统计与失败排查建议 |
