#!/usr/bin/env python3
"""
memory_system/vector_memory.py — 向量检索记忆

把每条消息转为向量存储，查询时用余弦相似度检索最相关的历史。
不依赖消息顺序，能跨越多轮找到语义相关的内容。
"""

import math
from .base import MemoryBase


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorMemory(MemoryBase):
    """向量检索记忆

    Args:
        embedding_fn: 文本 → 向量 的函数
                      签名: (text: str) -> list[float]
        top_k: 每次检索返回的最相关消息数（默认 5）
    """

    def __init__(self, embedding_fn, top_k: int = 5):
        self.embedding_fn = embedding_fn
        self.top_k = top_k
        self.messages: list[dict] = []
        self.vectors: list[list[float]] = []

    def add(self, role: str, content: str):
        vec = self.embedding_fn(content)
        self.messages.append({"role": role, "content": content})
        self.vectors.append(vec)

    def get_context(self, query: str = "") -> list[dict]:
        if not self.messages:
            return []

        if not query:
            # 无查询时返回最近 top_k 条
            return self.messages[-self.top_k:]

        q_vec = self.embedding_fn(query)
        scores = [cosine_similarity(q_vec, v) for v in self.vectors]

        # 取得分最高的 top_k 个索引
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:self.top_k]

        return [self.messages[i] for i in sorted(top_indices)]

    def __repr__(self):
        return f"<VectorMemory msgs={len(self.messages)} top_k={self.top_k}>"
