#!/usr/bin/env python3
"""
playground/chat.py — 交互式 CLI 聊天客户端（默认使用 DeepSeek API）

用途：
  体验 LLM API 调用、参数控制、流式输出、多轮对话。
  通过调参和换提示词，直观感受不同设置对输出质量的影响。

支持：
  - DeepSeek API（兼容 OpenAI 格式，默认）
  - OpenAI / Anthropic API（可选）
  - 流式输出（streaming）
  - temperature / top_p / max_tokens / frequency_penalty 参数控制
  - System Prompt 设定（支持从文件加载）
  - 多轮对话上下文
  - 对话历史保存/加载

用法：
  # 使用 System Prompt
  python chat.py --system "你是一名编程导师"

  # 单次提问（非交互模式）
  python chat.py --prompt "什么是提示工程？"

  # 从文件加载 System Prompt
  python chat.py --system-file ../prompts/prompt_templates.md

  # 调参
  python chat.py --temperature 0.8 --max-tokens 2048
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ============================================================
# 提供商适配器
# ============================================================
# 设计说明：
#   通过适配器模式统一 OpenAI 和 Anthropic 的 API 差异，
#   上层对话逻辑完全与厂商解耦。
#   后续添加新厂商只需新增一个适配器类。

class BaseAdapter:
    """适配器基类，定义统一的接口"""

    def __init__(self, model: str, temperature: float, top_p: float, max_tokens: int):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.client = self._build_client()

    def _build_client(self):
        raise NotImplementedError

    def chat_stream(self, messages: list):
        """返回一个迭代器，每次 yield 一个文本块"""
        raise NotImplementedError


class OpenAIAdapter(BaseAdapter):
    """OpenAI / 兼容 API 适配器"""

    def _build_client(self):
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL")
        if not api_key:
            print("错误：未设置 OPENAI_API_KEY 环境变量")
            sys.exit(1)
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs)

    def chat_stream(self, messages: list):
        """
        OpenAI 流式调用。

        关键设计：
        - stream=True 开启流式，每次 yield 一个 content chunk
        - 兼容 Azure OpenAI 和其他兼容服务商（通过 OPENAI_BASE_URL 指定）
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


class DeepSeekAdapter(BaseAdapter):
    """DeepSeek API 适配器（兼容 OpenAI 格式）"""

    DEEPSEEK_BASE_URL = "https://api.deepseek.com"

    def _build_client(self):
        from openai import OpenAI
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("错误：未设置 DEEPSEEK_API_KEY 环境变量")
            print("获取方式：https://platform.deepseek.com/api_keys")
            sys.exit(1)
        return OpenAI(api_key=api_key, base_url=self.DEEPSEEK_BASE_URL)

    def chat_stream(self, messages: list):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


class AnthropicAdapter(BaseAdapter):
    """Anthropic API 适配器"""

    def _build_client(self):
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("错误：未设置 ANTHROPIC_API_KEY 环境变量")
            sys.exit(1)
        return Anthropic(api_key=api_key)

    def chat_stream(self, messages: list):
        # Anthropic 的消息格式不同，需要转换
        system_msg = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        kwargs = dict(
            model=self.model,
            messages=anthropic_messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=True,
        )
        if system_msg:
            kwargs["system"] = system_msg

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text


# ============================================================
# 对话管理器
# ============================================================

class Conversation:
    """
    管理多轮对话的消息列表和上下文窗口。

    核心设计：
    - messages 列表累积所有历史消息
    - 每次调用时会裁剪到 max_context_messages 以内
    - 支持导出/导入对话历史（JSON 格式）
    """

    def __init__(self, system_prompt: str = "", max_context_messages: int = 20):
        self.messages: list[dict] = []
        self.max_context_messages = max_context_messages
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def get_context(self) -> list[dict]:
        """返回裁剪后的上下文消息列表"""
        # 始终保留 system prompt，然后取最近的 N 条
        if self.messages and self.messages[0]["role"] == "system":
            system = [self.messages[0]]
            rest = self.messages[1:]
        else:
            system = []
            rest = self.messages

        # 保留最近的 max_context_messages 条非 system 消息
        if len(rest) > self.max_context_messages:
            rest = rest[-self.max_context_messages:]

        return system + rest

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)
        print(f"\n💾 对话已保存到 {path}")

    def load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.messages = json.load(f)
        print(f"\n📂 已加载对话历史：{path} ({len(self.messages)} 条消息)")


# ============================================================
# 渲染器
# ============================================================

def print_header():
    """打印启动 banner"""
    print("=" * 60)
    print("  🧪 LLM Playground — 交互式聊天")
    print("  输入消息开始对话。支持多行输入：")
    print("  回车换行，空行（连续按两次回车）发送")
    print("  输入以下命令进行操作：")
    print("    /clear   — 清空对话历史")
    print("    /save    — 保存当前对话")
    print("    /load    — 加载历史对话")
    print("    /info    — 显示当前参数")
    print("    /exit    — 退出")
    print("=" * 60)


