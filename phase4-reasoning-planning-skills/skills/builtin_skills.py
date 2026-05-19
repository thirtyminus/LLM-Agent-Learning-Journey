#!/usr/bin/env python3
"""
skills/builtin_skills.py — 内置示例技能

一组即开即用的技能示例，演示技能注册表的用法。
"""

import json
import re
from typing import Any

from .skill_base import BaseSkill


# ============================================================
# 文本技能
# ============================================================

class SummarizeSkill(BaseSkill):
    """文本摘要技能 — 将长文本压缩为摘要"""

    name = "summarize"
    description = "将长文本压缩为简短摘要"
    version = "1.0.0"

    def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        max_length = kwargs.get("max_length", 100)

        if not text:
            return "错误：缺少输入文本"

        # 模拟：取前几句 + 截断
        sentences = re.split(r"[。！？\n]", text)
        summary = "。".join(sentences[:3]) + "。"
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return f"【摘要】{summary}"


class TranslateSkill(BaseSkill):
    """翻译技能 — 文本翻译（模拟）"""

    name = "translate"
    description = "将文本翻译成目标语言"
    version = "1.0.0"

    def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        target = kwargs.get("target_lang", "en")

        if not text:
            return "错误：缺少输入文本"

        # 模拟翻译（真实场景接入 LLM API）
        translations = {
            "en": f"[Translated] {text}",
            "zh": f"[翻译] {text}",
            "ja": f"[翻訳] {text}",
        }
        return translations.get(target, f"[{target}] {text}")


class FormatSkill(BaseSkill):
    """格式化技能 — 将文本转为 JSON 等结构化格式"""

    name = "format"
    description = "将文本转为结构化格式（JSON、Markdown 等）"
    version = "1.0.0"

    def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        fmt = kwargs.get("format", "json")

        if fmt == "json":
            return json.dumps({"content": text, "length": len(text)}, ensure_ascii=False)
        elif fmt == "markdown":
            return f"> {text}\n\n*长度：{len(text)} 字*"
        return text


# ============================================================
# 数据处理技能
# ============================================================

class ExtractKeywordsSkill(BaseSkill):
    """关键词提取技能"""

    name = "extract_keywords"
    description = "从文本中提取关键词"
    version = "1.0.0"

    def execute(self, **kwargs) -> list[str]:
        text = kwargs.get("text", "")

        if not text:
            return []

        # 模拟提取：按长度和频次规则
        words = re.findall(r"[\w\u4e00-\u9fff]+", text)
        # 过滤过短的词，取前5个
        keywords = [w for w in words if len(w) >= 2][:5]
        return keywords if keywords else [text[:10]]


class CountSkill(BaseSkill):
    """文本统计技能"""

    name = "count"
    description = "统计文本的字数、词数、句数"
    version = "1.0.0"

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")

        char_count = len(text)
        word_count = len(re.findall(r"[\w\u4e00-\u9fff]+", text))
        sentence_count = len(re.findall(r"[。！？\n]+", text)) or 1

        return {
            "characters": char_count,
            "words": word_count,
            "sentences": sentence_count,
        }


# ============================================================
# 组合技能
# ============================================================

class AnalysisPipelineSkill(BaseSkill):
    """分析管道技能 — 组合多个子技能完成完整分析"""

    name = "analyze"
    description = "全文本分析：统计 + 摘要 + 关键词提取"
    version = "1.0.0"
    dependencies = ["count", "summarize", "extract_keywords"]

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        pipeline_results = kwargs.get("pipeline_results", {})

        # 如果管道已经执行了依赖技能，直接使用其结果
        analysis = {
            "input_length": len(text),
            "stats": pipeline_results.get("count", {}),
            "summary": pipeline_results.get("summarize", ""),
            "keywords": pipeline_results.get("extract_keywords", []),
        }

        return analysis
