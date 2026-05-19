#!/usr/bin/env python3
"""
skills/skill_base.py — 技能抽象基类

技能（Skill）是一个可注册、可组合的能力单元。
相比工具（Tool），技能更具复合性——它可以包含多个子任务，
甚至组合其他技能。
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    """技能基类

    子类需要定义：
    - name: 技能名称（全局唯一）
    - description: 技能描述（注册表中使用的标识）
    - version: 技能版本
    - dependencies: 依赖的其他技能名称列表
    - execute(): 技能执行逻辑
    """

    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    dependencies: list[str] = []

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行技能

        Args:
            **kwargs: 技能所需的输入参数

        Returns:
            Any: 技能执行结果
        """
        pass

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数（可选重写）

        默认实现：检查是否有参数传入。
        """
        return len(kwargs) > 0

    def get_metadata(self) -> dict:
        """返回技能元数据"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "dependencies": self.dependencies,
            "class": self.__class__.__name__,
        }

    def __repr__(self) -> str:
        return f"<Skill {self.name} v{self.version}>"
