#!/usr/bin/env python3
"""
react_agent/prompts.py — ReAct System Prompt 模板

定义 Agent 的行为规则和工具调用格式。
"""

import sys
import os

# 将项目根目录加入 path（方便直接 import tools）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import BaseTool


def build_system_prompt(tools: list[BaseTool]) -> str:
    """根据工具列表生成 ReAct System Prompt"""

    tool_descriptions = "\n".join(f"- {t.to_prompt_block()}" for t in tools)

    return f"""你是一个智能助手，可以通过调用工具来回答问题。

可用的工具：

{tool_descriptions}

请严格按以下格式回复：

Thought: 你现在在想什么（分析当前状态，决定下一步）
Action: 工具名称
Action Input: {{"参数名": "参数值"}}

当工具返回结果后，继续分析：

Thought: 根据工具结果，你现在知道了什么
Action: 另一个工具（如需继续调用）
或：
Final Answer: 对用户的最终回答

注意事项：
1. 一次只调用一个工具，等待结果后再决定下一步
2. 如果工具返回错误信息，尝试换一个方式或告诉用户
3. 如果已经足够回答用户，直接给出 Final Answer
4. Action Input 必须是合法的 JSON 格式
5. 不要编造不存在的工具"""


# 默认 ReAct 提示词（不带工具列表，由 agent.py 动态生成）
DEFAULT_SYSTEM_PROMPT = "你是一个智能助手，可以通过调用工具来回答问题。"
