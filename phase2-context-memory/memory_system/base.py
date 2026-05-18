#!/usr/bin/env python3
"""
memory_system/base.py — 记忆策略抽象基类
"""

from abc import ABC, abstractmethod


class MemoryBase(ABC):
    @abstractmethod
    def add(self, role: str, content: str):
        pass

    @abstractmethod
    def get_context(self, query: str = "") -> list[dict]:
        pass
