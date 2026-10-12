#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechRadar 自动化工作流调度引擎 (Pipeline Execution Engine)
统一调度上游源采集、去重过滤、字幕/正文提取、Agent 研读与知识库归档。
"""

import os
import sys
import yaml
import json
from datetime import datetime
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pipeline.db import StateDatabase
from pipeline.collectors.base import ContentItem
from pipeline.collectors.rss_collector import RSSCollector
from pipeline.collectors.video_collector import VideoCollector
from pipeline.synthesizer import AgentSynthesizer
from pipeline.pkm_exporter import PKMExporter

class TechRadarPipeline:
    def __init__(self, sources_file: str = "config/sources.yaml", config_file: str = "config/pipeline_config.yaml"):
        self.sources_file = sources_file
        self.config_file = config_file
        self.sources = self._load_sources()
        self.config = self._load_config()

        # 初始化数据库与核心组件
        db_path = self.config.get("paths", {}).get("db_path", "data/state_store.db")
        self.db = StateDatabase(db_path)

        pkm_dir = self.config.get("paths", {}).get("pkm_vault_dir", "output/vault")
        digest_dir = self.config.get("paths", {}).get("digest_dir", "output/digests")
        self.exporter = PKMExporter(vault_dir=pkm_dir, digest_dir=digest_dir)

        synthesis_mode = self.config.get("synthesis", {}).get("default_mode", "mode_b_deep")
        self.synthesizer = AgentSynthesizer(mode=synthesis_mode)

        timeout = self.config.get("request_timeout_seconds", 20)
        user_agent = self.config.get("user_agent", "")
        self.rss_collector = RSSCollector(timeout=timeout, user_agent=user_agent)
        self.video_collector = VideoCollector(timeout=timeout, user_agent=user_agent)

    def _load_sources(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.sources_file):
            return []
        with open(self.sources_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("sources", [])

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_file):
            return {}
        with open(self.config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("pipeline", {})

    def run_cycle(self, max_items_override: int = None) -> Dict[str, Any]:
        """执行完整流水线单次扫描与研读任务"""
        max_items = max_items_override or self.config.get("max_items_per_source", 3)
        print(f"\n=======================================================")
        print(f"🚀 TechRadar 工作流启动 | 监控上游源数量: {len(self.sources)}")
        print(f"=======================================================\n")

        discovered_count = 0
        processed_count = 0
        processed_records = []

        raw_dir = self.config.get("paths", {}).get("raw_cache_dir", "output/raw")
        os.makedirs(raw_dir, exist_ok=True)

        for source in self.sources:
            if not source.get("enabled", True):
                continue

            source_name = source.get("name", "Unknown")
            source_type = source.get("type", "rss")
            print(f"📡 [正在扫描源] {source_name} ({source.get('category')})...")

            # 1. 采集器分流
            if source_type in ("youtube_channel", "video"):
                items = self.video_collector.fetch_recent(source, max_items=max_items)
            else:
                items = self.rss_collector.fetch_recent(source, max_items=max_items)

            print(f"   -> 探测到最新条目: {len(items)} 条")

            # 2. 逐条处理与去重
            for item in items:
                # 检查是否已处理过
                if self.db.is_item_seen(item.url):
                    continue

                discovered_count += 1
                item_hash = self.db.record_discovered(item.to_dict())
                print(f"   ✨ [新条目发现] {item.title[:45]}...")

                try:
                    # 3. 补充提取正文或字幕
                    if item.media_type == "video":
                        item = self.video_collector.fetch_full_content(item)
                    else:
                        item = self.rss_collector.fetch_full_content(item)

                    # 缓存原始数据
                    raw_path = os.path.join(raw_dir, f"{item_hash}.json")
                    with open(raw_path, "w", encoding="utf-8") as rf:
                        json.dump(item.to_dict(), rf, ensure_ascii=False, indent=2)
                    self.db.update_item_fetched(item_hash, raw_path)

                    # 4. Agent 智能深度研读与重构
                    print(f"   🧠 [Agent 研读中] 提炼核心架构与避坑清单...")
                    markdown_doc = self.synthesizer.synthesize(item)

                    # 5. 沉淀至 PKM 知识库
                    output_file = self.exporter.export(item, markdown_doc)
                    self.db.update_item_synthesized(item_hash, output_file)
                    print(f"   ✅ [入库成功] 归档至: {output_file}")

                    processed_count += 1
                    processed_records.append({
                        "title": item.title,
                        "url": item.url,
                        "source_name": item.source_name,
                        "category": item.category,
                        "author": item.author,
                        "output_path": output_file
                    })

                except Exception as e:
                    print(f"   ❌ [处理失败] {item.title}: {e}")
                    self.db.update_item_failed(item_hash, str(e))

        # 6. 生成每日简报
        digest_file = self.exporter.write_daily_digest(processed_records)
        if digest_file:
            print(f"\n📊 [每日简报已就绪] {digest_file}")

        stats = self.db.get_statistics()
        print(f"\n=======================================================")
        print(f"🎉 本轮工作流执行完毕！")
        print(f"   - 本轮新发现条目: {discovered_count}")
        print(f"   - 本轮深度研读入库: {processed_count}")
        print(f"   - 知识库累计归档总数: {stats.get('synthesized', 0)}")
        print(f"=======================================================\n")

        return {
            "discovered": discovered_count,
            "processed": processed_count,
            "digest_file": digest_file,
            "total_stats": stats
        }
