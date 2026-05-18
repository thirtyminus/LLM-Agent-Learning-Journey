#!/usr/bin/env python3
"""
memory_system/entity_memory.py — 实体记忆

从对话中提取结构化信息（人物、地点、偏好、事实），
存储为键值对并在上下文中注入。
"""

from .base import MemoryBase

EXTRACT_PROMPT = """从以下对话中提取关键信息，以 JSON 格式输出。
只提取明确提到的事实性信息，不要猜测。
输出格式：{"key": "value", ...}
如果没有可提取的信息，输出：{}"""


class EntityMemory(MemoryBase):
    """实体记忆

    Args:
        extract_fn: 从文本中提取结构化信息的函数
                    签名: (text: str) -> dict[str, str]
        recent_window: 返回上下文时保留的最近消息数（默认 5）
    """

    def __init__(self, extract_fn, recent_window: int = 5):
        self.extract_fn = extract_fn
        self.recent_window = recent_window
        self.entities: dict[str, str] = {}
        self.messages: list[dict] = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

        # 只从用户消息中提取信息
        if role == "user":
            extracted = self.extract_fn(content)
            for key, value in extracted.items():
                self.entities[key] = value

    def get_context(self, query: str = "") -> list[dict]:
        context = self.messages[-self.recent_window:] if self.messages else []

        if self.entities:
            entity_text = "已知用户信息：\n" + "\n".join(
                f"- {k}: {v}" for k, v in self.entities.items()
            )
            context = [
                {"role": "system", "content": entity_text},
                *context,
            ]

        return context

    def __repr__(self):
        return f"<EntityMemory entities={len(self.entities)} recent={self.recent_window}>"
