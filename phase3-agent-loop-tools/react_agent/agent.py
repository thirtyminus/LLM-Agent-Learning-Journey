#!/usr/bin/env python3
"""
react_agent/agent.py — ReAct Agent 核心实现

从零实现的 ReAct（Reasoning + Acting）循环。
支持自定义工具集和 LLM 调用函数。

用法：
  python3 -m react_agent.agent
"""

import json
import os
import re
import sys
from typing import Callable, Optional

# 将项目根目录加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import BaseTool, Calculator, GetWeather, WebSearch
from .prompts import build_system_prompt


# ============================================================
# 默认 LLM 调用函数（使用 DeepSeek API）
# ============================================================

def _default_llm(messages: list[dict]) -> str:
    """默认 LLM 调用：使用 DeepSeek API（兼容 OpenAI SDK）"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return _mock_llm(messages)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content
    except ImportError:
        return _mock_llm(messages)


def _mock_llm(messages: list[dict]) -> str:
    """模拟 LLM 回复（无 API key 时的回退方案）

    支持完整的 ReAct 模拟循环：
    第一轮 → 返回 Thought + Action
    第二轮（收到 Observation 后）→ 返回 Final Answer
    """
    # 检查是否有 Observation（上一轮工具调用的结果）
    obs_messages = [
        m for m in messages
        if m["role"] == "system" and m["content"].startswith("Observation:")
    ]
    if obs_messages:
        obs = obs_messages[-1]["content"]
        result = obs.replace("Observation: ", "")
        return f"Thought: 工具返回了结果，现在可以回答用户了。\nFinal Answer: {result}"

    last_msg = messages[-1]["content"] if messages else ""

    # 简单规则匹配
    if "天气" in last_msg or "温度" in last_msg:
        import re as re_mod
        city_match = re_mod.search(r"北京|上海|深圳|杭州|成都", last_msg)
        city = city_match.group(0) if city_match else "北京"
        return (
            f"Thought: 用户想查询 {city} 的天气，我需要调用 get_weather 工具。\n"
            f"Action: get_weather\n"
            f"Action Input: {{\"city\": \"{city}\"}}"
        )
    elif "计算" in last_msg or any(c in last_msg for c in "+-*/"):
        expr_match = re.search(r"[\d\+\-\*/\(\)\s]+", last_msg)
        expr = expr_match.group(0).strip() if expr_match else "1+1"
        return (
            f"Thought: 用户需要做数学计算，调用 calculator 工具。\n"
            f"Action: calculator\n"
            f"Action Input: {{\"expression\": \"{expr}\"}}"
        )
    elif "搜索" in last_msg or "找" in last_msg or "查" in last_msg:
        return (
            f"Thought: 用户需要搜索信息，调用 web_search 工具。\n"
            f"Action: web_search\n"
            f"Action Input: {{\"query\": \"{last_msg[:20]}\"}}"
        )
    else:
        return f"Final Answer: 你好！我是 ReAct Agent，可以帮你查询天气、做数学计算或搜索信息。请问你需要什么帮助？"


# ============================================================
# ReAct Agent
# ============================================================

class ReActAgent:
    """ReAct Agent

    Args:
        tools: 工具列表
        llm_fn: LLM 调用函数，签名 (messages) -> str
        max_steps: 最大循环步数（默认 5）
    """

    def __init__(
        self,
        tools: Optional[list[BaseTool]] = None,
        llm_fn: Optional[Callable] = None,
        max_steps: int = 5,
    ):
        self.tools = {t.name: t for t in (tools or self._default_tools())}
        self.llm_fn = llm_fn or _default_llm
        self.max_steps = max_steps

        system_prompt = build_system_prompt(list(self.tools.values()))
        self.messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]

    @staticmethod
    def _default_tools() -> list[BaseTool]:
        return [Calculator(), GetWeather(), WebSearch()]

    def _parse_action(self, text: str) -> tuple[Optional[str], dict]:
        """从模型回复中解析 Action 和 Action Input"""
        text = text.strip()

        # 正则匹配: Action: xxx 后跟 Action Input: {...json...}
        action_match = re.search(r"Action:\s*(\w+)", text)
        input_match = re.search(
            r"Action Input:\s*(\{.*?\})", text, re.DOTALL
        )

        if action_match:
            action = action_match.group(1)
            action_input = {}
            if input_match:
                try:
                    action_input = json.loads(input_match.group(1))
                except json.JSONDecodeError:
                    action_input = {}
            return action, action_input

        return None, {}

    def run(self, user_input: str, verbose: bool = True) -> str:
        """执行 Agent 循环

        Args:
            user_input: 用户输入
            verbose: 是否打印思考过程

        Returns:
            str: Agent 的最终回答
        """
        self.messages.append({"role": "user", "content": user_input})

        for step in range(1, self.max_steps + 1):
            if verbose:
                print(f"\n[Step {step}] 调用 LLM...")

            response = self.llm_fn(self.messages)

            if verbose:
                print(f"\n{response}")

            # 检查是否给出了最终答案
            if "Final Answer:" in response:
                answer = response.split("Final Answer:")[-1].strip()
                if verbose:
                    print(f"\n✅ 最终答案：{answer}")
                return answer

            # 解析工具调用
            action, action_input = self._parse_action(response)

            if action is None:
                # 没有 Action，也没有 Final Answer，当作普通回复
                self.messages.append({"role": "assistant", "content": response})
                continue

            if action not in self.tools:
                result = f"错误：未知工具「{action}」，可用工具：{', '.join(self.tools.keys())}"
            else:
                try:
                    if verbose:
                        print(f"  🔧 调用工具: {action}({action_input})")
                    result = self.tools[action].run(**action_input)
                    if verbose:
                        print(f"  📦 工具结果: {result[:100]}...")
                except Exception as e:
                    result = f"工具调用失败：{e}"

            # 将模型的思考和工具结果加入上下文
            self.messages.append({"role": "assistant", "content": response})
            self.messages.append({
                "role": "system",
                "content": f"Observation: {result}",
            })

        return "达到最大步骤限制，无法完成请求。"

    def reset(self):
        """重置对话历史"""
        system_prompt = build_system_prompt(list(self.tools.values()))
        self.messages = [{"role": "system", "content": system_prompt}]


# ============================================================
# 交互式运行
# ============================================================

def interactive():
    """启动交互式 Agent"""
    print("=" * 60)
    print("  🤖 ReAct Agent — 交互模式")
    print("  可用工具：计算器 / 天气查询 / 搜索")
    print("  输入 /reset 重置对话，/exit 退出")
    print("=" * 60)

    agent = ReActAgent()

    while True:
        try:
            user_input = input("\n>>> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 再见！")
            break

        if not user_input:
            continue
        if user_input == "/exit":
            print("👋 再见！")
            break
        if user_input == "/reset":
            agent.reset()
            print("🧹 对话已重置")
            continue

        agent.run(user_input)


if __name__ == "__main__":
    interactive()
