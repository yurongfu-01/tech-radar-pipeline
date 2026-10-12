#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechRadar 命令行中枢 (CLI Command Center)
提供开箱即用的一键执行、源管理、统计查看与 OPML 导出能力。
"""

import os
import sys
import argparse
import yaml
import xml.etree.ElementTree as ET

# 修复 Windows 控制台编码导致的 Unicode 打印异常
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pipeline.engine import TechRadarPipeline
from pipeline.db import StateDatabase

def list_sources(sources_file: str):
    if not os.path.exists(sources_file):
        print(f"[错误] 找不到源配置文件: {sources_file}")
        return

    with open(sources_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    sources = data.get("sources", [])

    print("\n" + "=" * 80)
    print("📋 当前已收录的行业权威内容源 (Curated Authority Sources)")
    print("=" * 80)
    print(f"{'类别':<12} | {'权威分':<6} | {'源标识 (ID)':<20} | {'名称与描述'}")
    print("-" * 80)

    category_map = {
        "conference": "顶级大会讲座",
        "podcast": "硬核深度播客",
        "blog": "大厂工程博客"
    }

    for s in sources:
        cat = category_map.get(s.get("category"), s.get("category", "其他"))
        score = str(s.get("authority_score", 9.0))
        s_id = s.get("id", "")
        name = s.get("name", "")
        status = "🟢" if s.get("enabled", True) else "⚪"
        print(f"{status} {cat:<9} | {score:<6} | {s_id:<20} | {name}")
    print("=" * 80 + "\n")

def show_stats(db_path: str):
    db = StateDatabase(db_path)
    stats = db.get_statistics()
    print("\n" + "=" * 50)
    print("📊 TechRadar 知识库状态概览")
    print("=" * 50)
    print(f"📡 监控中的活跃源:   {stats.get('active_sources', 0)}")
    print(f"✨ 累计发现条目:     {stats.get('discovered', 0)}")
    print(f"📥 成功拉取内容:     {stats.get('fetched', 0)}")
    print(f"🧠 Agent 研读并入库: {stats.get('synthesized', 0)}")
    print(f"❌ 异常失败记录:     {stats.get('failed', 0)}")
    print("=" * 50 + "\n")

def add_source(sources_file: str, s_id: str, name: str, category: str, feed_url: str):
    with open(sources_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    sources = data.get("sources", [])
    for existing in sources:
        if existing.get("id") == s_id:
            print(f"[提示] 源 ID '{s_id}' 已存在，请使用唯一 ID。")
            return

    new_source = {
        "id": s_id,
        "name": name,
        "category": category,
        "type": "youtube_channel" if "youtube.com" in feed_url else "rss",
        "url": feed_url,
        "feed_url": feed_url,
        "description": "用户自定义添加的行业权威源",
        "tags": [category, "自定义"],
        "authority_score": 9.0,
        "enabled": True
    }
    sources.append(new_source)
    data["sources"] = sources

    with open(sources_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"✅ 成功添加新权威源: [{s_id}] {name} ({feed_url})")

def export_opml(sources_file: str, output_file: str):
    with open(sources_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    sources = data.get("sources", [])
    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    title = ET.SubElement(head, "title")
    title.text = "TechRadar Curated Sources Export"

    body = ET.SubElement(root, "body")
    cat_outlines = {}

    for s in sources:
        cat = s.get("category", "General")
        if cat not in cat_outlines:
            cat_outlines[cat] = ET.SubElement(body, "outline", text=cat.upper(), title=cat.upper())
        feed_url = s.get("feed_url") or s.get("url", "")
        ET.SubElement(
            cat_outlines[cat],
            "outline",
            type="rss",
            text=s.get("name", ""),
            title=s.get("name", ""),
            xmlUrl=feed_url,
            htmlUrl=s.get("url", "")
        )

    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"✅ 已成功将所有源导出至标准 OPML: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="TechRadar: 行业权威讲座与工程博客自动化研读中枢")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 1. run 命令
    run_parser = subparsers.add_parser("run", help="执行自动化扫描、Agent 研读与入库")
    run_parser.add_argument("--max-items", type=int, default=1, help="每个源抓取的最大新条目数 (默认: 1)")

    # 2. list-sources 命令
    subparsers.add_parser("list-sources", help="列出所有已配置的权威源")

    # 3. stats 命令
    subparsers.add_parser("stats", help="查看知识库入库统计")

    # 4. add-source 命令
    add_parser = subparsers.add_parser("add-source", help="添加新的权威源")
    add_parser.add_argument("--id", required=True, help="唯一源标识 (如 blog-uber)")
    add_parser.add_argument("--name", required=True, help="源展示名称")
    add_parser.add_argument("--category", choices=["conference", "podcast", "blog"], default="blog", help="源类别")
    add_parser.add_argument("--feed-url", required=True, help="RSS 或 YouTube Feed URL")

    # 5. export-opml 命令
    opml_parser = subparsers.add_parser("export-opml", help="导出为 OPML 订阅文件")
    opml_parser.add_argument("--output", default="output/techradar_sources.opml", help="输出文件路径")

    args = parser.parse_args()

    sources_file = "config/sources.yaml"
    config_file = "config/pipeline_config.yaml"
    db_path = "data/state_store.db"

    if args.command == "run":
        pipeline = TechRadarPipeline(sources_file, config_file)
        pipeline.run_cycle(max_items_override=args.max_items)
    elif args.command == "list-sources":
        list_sources(sources_file)
    elif args.command == "stats":
        show_stats(db_path)
    elif args.command == "add-source":
        add_source(sources_file, args.id, args.name, args.category, args.feed_url)
    elif args.command == "export-opml":
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        export_opml(sources_file, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
