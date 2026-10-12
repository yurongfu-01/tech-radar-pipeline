# Claude Code / Codex / Hermes Harness 适配指南

本工作流为 100% 宿主中立（Harness Agnostic）设计，适用于以下各类主流 Agent 环境：

## 1. Claude Code
在 Claude Code 会话中：
```bash
claude "运行技术雷达流水线，抓取最新的一篇行业讲座并输出六段式深度研读"
```
Claude Code 可通过 bash 工具直接调用 `python cli.py run`，并直接读取生成的结构化 Markdown。

## 2. OpenAI Codex / CLI
通过标准终端或 Function Calling：
```bash
python cli.py run --max-items 2
```

## 3. Hermes / HermesStudio
将本项目作为 Tool 或 Skill 挂载至 Hermes workspace，可在后台通过定时 Cron 插件执行 `python cli.py run`，自动同步状态至远程 PKM 知识库。
