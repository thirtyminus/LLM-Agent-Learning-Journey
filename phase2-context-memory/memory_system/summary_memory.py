#!/usr/bin/env python3
"""
memory_system/summary_memory.py — 摘要压缩记忆

当上下文过长时，用 LLM 把旧消息压缩为摘要，保留核心信息。
"""

from .base import MemoryBase

SYSTEM_PROMPT = """你是一个对话摘要助手。请将以下对话内容压缩为一段简洁的摘要，
保留所有关键信息：用户意图、重要事实、已做出的决定、未解决的问题。
直接输出摘要，不要额外解释。"""


class SummaryMemory(MemoryBase):
    """摘要压缩记忆

    Args:
        max_messages: 触发压缩的消息数阈值（默认 6）
        llm_summarize: 调用 LLM 生成摘要的函数
                       签名: (messages: list[dict]) -> str
    """

    def __init__(self, max_messages: int = 6, llm_summarize=None):
        self.max_messages = max_messages
        self.messages: list[dict] = []
        self.summary: str = ""
        self.llm_summarize = llm_summarize or self._mock_summarize

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) >= self.max_messages * 2:
            self._summarize()

    def _summarize(self):
        """压缩前半部分消息为摘要"""
        mid = len(self.messages) // 2
        to_summarize = self.messages[:mid]

        if self.summary:
            merge_text = f"已有摘要：{self.summary}\n\n新对话：\n" + "\n".join(
                f"{m['role']}: {m['content']}" for m in to_summarize
            )
        else:
            merge_text = "\n".join(
                f"{m['role']}: {m['content']}" for m in to_summarize
            )

        self.summary = self.llm_summarize(merge_text)
        self.messages = self.messages[mid:]

    def _mock_summarize(self, text: str) -> str:
        """当未提供 LLM 函数时，用简单的截断代替"""
        lines = text.split("\n")
        summary = "; ".join(lines[:5])
        return summary[:200] + "…" if len(summary) > 200 else summary

    def get_context(self, query: str = "") -> list[dict]:
        if self.summary:
            return [
                {"role": "system", "content": f"对话摘要：{self.summary}"},
                *self.messages,
            ]
        return self.messages

    def __repr__(self):
        return f"<SummaryMemory msgs={len(self.messages)} has_summary={bool(self.summary)}>"
