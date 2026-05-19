#!/usr/bin/env python3
"""
skills/__init__.py

用法：
    from skills import SkillRegistry
    from skills.builtin_skills import SummarizeSkill, TranslateSkill
"""

from .skill_base import BaseSkill
from .skill_registry import SkillRegistry

__all__ = [
    "BaseSkill",
    "SkillRegistry",
]
