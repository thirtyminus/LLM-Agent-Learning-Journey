#!/usr/bin/env python3
"""
tools/calculator.py — 计算器工具

让模型能执行精确的数学计算（LLM 直接算算术经常出错）。
用安全的 eval 执行数学表达式，不暴露危险的内置函数。
"""

from .tool_base import BaseTool


class Calculator(BaseTool):
    name = "calculator"
    description = "执行数学计算。输入一个数学表达式（如 2+3*4），返回数值结果。"

    def run(self, expression: str) -> str:
        try:
            # 安全执行：只允许数学运算，禁用内置函数
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"计算错误：{e}"
