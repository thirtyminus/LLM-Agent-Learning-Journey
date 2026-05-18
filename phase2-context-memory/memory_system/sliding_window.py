#!/usr/bin/env python3
"""
memory_system/sliding_window.py — 滑动窗口记忆

只保留最近 N 条消息，超出的一刀切掉。
实现最简单，代价最低，但会丢失早期关键信息。
"""

from .base import MemoryBase


class SlidingWindow(MemoryBase):
    """滑动窗口记忆

    Args:
        window_size: 保留的消息数量上限（默认 10）
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.messages: list[dict] = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.window_size:
            self.messages = self.messages[-self.window_size:]

    def get_context(self, query: str = "") -> list[dict]:
        return self.messages

    def __repr__(self):
        return f"<SlidingWindow size={self.window_size} msgs={len(self.messages)}>"
