#!/usr/bin/env python3
"""
experiments/compare_strategies.py — 四种记忆策略对比实验

模拟一段长对话，分别用四种策略处理，输出各策略的上下文效果对比。

用法：
  cd phase2-context-memory
  python3 experiments/compare_strategies.py
"""

import sys
import os

# 将项目根目录加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memory_system import (
    SlidingWindow,
    SummaryMemory,
    VectorMemory,
    EntityMemory,
    cosine_similarity,
)


# ============================================================
# 辅助函数：模拟 embedding
# ============================================================

def mock_embedding(text: str) -> list[float]:
    """模拟 embedding：基于文本中关键词的简单哈希向量"""
    words = set(text.lower().split())
    # 预定义关键词到维度的映射（仅用于演示）
    keywords = ["北京", "上海", "咖啡", "茶", "喜欢", "推荐", "价格", "位置",
                 "学习", "编程", "Python", "项目", "工作", "面试", "考试", "复习",
                 "天气", "旅游", "美食", "电影"]
    vec = [0.0] * len(keywords)
    for i, kw in enumerate(keywords):
        if kw in words or any(kw in w for w in words):
            vec[i] = 1.0
    # 归一化
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def mock_entity_extract(text: str) -> dict[str, str]:
    """模拟实体提取：基于关键词的简单匹配"""
    entities = {}
    if "北京" in text:
        entities["location"] = "北京"
    if "上海" in text:
        entities["location"] = "上海"
    if "咖啡" in text:
        entities["preference"] = "咖啡"
    if "茶" in text:
        entities["preference"] = "茶"
    if "编程" in text or "Python" in text:
        entities["interest"] = "编程"
    if "工作" in text:
        entities["status"] = "在职"
    return entities


# ============================================================
# 模拟对话
# ============================================================

SAMPLE_CONVERSATION = [
    ("user", "你好，我想了解一下北京有什么好玩的地方"),
    ("assistant", "北京有很多景点，比如故宫、长城、颐和园等。"),
    ("user", "谢谢，我下个月要去北京出差，顺便玩几天"),
    ("assistant", "建议提前订票，旺季人多。需要我推荐住宿区域吗？"),
    ("user", "好的，推荐一下，我喜欢喝咖啡，附近最好有咖啡店"),
    ("assistant", "三里屯和国贸区域咖啡店密集，适合你。"),
    ("user", "另外我也在学 Python 编程，有什么推荐的学习资源吗？"),
    ("assistant", "推荐 Python 官方文档、LeetCode 刷题，还有这个仓库本身。"),
    ("user", "我目前在找工作，想转行做 AI 工程师"),
    ("assistant", "建议从机器学习基础学起，多做项目积累经验。"),
    ("user", "对了，我之前提到的北京出差，你能帮我规划一下行程吗？"),
    ("assistant", "当然，你的出差时间是几天？主要去哪个区域？"),
    ("user", "三天，主要在朝阳区，想抽一天去故宫"),
    ("assistant", "Day1: 朝阳区工作；Day2: 故宫+景山公园；Day3: 灵活安排。"),
    ("user", "谢谢！另外给我推荐一本 Python 数据分析的书吧"),
    ("assistant", "推荐《利用Python进行数据分析》（Wes McKinney 著）。"),
]


# ============================================================
# 运行对比
# ============================================================

def run_comparison():
    print("=" * 65)
    print("  记忆策略对比实验")
    print("=" * 65)
    print(f"\n模拟对话共 {len(SAMPLE_CONVERSATION)} 轮\n")

    # ---------- 1. 滑动窗口 ----------
    print("-" * 65)
    print("  1. 滑动窗口（SlidingWindow） — 窗口大小=6")
    print("-" * 65)
    sw = SlidingWindow(window_size=6)
    for role, content in SAMPLE_CONVERSATION:
        sw.add(role, content)

    ctx = sw.get_context()
    print(f"  保留消息数：{len(ctx)}")
    for msg in ctx:
        print(f"  [{msg['role']}] {msg['content'][:50]}…")
    print()

    # ---------- 2. 摘要压缩 ----------
    print("-" * 65)
    print("  2. 摘要压缩（SummaryMemory） — 阈值=6")
    print("-" * 65)
    sm = SummaryMemory(max_messages=6)
    for role, content in SAMPLE_CONVERSATION:
        sm.add(role, content)

    ctx = sm.get_context()
    summary_msg = [m for m in ctx if m["role"] == "system" and "对话摘要" in m["content"]]
    recent_msgs = [m for m in ctx if m["role"] != "system"]
    if summary_msg:
        print(f"  摘要：{summary_msg[0]['content'][:100]}…")
    print(f"  最近消息数：{len(recent_msgs)}")
    for msg in recent_msgs:
        print(f"  [{msg['role']}] {msg['content'][:50]}…")
    print()

    # ---------- 3. 向量检索 ----------
    print("-" * 65)
    print("  3. 向量检索（VectorMemory） — top_k=3")
    print("-" * 65)
    vm = VectorMemory(embedding_fn=mock_embedding, top_k=3)

    # 先添加所有消息
    for role, content in SAMPLE_CONVERSATION:
        vm.add(role, content)

    # 用最后一条消息作为查询
    last_query = SAMPLE_CONVERSATION[-1][1]
    ctx = vm.get_context(query=last_query)
    print(f"  查询：{last_query[:50]}…")
    print(f"  检索到 {len(ctx)} 条相关历史：")
    for msg in ctx:
        print(f"  [{msg['role']}] {msg['content'][:50]}…")

    # 用第一条消息（北京话题）作为查询
    first_query = SAMPLE_CONVERSATION[0][1]
    ctx2 = vm.get_context(query=first_query)
    print(f"\n  查询：{first_query[:50]}…")
    print(f"  检索到 {len(ctx2)} 条相关历史：")
    for msg in ctx2:
        print(f"  [{msg['role']}] {msg['content'][:50]}…")
    print()

    # ---------- 4. 实体记忆 ----------
    print("-" * 65)
    print("  4. 实体记忆（EntityMemory）")
    print("-" * 65)
    em = EntityMemory(extract_fn=mock_entity_extract)
    for role, content in SAMPLE_CONVERSATION:
        em.add(role, content)

    ctx = em.get_context()
    print(f"  提取到的实体：")
    for msg in ctx:
        if msg["role"] == "system":
            print(f"  {msg['content']}")
    print(f"  最近消息数：{len([m for m in ctx if m['role'] != 'system'])}")

    # ---------- 总结 ----------
    print()
    print("=" * 65)
    print("  对比总结")
    print("=" * 65)
    print("""
  场景说明：用户先聊北京出差 → 切换谈 Python 学习 → 切换谈找工作
           → 回头又问北京出差

  滑动窗口：用户问"北京出差行程"时，最初聊北京的信息已被切掉
  摘要压缩：保留了摘要（北京出差+Python学习），但细节可能丢失
  向量检索：用语义相似度找回早期的北京相关历史，跨越多轮
  实体记忆：记住了 location=北京, preference=咖啡, interest=编程
    """)

    print("💡 提示：替换 mock_embedding 和 mock_entity_extract 为真实 API")
    print("   即可在生产环境中使用。")


if __name__ == "__main__":
    run_comparison()
