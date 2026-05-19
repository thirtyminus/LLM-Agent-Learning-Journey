#!/usr/bin/env python3
"""
planner/simple_planner.py — 简单顺序规划器

最基础的规划实现：将目标分解为一系列顺序执行的步骤。
适合步骤依赖明确、无需并行或动态调整的场景。
"""

import os
from typing import Any, Callable, Optional

from .base_planner import BasePlanner


def _default_llm(messages: list[dict]) -> str:
    """默认 LLM 调用：优先使用 DeepSeek API，无 Key 时返回空字符串（降级到规则分解）"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=30)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except ImportError:
            pass
        except Exception:
            pass
    return ""


class SimplePlanner(BasePlanner):
    """简单顺序规划器

    把目标分解为一组顺序步骤，前一步的 output 自动注入后一步的 context。

    默认行为：
    - 没有 DEEPSEEK_API_KEY → 规则分解（无需 LLM）
    - 有 DEEPSEEK_API_KEY  → 自动用 LLM 分解
    - 传入 llm_fn           → 使用自定义 LLM
    """

    name: str = "simple_planner"

    def __init__(self, llm_fn: Optional[Callable] = None):
        self._llm_fn = llm_fn

    def _get_llm(self) -> Optional[Callable]:
        """获取当前生效的 LLM 函数"""
        return self._llm_fn or _default_llm

    def plan(self, goal: str, **kwargs) -> list[dict]:
        """将目标分解为顺序步骤

        Args:
            goal: 目标描述
            **kwargs: 可选传入 llm_fn 覆盖默认 LLM

        Returns:
            list[dict]: 步骤列表
        """
        llm_fn = kwargs.get("llm_fn") or self._get_llm()

        if llm_fn:
            steps, raw = self._plan_with_llm(goal, llm_fn)
            # 如果 LLM 返回空（无 Key），降级到规则
            if steps:
                return steps

        return self._plan_with_rules(goal, kwargs)

    def _plan_with_llm(self, goal: str, llm_fn) -> tuple[list[dict], str]:
        """使用 LLM 智能分解步骤

        Returns:
            tuple[list[dict], str]: (步骤列表, LLM 原始回复)
            无 Key 或解析失败时返回 ([], response)
        """
        prompt = (
            "请将以下目标分解为 3~6 个顺序执行的步骤。\n"
            "每个步骤包含 step_id（数字）、description（步骤描述）、"
            "depends_on（依赖的上一步 id 列表，通常为 [前一步]）。\n"
            f"目标：{goal}\n"
            "以 JSON 列表格式输出：\n"
            '[{"step_id": 1, "description": "...", "depends_on": []}, ...]'
        )
        response = llm_fn([{"role": "user", "content": prompt}])

        # 无 Key 时返回空，让 plan() 降级到规则分解
        if not response or not response.strip():
            return [], response

        import json
        import re

        # 去掉 markdown 代码块标记
        cleaned = re.sub(r"```(?:json)?\s*", "", response).strip()
        json_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0)), response
            except json.JSONDecodeError:
                pass

        # 解析失败时返回空
        return [], response

    def _plan_with_rules(self, goal: str, kwargs: dict) -> list[dict]:
        """基于规则的关键词分解"""
        steps = [
            {
                "step_id": 1,
                "description": f"分析目标「{goal}」，明确需求和约束条件",
                "depends_on": [],
            },
            {
                "step_id": 2,
                "description": "收集相关资料和信息",
                "depends_on": [1],
            },
            {
                "step_id": 3,
                "description": "制定初步方案",
                "depends_on": [2],
            },
            {
                "step_id": 4,
                "description": "评估方案可行性，调整优化",
                "depends_on": [3],
            },
            {
                "step_id": 5,
                "description": f"输出最终结果：{goal}",
                "depends_on": [4],
            },
        ]
        return steps

    def execute_step(self, step: dict, context: Optional[dict[str, Any]] = None) -> dict:
        """执行单个步骤

        Args:
            step: 步骤信息
            context: 全局上下文

        Returns:
            dict: 执行结果
        """
        context = context or {}
        step_id = step["step_id"]
        description = step["description"]

        # 将前一步的输出注入当前步的上下文
        prev_output = context.get(f"step_{step_id - 1}_output", "")

        simulated_output = description[:80]

        # 上下文中的信息会累积
        context_updates = {}
        if "constraints" in context:
            context_updates["constraints_used"] = context["constraints"]

        return {
            "step_id": step_id,
            "status": "completed",
            "output": simulated_output,
            "context_updates": context_updates,
        }

    def run_all(self, goal: str, verbose: bool = False, **kwargs) -> list[dict]:
        """顺序执行全部步骤

        Args:
            goal: 目标描述
            verbose: 是否打印执行过程
            **kwargs: 传递给 plan() 的额外参数

        Returns:
            list[dict]: 所有步骤的执行结果
        """
        if verbose:
            print(f"📋 生成步骤规划：目标「{goal}」")

        llm_fn = kwargs.get("llm_fn") or self._get_llm()
        plan_raw = ""

        if llm_fn:
            steps, plan_raw = self._plan_with_llm(goal, llm_fn)
            if not steps:
                steps = self._plan_with_rules(goal, kwargs)
        else:
            steps = self._plan_with_rules(goal, kwargs)

        if verbose:
            print(f"   生成了 {len(steps)} 个步骤")
            if plan_raw:
                print(f"\n  ── LLM 规划过程 ──")
                print(f"  {plan_raw[:500]}")
                print(f"  ────────────────")

        results = []
        context: dict[str, Any] = {"_goal": goal}

        for step in steps:
            if verbose:
                print(f"\n  ▶ Step {step['step_id']}: {step['description'][:50]}...")

            result = self.execute_step(step, context)
            results.append(result)
            context[f"step_{step['step_id']}_output"] = result["output"]
            context.update(result.get("context_updates", {}))

            if verbose:
                print(f"    状态：{result['status']}")
                print(f"    → {result['output'][:80]}")

        return results
