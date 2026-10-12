#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级网页正文提取与 HTML 降噪清洗器 (Web Cleaner & Text Extractor)
专为技术博客、工程专栏设计，剥离导航栏、侧边栏、Cookie 弹窗与脚标，保留高质量正文与代码块。
"""

import re
from html.parser import HTMLParser
from typing import Tuple

class MinimalHTMLToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.ignored_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'svg', 'noscript', 'form'}
        self.current_ignored = 0
        self.in_code_block = False
        self.in_heading = False
        self.heading_level = 1

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in self.ignored_tags:
            self.current_ignored += 1
            return
        if self.current_ignored > 0:
            return

        if tag_lower in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.in_heading = True
            self.heading_level = int(tag_lower[1])
            self.output.append(f"\n\n{'#' * self.heading_level} ")
        elif tag_lower == 'pre':
            self.in_code_block = True
            self.output.append("\n\n```\n")
        elif tag_lower == 'code' and not self.in_code_block:
            self.output.append("`")
        elif tag_lower in ('p', 'div'):
            self.output.append("\n\n")
        elif tag_lower == 'li':
            self.output.append("\n- ")
        elif tag_lower == 'blockquote':
            self.output.append("\n\n> ")

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.ignored_tags:
            self.current_ignored = max(0, self.current_ignored - 1)
            return
        if self.current_ignored > 0:
            return

        if tag_lower in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.in_heading = False
            self.output.append("\n")
        elif tag_lower == 'pre':
            self.in_code_block = False
            self.output.append("\n```\n")
        elif tag_lower == 'code' and not self.in_code_block:
            self.output.append("`")

    def handle_data(self, data):
        if self.current_ignored > 0:
            return
        text = data if self.in_code_block else data.strip()
        if text:
            if not self.in_code_block and not self.in_heading and not self.output[-1:].__eq__([' ']):
                self.output.append(" ")
            self.output.append(text)

    def get_markdown(self) -> str:
        raw = "".join(self.output)
        # 清洗过多的空行
        cleaned = re.sub(r'\n{3,}', '\n\n', raw)
        return cleaned.strip()

def extract_clean_text_from_html(html_content: str) -> str:
    """提取干净的正文 Markdown 文本"""
    parser = MinimalHTMLToMarkdown()
    try:
        parser.feed(html_content)
        parser.close()
        return parser.get_markdown()
    except Exception:
        # Fallback 正则清洗
        text = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
