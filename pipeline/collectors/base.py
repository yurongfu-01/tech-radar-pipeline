#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一采集器基类与数据规范 (Base Collector & Content Item Model)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ContentItem:
    url: str
    title: str
    source_id: str
    source_name: str
    category: str                               # 'conference', 'podcast', 'blog'
    media_type: str                             # 'video', 'podcast', 'blog'
    author: str = ""
    published_at: str = ""
    raw_content: str = ""                       # 纯文本正文或字幕全文
    segments: List[Dict[str, str]] = field(default_factory=list) # [{"timestamp": "01:23", "content": "..."}]
    enclosure_url: Optional[str] = None         # 音视频直链
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "category": self.category,
            "media_type": self.media_type,
            "author": self.author,
            "published_at": self.published_at,
            "raw_content": self.raw_content,
            "segments": self.segments,
            "enclosure_url": self.enclosure_url,
            "tags": self.tags,
            "metadata": self.metadata
        }

class BaseCollector(ABC):
    def __init__(self, timeout: int = 20, user_agent: str = ""):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TechRadar/1.0"

    @abstractmethod
    def fetch_recent(self, source_config: Dict[str, Any], max_items: int = 3) -> List[ContentItem]:
        """抓取指定源的最新条目元数据"""
        pass

    @abstractmethod
    def fetch_full_content(self, item: ContentItem) -> ContentItem:
        """补充提取条目的全文、字幕或文稿"""
        pass