def print_info(provider: str, model: str, temperature: float, top_p: float, max_tokens: int, system_prompt: str):
    """显示当前配置信息"""
    print(f"\n📋 当前配置")
    print(f"   提供商:       {provider}")
    print(f"   模型:         {model}")
    print(f"   temperature:  {temperature}")
    print(f"   top_p:        {top_p}")
    print(f"   max_tokens:   {max_tokens}")
    print(f"   System Prompt:")
    for line in system_prompt.split("\n"):
        print(f"     │ {line}")
    print()


def print_streaming(text: str):
    """流式输出（直接写终端，不换行）"""
    print(text, end="", flush=True)


# ============================================================
# 主循环
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="LLM Playground — 交互式聊天客户端")
    # 提供商和模型
    parser.add_argument("--provider", default="deepseek", choices=["deepseek", "openai", "anthropic"],
                        help="API 提供商（默认: deepseek）")
    parser.add_argument("--model", default="",
                        help="模型名称（默认: deepseek-v4-flash / gpt-4o / claude-sonnet-4）")

    # 参数控制
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="温度参数 0.0~2.0（默认: 0.7）")
    parser.add_argument("--top-p", type=float, default=1.0,
                        help="核采样参数 0.0~1.0（默认: 1.0）")
    parser.add_argument("--max-tokens", type=int, default=4096,
                        help="最大输出 token 数（默认: 4096）")

    # System Prompt
    parser.add_argument("--system", type=str, default="",
                        help="System Prompt 内容")
    parser.add_argument("--system-file", type=str, default="",
                        help="从文件加载 System Prompt")

    # 单次提问
    parser.add_argument("--prompt", type=str, default="",
                        help="单条消息，发送后退出（非交互模式）")

    args = parser.parse_args()

    # --- 确定 System Prompt ---
    system_prompt = args.system
    if args.system_file:
        filepath = Path(args.system_file)
        if filepath.exists():
            system_prompt = filepath.read_text(encoding="utf-8").strip()
            print(f"📖 已加载 System Prompt 文件：{args.system_file}")
        else:
            print(f"⚠️  文件不存在：{args.system_file}，忽略")

    # --- 确定模型名称 ---
    default_models = {
        "deepseek": "deepseek-v4-flash",
        "openai": "gpt-4o",
        "anthropic": "claude-sonnet-4-20250514",
    }
    model = args.model or default_models.get(args.provider, "")

    # --- 初始化适配器 ---
    provider_map = {
        "deepseek": DeepSeekAdapter,
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
    }
    adapter_cls = provider_map[args.provider]
    adapter = adapter_cls(model, args.temperature, args.top_p, args.max_tokens)

    # --- 初始化对话 ---
    conv = Conversation(system_prompt=system_prompt)

    # --- 启动 ---
    print_header()
    print_info(args.provider, model, args.temperature, args.top_p,
               args.max_tokens, system_prompt)

    # ==================== 单次模式 ====================
    if args.prompt:
        conv.add_user_message(args.prompt)
        context = conv.get_context()
        print(f"\n🧑  {args.prompt}\n")
        print("🤖 ", end="", flush=True)
        try:
            for chunk in adapter.chat_stream(context):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"\n❌ API 调用失败：{e}")
        return

    # ==================== 交互模式 ====================
    if not system_prompt:
        print("💡 提示：可以用 --system 或 --system-file 设置 System Prompt")
        print()

    # ==================== 交互循环 ====================
    while True:
        # --- 多行输入：空行结束，命令取第一行 ---
        try:
            lines = []
            first = input(">>> ").strip()
            # 命令处理（仅检查第一行）
            if first == "/exit":
                print("👋 再见！")
                break
            elif first == "/clear":
                conv = Conversation(system_prompt=system_prompt)
                print("🧹 对话已清空")
                continue
            elif first == "/save":
                path = input("  保存路径（默认: chat_history.json）: ").strip()
                conv.save(path or "chat_history.json")
                continue
            elif first == "/load":
                path = input("  加载路径（默认: chat_history.json）: ").strip()
                if Path(path or "chat_history.json").exists():
                    conv.load(path or "chat_history.json")
                else:
                    print(f"⚠️  文件不存在：{path}")
                continue
            elif first == "/info":
                print_info(args.provider, model, args.temperature, args.top_p,
                           args.max_tokens, system_prompt)
                continue
            elif not first:
                continue

            lines.append(first)
            # 继续读后续行，空行结束
            while True:
                line = input("... ").rstrip("\n")
                if not line:
                    break
                lines.append(line)

            user_input = "\n".join(lines)
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        # --- 发送消息 ---
        conv.add_user_message(user_input)
        context = conv.get_context()

        # 显示 Assistant 前缀
        print("\n🤖 ", end="", flush=True)

        try:
            collected = ""
            for chunk in adapter.chat_stream(context):
                print(chunk, end="", flush=True)
                collected += chunk
            print()  # 换行
            conv.add_assistant_message(collected)
        except Exception as e:
            print(f"\n❌ API 调用失败：{e}")
            # 移除最后一个 user message，避免下次调用时重复
            if conv.messages and conv.messages[-1]["role"] == "user":
                conv.messages.pop()
        print()


if __name__ == "__main__":
    main()