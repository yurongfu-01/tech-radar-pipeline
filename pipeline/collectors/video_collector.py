#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权威讲座与长视频采集器 (Video & Subtitle Ingestion Engine)
优先拉取 YouTube / B站 原生带时间戳字幕 (VTT/SRT)，零带宽浪费免下载大视频文件。
"""

import os
import re
import json
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

from pipeline.collectors.base import BaseCollector, ContentItem

class VideoCollector(BaseCollector):
    def __init__(self, timeout: int = 20, user_agent: str = ""):
        super().__init__(timeout, user_agent)
        self.has_ytdlp = shutil.which("yt-dlp") is not None

    def fetch_recent(self, source_config: Dict[str, Any], max_items: int = 3) -> List[ContentItem]:
        """通过 YouTube 频道 Atom Feed 极速探测最新发布的讲座"""
        feed_url = source_config.get("feed_url")
        if not feed_url:
            return []

        req = urllib.request.Request(
            feed_url,
            headers={"User-Agent": self.user_agent}
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                xml_data = resp.read()
        except Exception as e:
            print(f"[WARN] 探测 YouTube 频道失败 ({source_config.get('name')}): {e}")
            return []

        return self._parse_youtube_feed(xml_data, source_config, max_items)

    def _parse_youtube_feed(self, xml_bytes: bytes, source_config: Dict[str, Any], max_items: int) -> List[ContentItem]:
        items: List[ContentItem] = []
        try:
            root = ET.fromstring(xml_bytes)
        except Exception as e:
            print(f"[WARN] 解析 YouTube Feed 失败: {e}")
            return []

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/"
        }

        entries = root.findall("atom:entry", ns)
        for entry in entries[:max_items]:
            video_id_elem = entry.find("yt:videoId", ns)
            video_id = video_id_elem.text.strip() if video_id_elem is not None else ""
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip() if title_elem is not None else ""
            link_elem = entry.find("atom:link", ns)
            url = link_elem.get("href", "") if link_elem is not None else f"https://www.youtube.com/watch?v={video_id}"
            
            pub_elem = entry.find("atom:published", ns)
            pub_date = pub_elem.text.strip() if pub_elem is not None else ""

            # 视频简介描述
            media_group = entry.find("media:group", ns)
            desc = ""
            if media_group is not None:
                desc_elem = media_group.find("media:description", ns)
                if desc_elem is not None and desc_elem.text:
                    desc = desc_elem.text.strip()

            if url and title:
                items.append(ContentItem(
                    url=url,
                    title=title,
                    source_id=source_config.get("id", "yt"),
                    source_name=source_config.get("name", "YouTube"),
                    category="conference",
                    media_type="video",
                    author=source_config.get("name", ""),
                    published_at=pub_date,
                    raw_content=desc,
                    tags=source_config.get("tags", []),
                    metadata={"video_id": video_id}
                ))

        return items

    def fetch_full_content(self, item: ContentItem) -> ContentItem:
        """补充提取视频的带时间戳字幕 (VTT / SRT)"""
        # 优先使用 yt-dlp 抓取字幕文件
        if self.has_ytdlp:
            vtt_content = self._fetch_subtitles_via_ytdlp(item.url)
            if vtt_content:
                segments = self._parse_vtt_to_segments(vtt_content)
                if segments:
                    item.segments = segments
                    item.raw_content = " ".join([s["content"] for s in segments])
                    return item

        # 如果没有 yt-dlp 或抓取失败，退化为尝试解析视频描述与章节 (Timestamps in Description)
        segments_from_desc = self._extract_timestamps_from_description(item.raw_content)
        if segments_from_desc:
            item.segments = segments_from_desc

        return item

    def _fetch_subtitles_via_ytdlp(self, url: str) -> Optional[str]:
        """调用 yt-dlp 快速拉取字幕文本，不下载视频音频主体"""
        try:
            # 临时获取字幕
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-auto-sub",
                "--write-sub",
                "--sub-lang", "en,zh-Hans,zh",
                "--sub-format", "vtt",
                "--output", "temp_sub_%(id)s",
                url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # 查找生成的 temp_sub_*.vtt
            for fname in os.listdir("."):
                if fname.startswith("temp_sub_") and fname.endswith(".vtt"):
                    with open(fname, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    os.remove(fname)
                    return content
        except Exception as e:
            print(f"[INFO] yt-dlp 提取字幕未执行或失败: {e}")
        return None

    @staticmethod
    def _parse_vtt_to_segments(vtt_text: str) -> List[Dict[str, str]]:
        """将 WebVTT 格式字幕解析为结构化时间戳切片"""
        segments = []
        lines = vtt_text.splitlines()
        time_pattern = re.compile(r"(\d{2}:\d{2}(?::\d{2})?)\.\d{3}\s*-->\s*(\d{2}:\d{2}(?::\d{2})?)\.\d{3}")
        
        current_time = None
        current_text = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
                continue
            m = time_pattern.search(line)
            if m:
                if current_time and current_text:
                    combined = " ".join(current_text).strip()
                    # 过滤重复词
                    if combined:
                        segments.append({"timestamp": current_time, "content": combined})
                    current_text = []
                current_time = m.group(1)
            else:
                # 过滤标签如 <c> </c>
                clean_line = re.sub(r"<[^>]+>", "", line)
                if clean_line:
                    current_text.append(clean_line)

        if current_time and current_text:
            segments.append({"timestamp": current_time, "content": " ".join(current_text).strip()})

        return segments

    @staticmethod
    def _extract_timestamps_from_description(desc: str) -> List[Dict[str, str]]:
        """从讲座简介中提取章节时间戳 (如 00:00 Intro, 05:20 Architecture)"""
        segments = []
        pattern = re.compile(r"(?:^|\n)\s*\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*[-–—:]?\s*(.*)")
        for match in pattern.finditer(desc):
            ts = match.group(1)
            title = match.group(2).strip()
            if title:
                segments.append({"timestamp": ts, "content": title})
        return segments
