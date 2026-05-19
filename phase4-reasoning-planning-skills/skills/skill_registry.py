#!/usr/bin/env python3
"""
skills/skill_registry.py — 技能注册表

管理所有可用的技能，支持注册、发现、依赖解析和组合执行。
"""

from typing import Any, Optional

from .skill_base import BaseSkill


class SkillRegistry:
    """技能注册表

    全局统一的技能管理中心，提供：
    - 注册/注销技能
    - 按名称查找技能
    - 列出所有可用技能
    - 技能依赖解析（基于 DAG 拓扑排序）
    - 批量执行技能组合

    Usage:
        registry = SkillRegistry()
        registry.register(my_skill)
        skill = registry.get("translate")
        result = skill.execute(text="Hello")
    """

    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}

    # ---- 注册与注销 ----

    def register(self, skill: BaseSkill) -> None:
        """注册一个技能

        Args:
            skill: BaseSkill 实例

        Raises:
            ValueError: 技能名已存在或无效
        """
        if not skill.name:
            raise ValueError("技能名称不能为空")
        if skill.name in self._skills:
            raise ValueError(f"技能「{skill.name}」已存在")
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> None:
        """注销一个技能

        Args:
            name: 技能名称

        Raises:
            KeyError: 技能不存在
        """
        if name not in self._skills:
            raise KeyError(f"技能「{name}」未注册")
        del self._skills[name]

    # ---- 查找与发现 ----

    def get(self, name: str) -> Optional[BaseSkill]:
        """按名称获取技能"""
        return self._skills.get(name)

    def list_all(self) -> list[dict]:
        """列出所有已注册技能

        Returns:
            list[dict]: 每个技能的名称、描述、版本、依赖
        """
        return [s.get_metadata() for s in self._skills.values()]

    def search(self, query: str) -> list[dict]:
        """按关键词搜索技能（匹配名称和描述）

        Args:
            query: 搜索关键词

        Returns:
            list[dict]: 匹配的技能元数据
        """
        query_lower = query.lower()
        results = []
        for skill in self._skills.values():
            if (
                query_lower in skill.name.lower()
                or query_lower in skill.description.lower()
            ):
                results.append(skill.get_metadata())
        return results

    # ---- 依赖解析 ----

    def _expand_dependencies(self, skill_names: list[str]) -> set[str]:
        """递归扩展所有传递依赖

        Args:
            skill_names: 初始技能名称列表

        Returns:
            set[str]: 包含所有传递依赖的技能名集合
        """
        expanded = set(skill_names)
        queue = list(skill_names)
        while queue:
            name = queue.pop(0)
            skill = self.get(name)
            if skill is None:
                raise ValueError(f"依赖的技能「{name}」未注册")
            for dep in skill.dependencies:
                if dep not in expanded:
                    # 验证依赖本身已注册
                    if self.get(dep) is None:
                        raise ValueError(f"技能「{name}」依赖的「{dep}」未注册")
                    expanded.add(dep)
                    queue.append(dep)
        return expanded

    def resolve_dependencies(self, skill_names: list[str]) -> list[str]:
        """解析技能依赖，返回拓扑排序后的执行顺序

        自动递归展开传递依赖。使用 Kahn 拓扑排序算法处理 DAG。

        Args:
            skill_names: 要解析的技能名称列表

        Returns:
            list[str]: 拓扑排序后的执行顺序（无依赖的在前）

        Raises:
            ValueError: 存在循环依赖或依赖缺失
        """
        # 自动展开传递依赖
        all_names = self._expand_dependencies(skill_names)

        # 构建依赖图（仅包含 expanded 范围内的依赖）
        graph: dict[str, list[str]] = {}
        for name in all_names:
            skill = self.get(name)
            if skill is None:
                raise ValueError(f"依赖的技能「{name}」未注册")
            deps = [d for d in skill.dependencies if d in all_names]
            graph[name] = deps

        # Kahn 拓扑排序
        in_degree = {name: 0 for name in graph}
        for name, deps in graph.items():
            for dep in deps:
                # dep 是依赖项，name 依赖于 dep → 有向边 dep → name
                # 因此 name 的入度增加
                in_degree[name] = in_degree.get(name, 0) + 1

        queue = [name for name, deg in in_degree.items() if deg == 0]
        sorted_order = []

        while queue:
            node = queue.pop(0)
            sorted_order.append(node)
            for name, deps in graph.items():
                if node in deps:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        if len(sorted_order) != len(all_names):
            raise ValueError("技能依赖存在循环依赖，无法解析")

        return sorted_order

    # ---- 组合执行 ----

    def execute_pipeline(self, skill_names: list[str], **kwargs) -> dict[str, Any]:
        """按依赖顺序批量执行技能（管道模式）

        前一个技能的输出作为后一个技能的上下文注入。

        Args:
            skill_names: 技能名称列表
            **kwargs: 初始输入参数

        Returns:
            dict[str, Any]: 每个技能的执行结果，key 为技能名
        """
        order = self.resolve_dependencies(skill_names)
        results: dict[str, Any] = {}
        context = dict(kwargs)

        for name in order:
            skill = self.get(name)
            if skill is None:
                results[name] = {"error": f"技能「{name}」未找到"}
                continue

            # 注入上游结果
            skill_input = {**context, "pipeline_results": dict(results)}
            results[name] = skill.execute(**skill_input)
            context[f"{name}_output"] = results[name]

        return results

    def __len__(self) -> int:
        return len(self._skills)

    def __repr__(self) -> str:
        return f"<SkillRegistry skills={len(self)}>"
