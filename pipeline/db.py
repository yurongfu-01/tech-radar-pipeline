#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 状态跟踪与增量去重存储引擎 (State Store & Deduplication DB)
负责持久化跟踪所有条目的抓取、转录、合成状态，避免重复消费与刷爆接口。
"""

import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any

class StateDatabase:
    def __init__(self, db_path: str = "data/state_store.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. 抓取条目状态表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS radar_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_hash TEXT UNIQUE NOT NULL,
                source_id TEXT NOT NULL,
                source_name TEXT,
                category TEXT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                author TEXT,
                published_at TEXT,
                media_type TEXT,          -- 'video', 'podcast', 'blog'
                raw_path TEXT,            -- 原始字幕/正文快照路径
                output_path TEXT,         -- 沉淀到知识库的 Markdown 路径
                status TEXT NOT NULL,     -- 'discovered', 'fetched', 'synthesized', 'failed'
                error_msg TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_hash ON radar_items(item_hash);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_status ON radar_items(status);")

            # 2. 源活跃状态统计表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_stats (
                source_id TEXT PRIMARY KEY,
                last_checked_at TIMESTAMP,
                total_items_discovered INTEGER DEFAULT 0,
                total_items_processed INTEGER DEFAULT 0
            );
            """)
            conn.commit()

    @staticmethod
    def hash_url(url: str) -> str:
        """为 URL 生成标准 SHA256 指纹"""
        return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()

    def is_item_seen(self, url: str) -> bool:
        """检查条目是否已被系统捕获过"""
        item_hash = self.hash_url(url)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM radar_items WHERE item_hash = ?", (item_hash,))
            return cursor.fetchone() is not None

    def record_discovered(self, item: Dict[str, Any]) -> str:
        """记录发现的新条目"""
        item_hash = self.hash_url(item["url"])
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO radar_items 
            (item_hash, source_id, source_name, category, title, url, author, published_at, media_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'discovered')
            """, (
                item_hash,
                item.get("source_id", "unknown"),
                item.get("source_name", ""),
                item.get("category", "tech"),
                item["title"],
                item["url"],
                item.get("author", ""),
                item.get("published_at", ""),
                item.get("media_type", "blog")
            ))
            conn.commit()
        return item_hash

    def update_item_fetched(self, item_hash: str, raw_path: str):
        """更新条目为已拉取内容状态"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE radar_items
            SET status = 'fetched', raw_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_hash = ?
            """, (raw_path, item_hash))
            conn.commit()

    def update_item_synthesized(self, item_hash: str, output_path: str):
        """更新条目为已由 Agent 研读并入库状态"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE radar_items
            SET status = 'synthesized', output_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_hash = ?
            """, (output_path, item_hash))
            conn.commit()

    def update_item_failed(self, item_hash: str, error_msg: str):
        """记录失败条目"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE radar_items
            SET status = 'failed', error_msg = ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_hash = ?
            """, (error_msg, item_hash))
            conn.commit()

    def get_pending_synthesis(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取已抓取但尚未被 Agent 研读的条目列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM radar_items
            WHERE status = 'fetched'
            ORDER BY created_at ASC
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """获取当前雷达知识库的运行概览统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, count(*) as cnt FROM radar_items GROUP BY status")
            status_counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
            
            cursor.execute("SELECT count(DISTINCT source_id) as total_sources FROM radar_items")
            total_active_sources = cursor.fetchone()["total_sources"]
            
            return {
                "active_sources": total_active_sources,
                "discovered": status_counts.get("discovered", 0),
                "fetched": status_counts.get("fetched", 0),
                "synthesized": status_counts.get("synthesized", 0),
                "failed": status_counts.get("failed", 0),
                "total": sum(status_counts.values())
            }
