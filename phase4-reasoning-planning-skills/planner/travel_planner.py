#!/usr/bin/env python3
"""
planner/travel_planner.py — 旅行规划示例

基于 Plan-and-Execute 模式，结合时间、预算、偏好等约束，
自动生成旅行攻略。

演示了 Chain-of-Thought 推理在规划类任务中的应用。
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
    from ._mock_llm import mock_travel_planner_llm
    return mock_travel_planner_llm(messages)


# 城市知识库（模拟）
CITY_DB = {
    "北京": {
        "机场": "北京首都国际机场（PEK）/ 北京大兴国际机场（PKX）",
        "推荐景点": ["故宫", "长城", "颐和园", "天坛", "南锣鼓巷"],
        "推荐美食": ["北京烤鸭", "涮羊肉", "炸酱面", "豆汁儿"],
        "最佳季节": "春秋（3-5月、9-11月）",
        "建议天数": "3-5天",
    },
    "上海": {
        "机场": "上海浦东国际机场（PVG）/ 上海虹桥国际机场（SHA）",
        "推荐景点": ["外滩", "迪士尼乐园", "东方明珠", "武康路", "豫园"],
        "推荐美食": ["小笼包", "生煎", "本帮菜", "蟹粉豆腐"],
        "最佳季节": "春秋（3-5月、10-11月）",
        "建议天数": "3-4天",
    },
    "成都": {
        "机场": "成都天府国际机场（TFU）/ 成都双流国际机场（CTU）",
        "推荐景点": ["大熊猫基地", "宽窄巷子", "锦里", "青城山", "都江堰"],
        "推荐美食": ["火锅", "串串香", "担担面", "夫妻肺片"],
        "最佳季节": "春秋（3-6月、9-11月）",
        "建议天数": "3-5天",
    },
    "杭州": {
        "机场": "杭州萧山国际机场（HGH）",
        "推荐景点": ["西湖", "灵隐寺", "西溪湿地", "宋城", "九溪烟树"],
        "推荐美食": ["西湖醋鱼", "龙井虾仁", "东坡肉", "葱包桧"],
        "最佳季节": "3-5月、9-11月",
        "建议天数": "2-3天",
    },
}


class TravelPlanner(BasePlanner):
    """旅行规划器

    根据目的地、天数、预算、偏好生成旅行攻略。
    使用 Chain-of-Thought 风格的规划过程。

    Args:
        llm_fn: LLM 调用函数
        city_db: 城市知识库（字典），默认使用内置数据
    """

    name: str = "travel_planner"

    def __init__(
        self,
        llm_fn: Optional[Callable] = None,
        city_db: Optional[dict] = None,
    ):
        self.llm_fn = llm_fn or _default_llm
        self.city_db = city_db or CITY_DB

    def plan(self, goal: str, **kwargs) -> list[dict]:
        """生成旅行计划

        从 goal 中解析目的地、天数、预算等信息。
        用 Chain-of-Thought 步骤确保规划质量。

        Args:
            goal: 如 "去北京玩3天，预算5000"
            **kwargs: 可传入 constraints, preferences 等

        Returns:
            list[dict]: 旅行规划的步骤
        """
        city = kwargs.get("city") or self._extract_city(goal)
        days = kwargs.get("days") or self._extract_days(goal)
        budget = kwargs.get("budget") or self._extract_budget(goal)
        preferences = kwargs.get("preferences", "")

        city_info = self.city_db.get(city, {})
        if not city_info:
            return [{"step_id": 1, "description": f"暂未收录 {city} 的旅行数据", "depends_on": []}]

        # Chain-of-Thought: 先分析约束，再逐步生成
        steps = [
            {
                "step_id": 1,
                "description": (
                    f"【分析约束】用户要去 {city}，{days}天，预算{budget}元。\n"
                    f"  城市信息：{city_info['推荐景点'][:3]}...\n"
                    f"  偏好：{preferences or '无特殊偏好'}\n"
                    f"  结论：{days}天建议安排 {min(days, len(city_info['推荐景点']))} 个景点"
                ),
                "depends_on": [],
            },
            {
                "step_id": 2,
                "description": f"规划行程框架（每日分区）：\n"
                    f"  第1天：抵达 + {city_info['推荐景点'][0]}\n"
                    f"  第2天：{city_info['推荐景点'][1]} + {city_info['推荐景点'][2] if len(city_info['推荐景点']) > 2 else '市区游览'}\n"
                    f"  第{days}天：返程",
                "depends_on": [1],
            },
            {
                "step_id": 3,
                "description": f"预算分配：\n"
                    f"  交通：{int(budget) * 30 // 100}元\n"
                    f"  住宿：{int(budget) * 35 // 100}元\n"
                    f"  餐饮：{int(budget) * 20 // 100}元\n"
                    f"  门票：{int(budget) * 10 // 100}元\n"
                    f"  备用：{int(budget) * 5 // 100}元",
                "depends_on": [2],
            },
            {
                "step_id": 4,
                "description": f"生成最终行程单",
                "depends_on": [3],
            },
        ]
        return steps

    def execute_step(self, step: dict, context: Optional[dict[str, Any]] = None) -> dict:
        """执行单步，用 LLM 或规则生成详细内容"""
        context = context or {}
        step_id = step["step_id"]
        description = step["description"]

        llm_fn = context.get("llm_fn", self.llm_fn)

        if step_id < 4:
            # 前几步直接用已有分析结果
            return {
                "step_id": step_id,
                "status": "completed",
                "output": description,
                "context_updates": {},
            }

        # 第4步：用 LLM 生成完整的行程单
        goal = context.get("goal", "")
        system_prompt = (
            "你是一个旅行规划专家。请直接输出行程单，不要输出过程描述，不要客气。"
            "用简洁的列表格式，包含每日安排、推荐餐厅和预算。"
        )
        user_prompt = (
            f"生成{context.get('city','目的地')}的行程单。\n"
            f"天数：{context.get('days',3)}天\n"
            f"预算：{context.get('budget',3000)}元\n"
            f"背景信息：{context.get('step_1_output', '')[:200]}"
        )
        response = llm_fn([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        return {
            "step_id": step_id,
            "status": "completed",
            "output": response.strip() or description,
            "context_updates": {},
        }

    # ---- 辅助方法 ----

    def _extract_city(self, text: str) -> str:
        for city in self.city_db:
            if city in text:
                return city
        return "北京"

    def _extract_days(self, text: str) -> int:
        match = re.search(r"(\d+)\s*天", text)
        return int(match.group(1)) if match else 3

    def _extract_budget(self, text: str) -> int:
        match = re.search(r"预算(\d+)", text)
        if not match:
            match = re.search(r"(\d+)\s*元", text)
        return int(match.group(1)) if match else 3000

    def run(self, goal: str, **kwargs) -> dict:
        """完整执行旅行规划

        Args:
            goal: 用户输入，如 "去成都玩4天，预算6000"
            **kwargs: 可覆盖 city, days, budget, preferences

        Returns:
            dict: 包含 plan, results, itinerary
        """
        context = dict(kwargs)

        city = self._extract_city(goal)
        days = self._extract_days(goal)
        budget = self._extract_budget(goal)

        print(f"🗺️  旅行规划：{city} {days}天 预算{budget}元")
        print(f"   {'='*40}")

        steps = self.plan(goal, **context)
        results = []
        context["city"] = city
        context["days"] = days
        context["budget"] = budget

        for step in steps:
            result = self.execute_step(step, context)
            results.append(result)
            context[f"step_{step['step_id']}_output"] = result["output"]

        itinerary = results[-1]["output"] if results else "规划失败"

        print(f"\n📄 生成行程单（{len(steps)} 步完成）")
        print(f"{'='*50}")
        print(itinerary[:500])

        return {
            "plan": steps,
            "results": results,
            "itinerary": itinerary,
            "city": city,
            "days": days,
            "budget": budget,
        }
