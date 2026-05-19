#!/usr/bin/env python3
"""
planner/plan_execute_agent.py — Plan-and-Execute Agent

将规划与执行分离为两个阶段：
1. Plan 阶段：LLM 先生成完整的执行计划
2. Execute 阶段：逐步骤执行，支持动态重规划

相比 ReAct（边想边做），Plan-and-Execute 更适合复杂多步骤任务。
"""

import json
import os
import re
from typing import Any, Callable, Optional

from .base_planner import BasePlanner


def _default_llm(messages: list[dict]) -> str:
    """默认 LLM 调用：优先使用 DeepSeek API，无 Key 时回退到模拟"""
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

    # 无 API Key 或调用失败时回退到模拟
    from ._mock_llm import mock_plan_execute_llm
    return mock_plan_execute_llm(messages)


class PlanExecuteAgent(BasePlanner):
    """Plan-and-Execute Agent

    流程：
    1. 接收目标 → 生成计划
    2. 逐个执行步骤
    3. 某步失败 → 调用 replan() 调整剩余计划
    4. 全部完成 → 汇总结果

    Args:
        llm_fn: LLM 调用函数，签名 (messages) -> str
        max_retries: 单步最大重试次数
    """

    name: str = "plan_execute_agent"

    def __init__(
        self,
        llm_fn: Optional[Callable] = None,
        max_retries: int = 2,
    ):
        self.llm_fn = llm_fn or _default_llm
        self.max_retries = max_retries

    # ---- Plan 阶段 ----

    def plan(self, goal: str, **kwargs) -> list[dict]:
        """用 LLM 生成执行计划

        提示模型输出结构化步骤列表（JSON 格式）。
        返回 (steps, raw_response) 元组。
        """
        constraints = kwargs.get("constraints", "")
        constraints_text = f"\n约束条件：{constraints}" if constraints else ""

        prompt = (
            "你是一个任务规划专家。请将以下目标分解为 3~6 个可执行的步骤。\n"
            "每个步骤用 JSON 格式表示：\n"
            "- step_id: 数字序号\n"
            "- description: 清晰描述该步骤要做什么\n"
            "- depends_on: 依赖的上一步 id 列表（空列表表示无依赖）\n"
            "- expected_output: 该步骤预期的输出\n"
            f"目标：{goal}{constraints_text}\n\n"
            "输出格式：\n"
            '[\n'
            '  {"step_id": 1, "description": "...", "depends_on": [], "expected_output": "..."},\n'
            '  ...\n'
            ']'
        )

        raw_response = self.llm_fn([{"role": "user", "content": prompt}])
        steps = self._parse_json_steps(raw_response, goal)
        return steps, raw_response

    def _parse_json_steps(self, text: str, goal: str = "") -> list[dict]:
        """从 LLM 回复中解析 JSON 步骤列表

        优先处理 markdown 代码块包裹的 JSON，然后尝试裸 JSON。
        都失败则返回包含目标信息的默认步骤。
        """
        # 去掉 markdown 代码块标记 ```json ... ```
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()

        # 尝试匹配 JSON 数组
        json_match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except (json.JSONDecodeError, TypeError):
                pass

        # 回退：生成包含目标信息的默认计划
        goal_text = goal[:40] if goal else ""
        return [
            {"step_id": 1, "description": f"分析目标「{goal_text}」，明确需求和约束条件", "depends_on": [], "expected_output": "需求分析"},
            {"step_id": 2, "description": f"收集与「{goal_text}」相关的资料和信息", "depends_on": [1], "expected_output": "资料汇总"},
            {"step_id": 3, "description": f"针对「{goal_text}」执行核心任务", "depends_on": [2], "expected_output": "执行结果"},
        ]

    # ---- Execute 阶段 ----

    def execute_step(self, step: dict, context: Optional[dict[str, Any]] = None) -> dict:
        """用 LLM 执行单个步骤

        通过约束 prompt 让 LLM 输出简洁的实质性内容。
        """
        context = context or {}
        step_id = step["step_id"]
        description = step["description"]

        # 收集前置步骤输出（取末尾部分）
        dep_outputs = []
        for dep_id in step.get("depends_on", []):
            out = context.get(f"step_{dep_id}_output")
            if out:
                dep_outputs.append(f"  步骤 {dep_id} 输出：{out[:150]}")

        deps_text = "\n".join(dep_outputs) if dep_outputs else "  无前置依赖"

        goal = context.get("_goal", "")
        system_prompt = "你是一个任务执行助手。请直接输出结果，不要输出过程描述、不要客气、不要重复题目。50字以内。"
        user_prompt = (
            f"目标：{goal}\n"
            f"步骤 {step_id}：{description}\n"
            f"依赖输入：{deps_text}"
        )

        raw_response = ""
        for attempt in range(self.max_retries + 1):
            raw_response = self.llm_fn([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
            if raw_response.strip():
                return {
                    "step_id": step_id,
                    "status": "completed",
                    "output": raw_response.strip()[:300],
                    "raw_output": raw_response.strip(),
                    "context_updates": {},
                }

        return {
            "step_id": step_id,
            "status": "failed",
            "output": f"步骤 {step_id} 在 {self.max_retries} 次重试后仍失败",
            "raw_output": raw_response,
            "context_updates": {},
        }

    # ---- 重规划 ----

    def replan(
        self,
        original_goal: str,
        steps: list[dict],
        completed: list[dict],
        failed_step: dict,
        context: dict[str, Any],
    ) -> list[dict]:
        """失败时用 LLM 重新规划剩余步骤"""
        completed_ids = [s["step_id"] for s in completed]
        remaining = [s for s in steps if s["step_id"] not in completed_ids]

        prompt = (
            f"原始目标：{original_goal}\n"
            f"已完成的步骤：{completed_ids}\n"
            f"失败的步骤：{failed_step['step_id']} - {failed_step.get('description', '')}\n"
            f"原计划剩余步骤：{json.dumps(remaining, ensure_ascii=False)}\n\n"
            "请基于失败原因调整剩余计划。输出 JSON 步骤列表。"
        )

        response = self.llm_fn([{"role": "user", "content": prompt}])
        new_steps = self._parse_json_steps(response, original_goal)

        # 重新编号
        for i, s in enumerate(new_steps):
            s["step_id"] = i + 1
        return new_steps

    def run(self, goal: str, verbose: bool = False, **kwargs) -> dict:
        """完整执行 Plan-and-Execute 流程

        Args:
            goal: 目标描述
            verbose: 是否打印执行过程
            **kwargs: 传递给 plan() 的额外参数

        Returns:
            dict: 包含 plan, results, final_output
        """
        if verbose:
            print(f"📋 Plan 阶段：规划目标「{goal}」")
        steps, plan_raw = self.plan(goal, **kwargs)
        if verbose:
            print(f"   生成了 {len(steps)} 个步骤")
            print(f"\n  ── LLM 规划过程 ──")
            print(f"  {plan_raw[:500]}")
            print(f"  ────────────────")

        context: dict[str, Any] = {"_goal": goal}
        completed: list[dict] = []
        step_index = 0

        while step_index < len(steps):
            step = steps[step_index]
            if verbose:
                print(f"\n  ▶ Step {step['step_id']}: {step['description'][:50]}...")

            result = self.execute_step(step, context)

            if verbose:
                print(f"    状态：{result['status']}")
                raw = result.get("raw_output", "")
                if raw:
                    print(f"    ── LLM 执行输出 ──")
                    print(f"    {raw[:200]}")
                    print(f"    ────────────────")

            if result["status"] == "completed":
                completed.append(result)
                context[f"step_{step['step_id']}_output"] = result["output"]
                context.update(result.get("context_updates", {}))
                step_index += 1
            else:
                if verbose:
                    print(f"    ⚠ 步骤失败，重新规划...")
                steps = self.replan(goal, steps, completed, step, context)
                if verbose:
                    print(f"    调整后剩余 {len(steps) - step_index} 个步骤")

        # 汇总
        final_output = "\n".join(r["output"] for r in completed)

        if verbose:
            print(f"\n✅ 全部完成")

        return {
            "plan": steps,
            "plan_raw": plan_raw,
            "results": completed,
            "final_output": final_output,
            "total_steps": len(completed),
        }
