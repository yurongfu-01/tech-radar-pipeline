#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PKM 知识库自动化沉淀与看板生成器 (Obsidian Vault & PKM Exporter)
将提炼产物归档至指定目录，并维护 Obsidian Dataview 自动聚合看板。
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, List
from pipeline.collectors.base import ContentItem

class PKMExporter:
    def __init__(self, vault_dir: str = "output/vault", digest_dir: str = "output/digests"):
        self.vault_dir = vault_dir
        self.digest_dir = digest_dir
        os.makedirs(self.vault_dir, exist_ok=True)
        os.makedirs(self.digest_dir, exist_ok=True)
        self._ensure_dataview_dashboard()

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """清理文件名中的 Windows 非法字符"""
        clean = re.sub(r'[\\/*?:"<>|]', '_', name)
        return clean.strip()[:80]

    def export(self, item: ContentItem, markdown_content: str) -> str:
        """归档单篇 Markdown 文档至分类子目录"""
        category_dir = os.path.join(self.vault_dir, self.sanitize_filename(item.category))
        os.makedirs(category_dir, exist_ok=True)

        date_prefix = datetime.now().strftime("%Y%m%d")
        safe_title = self.sanitize_filename(item.title)
        filename = f"{date_prefix}_{safe_title}.md"
        target_path = os.path.join(category_dir, filename)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return target_path

    def _ensure_dataview_dashboard(self):
        """确保知识库根目录具备 Dataview 自动看板"""
        dashboard_path = os.path.join(self.vault_dir, "00-技术雷达总看板.md")
        if not os.path.exists(dashboard_path):
            content = """---
title: "全球技术雷达与权威讲座总看板"
date: 2026-10-12
tags: [知识库/看板, 技术雷达]
---

# 全球技术雷达与权威讲座总看板

> [!TIP]
> 本看板由 **TechRadar Pipeline** 自动化维护，原生兼容 **Obsidian Dataview** 插件。
> 每天自动扫描全球权威大会 (QCon, USENIX)、顶尖播客 (Dwarkesh, Latent Space) 与知名科技大厂工程博客。

---

## 1. 最新研读流 (Live Feed)

```dataview
TABLE 
  author AS "讲师 / 作者", 
  platform AS "来源平台", 
  type AS "模式", 
  date AS "研读日期"
FROM #学习笔记/深度研读 OR #学习笔记/原貌切片
SORT file.mtime DESC
LIMIT 20
```

---

## 2. 顶级技术会议与讲座 (Conferences)

```dataview
TABLE 
  author AS "大会/讲师", 
  platform AS "平台", 
  date AS "时间"
FROM #领域/conference
SORT date DESC
```

---

## 3. 科技大厂工程演进专栏 (Engineering Blogs)

```dataview
TABLE 
  author AS "公司/团队", 
  date AS "发布日期"
FROM #领域/blog
SORT date DESC
```
"""
            with open(dashboard_path, "w", encoding="utf-8") as f:
                f.write(content)

    def write_daily_digest(self, processed_items: List[Dict[str, Any]]) -> str:
        """生成当日技术雷达汇编报告 (Daily Radar Digest)"""
        if not processed_items:
            return ""

        today = datetime.now().strftime("%Y-%m-%d")
        digest_file = os.path.join(self.digest_dir, f"radar_digest_{datetime.now().strftime('%Y%m%d')}.md")

        lines = [
            f"# TechRadar 每日权威研读简报 ({today})",
            "",
            f"> 今日雷达共捕获并深度解析了 **{len(processed_items)}** 篇业内高价值讲座与工程专栏。",
            "",
            "---",
            "",
            "## 核心洞察一览 (Executive Summary)",
            ""
        ]

        for idx, item in enumerate(processed_items, 1):
            lines.append(f"### {idx}. [{item['title']}]({item['url']})")
            lines.append(f"- **来源**：`{item['source_name']}` | **分类**：`{item['category']}` | **讲师/作者**：`{item['author']}`")
            lines.append(f"- **本地笔记**：`{item['output_path']}`")
            lines.append("")

        with open(digest_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return digest_file
