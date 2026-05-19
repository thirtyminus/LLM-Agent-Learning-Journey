#!/usr/bin/env python3
"""
planner/_mock_llm.py — 模拟 LLM 回复（无 API Key 时的回退方案）

提供 PlanExecuteAgent 和 TravelPlanner 的模拟回复。
"""

import json


# ============================================================
# PlanExecuteAgent 模拟
# ============================================================

def mock_plan_execute_llm(messages: list[dict]) -> str:
    """模拟 PlanExecuteAgent 的 LLM 回复"""
    last_msg = messages[-1]["content"] if messages else ""

    # 步骤规划请求
    if "分解为 3~6 个可执行的步骤" in last_msg or "你是一个任务规划专家" in last_msg:
        return json.dumps(
            [
                {
                    "step_id": 1,
                    "description": "分析任务目标，明确输入输出和约束条件",
                    "depends_on": [],
                    "expected_output": "需求分析文档",
                },
                {
                    "step_id": 2,
                    "description": "收集执行任务所需的资料和信息",
                    "depends_on": [1],
                    "expected_output": "信息汇总",
                },
                {
                    "step_id": 3,
                    "description": "执行核心任务，生成初步结果",
                    "depends_on": [2],
                    "expected_output": "初步结果",
                },
                {
                    "step_id": 4,
                    "description": "审核和优化结果，确保质量",
                    "depends_on": [3],
                    "expected_output": "最终交付物",
                },
            ],
            ensure_ascii=False,
        )

    # 单步执行（格式：系统提示 + 用户提示）
    if "步骤 " in last_msg and "目标：" in last_msg:
        for line in last_msg.split("\n"):
            if line.startswith("步骤 "):
                # "步骤 1：xxx" → "xxx"
                desc = line.split("：", 1)[-1] if "：" in line else line
                return f"{desc[:50]}"
        return "步骤执行完毕"

    # 重规划请求
    if "调整剩余计划" in last_msg or "重新规划" in last_msg:
        return json.dumps(
            [
                {"step_id": 1, "description": "重新分析失败原因", "depends_on": []},
                {"step_id": 2, "description": "使用备选方案继续执行", "depends_on": [1]},
            ],
            ensure_ascii=False,
        )

    return "模拟 LLM 回复：收到你的消息，但我是一个模拟 LLM，无法提供实际回复。"


# ============================================================
# TravelPlanner 模拟
# ============================================================

def mock_travel_planner_llm(messages: list[dict]) -> str:
    """模拟 TravelPlanner 的 LLM 回复（生成行程单）"""
    last_msg = messages[-1]["content"] if messages else ""

    if "行程单" in last_msg:
        return (
            "📅 第1天：抵达，游览市区景点，品尝当地美食\n"
            "📅 第2天：主要景点深度游\n"
            "📅 第3天：自由活动+购物，返程\n"
            "💰 预算：交通30% 住宿35% 餐饮20% 门票10% 备用5%"
        )

    return "模拟 LLM 回复：正在处理你的旅行规划请求..."
