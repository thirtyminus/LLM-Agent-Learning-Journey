#!/usr/bin/env python3
"""
planner/base_planner.py — Planner 抽象基类

所有规划器继承同一个接口，方便替换和对比。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BasePlanner(ABC):
    """规划器基类

    子类需要实现：
    - name: 规划器名称
    - plan(): 生成规划
    - execute_step(): 执行单个步骤
    """

    name: str = ""

    @abstractmethod
    def plan(self, goal: str, **kwargs) -> list[dict]:
        """根据目标生成步骤规划

        Args:
            goal: 目标描述
            **kwargs: 额外上下文（约束、偏好等）

        Returns:
            list[dict]: 步骤列表，每步包含 step_id, description, depends_on 等
        """
        pass

    @abstractmethod
    def execute_step(self, step: dict, context: Optional[dict[str, Any]] = None) -> dict:
        """执行单个步骤

        Args:
            step: 步骤信息
            context: 全局上下文（可被步骤读写）

        Returns:
            dict: 执行结果，包含 step_id, status, output, context_updates
        """
        pass

    def replan(
        self,
        original_goal: str,
        steps: list[dict],
        completed: list[dict],
        failed_step: dict,
        context: dict[str, Any],
    ) -> list[dict]:
        """当某步失败时重新规划（默认实现：返回原计划）

        Args:
            original_goal: 原始目标
            steps: 全部步骤
            completed: 已完成的步骤
            failed_step: 失败的步骤
            context: 当前上下文

        Returns:
            list[dict]: 调整后的步骤规划
        """
        return steps

    def __repr__(self) -> str:
        return f"<Planner {self.name}>"
