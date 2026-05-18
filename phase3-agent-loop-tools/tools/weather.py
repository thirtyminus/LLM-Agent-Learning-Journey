#!/usr/bin/env python3
"""
tools/weather.py — 天气查询工具

模拟查询指定城市的当前天气。
实际使用时替换为真实天气 API。
"""

from .tool_base import BaseTool


class GetWeather(BaseTool):
    name = "get_weather"
    description = "查询指定城市的实时天气。输入城市名称（如 北京），返回温度、天气状况。"

    def run(self, city: str) -> str:
        # 模拟天气数据
        data = {
            "北京": "15°C，晴，风力3级，空气质量：良",
            "上海": "22°C，多云，风力2级，空气质量：优",
            "广州": "28°C，多云，风力3级，空气质量：良",
            "深圳": "26°C，阵雨，风力4级，空气质量：优",
            "杭州": "18°C，阴，风力2级，空气质量：良",
            "成都": "20°C，多云，风力1级，空气质量：良",
            "武汉": "25°C，多云转阴，风力3级，空气质量：良",
            "南京": "19°C，小雨，风力2级，空气质量：优",
        }
        return data.get(city, f"暂未收录 {city} 的天气数据")
