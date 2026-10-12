# Antigravity Harness 适配指南

在 Google Antigravity 中使用本技能：

1. **自动意图激活**：
   在对话框中输入任意包含“技术雷达”、“扫描业内最新讲座”、“更新大厂工程博客”等关键词，Antigravity 将自动激活 `tech-radar-pipeline` 技能。

2. **工具链调用**：
   - 依赖项：仅需 Python 3.8+ 及 `pyyaml`
   - 执行命令：`python cli.py run --max-items 1`

3. **知识库联动**：
   产物默认输出至 `output/vault/`，可直接通过 Antigravity 生成式 UI 或在侧边栏打开 Obsidian 进行双链研读。
