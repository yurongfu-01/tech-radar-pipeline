#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用 RSS / Atom / 播客采集器 (RSS & Podcast Ingestion Engine)
支持各大公司技术博客 RSS、Substack、播客音频 Enclosure 提取与正文初筛。
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional

from pipeline.collectors.base import BaseCollector, ContentItem
from pipeline.collectors.web_cleaner import extract_clean_text_from_html

class RSSCollector(BaseCollector):
    def fetch_recent(self, source_config: Dict[str, Any], max_items: int = 3) -> List[ContentItem]:
        """抓取 RSS/Atom 源的最新条目"""
        feed_url = source_config.get("feed_url") or source_config.get("url")
        if not feed_url:
            return []

        req = urllib.request.Request(
            feed_url,
            headers={"User-Agent": self.user_agent, "Accept": "application/rss+xml, application/atom+xml, text/xml, */*"}
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                xml_data = resp.read()
        except Exception as e:
            # 记录警告并返回空列表
            print(f"[WARN] 抓取 RSS 失败 ({source_config.get('name')}): {e}")
            return []

        return self._parse_feed_xml(xml_data, source_config, max_items)

    def _parse_feed_xml(self, xml_bytes: bytes, source_config: Dict[str, Any], max_items: int) -> List[ContentItem]:
        items: List[ContentItem] = []
        try:
            root = ET.fromstring(xml_bytes)
        except Exception as e:
            print(f"[WARN] 解析 XML 失败 ({source_config.get('name')}): {e}")
            return []

        # 检查是否为 RSS (root tag 为 rss)
        channel = root.find("channel")
        if channel is not None:
            # RSS 2.0 格式
            rss_items = channel.findall("item")
            for item_elem in rss_items[:max_items]:
                item = self._parse_rss_item(item_elem, source_config)
                if item:
                    items.append(item)
            return items

        # 检查是否为 Atom 格式 (root tag 为 feed，通常包含 xmlns)
        # 移除命名空间处理
        entries = root.findall("{http://www.w3.org/2005/Atom}entry") or root.findall("entry")
        for entry_elem in entries[:max_items]:
            item = self._parse_atom_entry(entry_elem, source_config)
            if item:
                items.append(item)

        return items

    def _parse_rss_item(self, item_elem: ET.Element, source_config: Dict[str, Any]) -> Optional[ContentItem]:
        title = item_elem.findtext("title", "").strip()
        link = item_elem.findtext("link", "").strip()
        if not link or not title:
            return None

        # 提取发布时间
        pub_date = item_elem.findtext("pubDate", "").strip()
        author = item_elem.findtext("author", "") or item_elem.findtext("{http://purl.org/dc/elements/1.1/}creator", "")
        author = author.strip() or source_config.get("name", "")

        # 提取正文内容 (优先 content:encoded，其次 description)
        content_encoded = item_elem.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", "")
        description = item_elem.findtext("description", "")
        raw_html = content_encoded or description or ""
        clean_text = extract_clean_text_from_html(raw_html)

        # 检查是否有播客音频 enclosure
        enclosure_url = None
        enclosure = item_elem.find("enclosure")
        if enclosure is not None:
            enclosure_url = enclosure.get("url")

        category = source_config.get("category", "blog")
        media_type = "podcast" if enclosure_url or category == "podcast" else "blog"

        return ContentItem(
            url=link,
            title=title,
            source_id=source_config.get("id", "rss"),
            source_name=source_config.get("name", "RSS"),
            category=category,
            media_type=media_type,
            author=author,
            published_at=pub_date,
            raw_content=clean_text,
            enclosure_url=enclosure_url,
            tags=source_config.get("tags", [])
        )

    def _parse_atom_entry(self, entry_elem: ET.Element, source_config: Dict[str, Any]) -> Optional[ContentItem]:
        title = (entry_elem.findtext("{http://www.w3.org/2005/Atom}title") or entry_elem.findtext("title") or "").strip()
        
        # Link 在 Atom 中通常是属性 href
        link = ""
        link_elem = entry_elem.find("{http://www.w3.org/2005/Atom}link") or entry_elem.find("link")
        if link_elem is not None:
            link = link_elem.get("href", "").strip()

        if not link or not title:
            return None

        pub_date = (entry_elem.findtext("{http://www.w3.org/2005/Atom}published") or 
                    entry_elem.findtext("{http://www.w3.org/2005/Atom}updated") or "").strip()

        content = (entry_elem.findtext("{http://www.w3.org/2005/Atom}content") or 
                   entry_elem.findtext("{http://www.w3.org/2005/Atom}summary") or "")
        clean_text = extract_clean_text_from_html(content)

        return ContentItem(
            url=link,
            title=title,
            source_id=source_config.get("id", "atom"),
            source_name=source_config.get("name", "Atom"),
            category=source_config.get("category", "blog"),
            media_type="blog",
            author=source_config.get("name", ""),
            published_at=pub_date,
            raw_content=clean_text,
            tags=source_config.get("tags", [])
        )

    def fetch_full_content(self, item: ContentItem) -> ContentItem:
        """如果 RSS 仅提供了摘要且正文过短，尝试抓取原网页正文"""
        if len(item.raw_content) > 500:
            return item

        req = urllib.request.Request(item.url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                full_text = extract_clean_text_from_html(html)
                if len(full_text) > len(item.raw_content):
                    item.raw_content = full_text
        except Exception as e:
            print(f"[INFO] 补充抓取网页全文跳过 ({item.url}): {e}")

        return item
