#!/usr/bin/env python3
"""
tools/tool_base.py — 工具基类

所有 Agent 工具继承 BaseTool，统一注册和调用接口。
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具基类

    子类需要定义：
    - name: 工具名称（模型引用时使用）
    - description: 工具描述（注入 System Prompt）
    - run(): 工具执行逻辑
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, **kwargs) -> str:
        """执行工具，返回结果字符串"""
        pass

    def to_prompt_block(self) -> str:
        """生成 System Prompt 中的工具定义块"""
        return f"{self.name}: {self.description}"

    def __repr__(self):
        return f"<Tool {self.name}>"
