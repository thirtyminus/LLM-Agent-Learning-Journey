# 阶段二：上下文与记忆系统

> 让 LLM 记住该记住的，忘掉该忘掉的。  
> 滑动窗口、摘要压缩、向量检索、实体记忆 —— 四种策略从零实现。

`Python 3.10+` · `DeepSeek` · `MIT License`

---

## 一、为什么需要记忆系统？

大模型的上下文窗口虽然越来越大（128K、1M），但有两个核心问题没有解决：

1. **成本**：Token 越多，每次调用越贵，响应越慢
2. **精度**：长上下文中，关键信息容易被淹没，模型在"大海捞针"测试中仍然不稳定

记忆系统的目标很简单：**在有限的窗口里，保留最有价值的信息。**

---

## 二、四种记忆策略

### 1. 滑动窗口（Sliding Window）

**思路：** 只保留最近 N 轮对话，超出的一刀切掉。

```
对话: [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]
窗口大小 = 5
保留: [6] [7] [8] [9] [10]
```

**优点：** 实现简单、零开销  
**缺点：** 丢失早期关键信息  

**适用场景：** 闲聊、单轮问答、上下文关联性弱的任务。

### 2. 摘要压缩（Summary Memory）

**思路：** 当上下文过长时，把旧消息压缩成一段摘要，保留核心信息。

```
对话: [1] [2] [3] [4] [5] [6]
      ↓ 摘要
摘要: "用户询问了 A 问题，讨论了 B 方案，最终选择了 C"
保留: [摘要] [5] [6]
```

**优点：** 比滑动窗口保留更多高层语义  
**缺点：** 摘要本身可能丢失细节，且每次压缩需要额外 LLM 调用  

**适用场景：** 长文档对话、多轮咨询、需要保留上下文脉络的任务。

### 3. 向量检索（Vector Memory）

**思路：** 把每条消息转为向量（embedding），存储到向量库。每次对话时检索最相关的几条历史。

```
提问 → 向量化 → 向量库检索 → 找到 Top-3 相关历史 → 拼接后发给模型
```

**优点：** 不依赖顺序，能跨越多轮找到相关历史  
**缺点：** 需要 embedding 模型和向量存储，架构更重  

**适用场景：** 知识库问答、历史信息需要跨越多轮引用的任务。

### 4. 实体记忆（Entity Memory）

**思路：** 从对话中提取结构化信息（人物、时间、偏好、事实），存储为键值对或知识图谱。

```
对话: "我住在北京，喜欢喝拿铁"
      ↓ 提取
实体: { location: "北京", preference: "拿铁" }
```

**优点：** 信息高度结构化，检索精准  
**缺点：** 依赖信息抽取质量，复杂关系建模困难  

**适用场景：** 个性化助手、推荐系统、需要长期记忆用户偏好的任务。

---

## 三、代码结构

```text
phase2-context-memory/
├── README.md                     # 本文件
├── memory_system/                # 四种记忆策略实现
│   ├── base.py                   # 抽象基类
│   ├── sliding_window.py         # 滑动窗口
│   ├── summary_memory.py         # 摘要压缩
│   ├── vector_memory.py          # 向量检索
│   ├── entity_memory.py          # 实体记忆
│   └── requirements.txt          # 依赖
└── experiments/                  # 对比实验
    └── compare_strategies.py     # 四种策略效果对比
```

---

## 四、记忆策略实现

### 抽象基类

所有记忆策略继承同一个接口，方便替换和对比：

```python
class MemoryBase(ABC):
    @abstractmethod
    def add(self, role: str, content: str):
        """添加一条消息到记忆"""
        pass

    @abstractmethod
    def get_context(self, query: str = "") -> list:
        """获取当前上下文中应包含的消息列表"""
        pass
```

### 滑动窗口

```python
class SlidingWindow(MemoryBase):
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.messages: list[dict] = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.window_size:
            self.messages = self.messages[-self.window_size:]

    def get_context(self, query: str = "") -> list:
        return self.messages
```

### 摘要压缩

每次添加消息时，如果消息数超过阈值，用 LLM 把前半部分压缩为摘要。

```python
class SummaryMemory(MemoryBase):
    def __init__(self, max_messages: int = 6):
        self.max_messages = max_messages
        self.messages: list[dict] = []
        self.summary: str = ""

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) >= self.max_messages * 2:
            self._summarize()

    def _summarize(self):
        """调用 LLM 压缩前半部分为摘要"""
        to_summarize = self.messages[:len(self.messages)//2]
        # ... 调用 LLM 生成摘要 ...
        self.summary = summary_text
        self.messages = self.messages[len(self.messages)//2:]

    def get_context(self, query: str = "") -> list:
        if self.summary:
            return [{"role": "system", "content": f"对话摘要：{self.summary}"}] + self.messages
        return self.messages
```

### 向量检索

使用 embedding 将消息转为向量，查询时用余弦相似度检索 Top-K。

```python
class VectorMemory(MemoryBase):
    def __init__(self, embedding_fn, top_k: int = 5):
        self.embedding_fn = embedding_fn
        self.top_k = top_k
        self.messages: list[dict] = []
        self.vectors: list[list[float]] = []

    def add(self, role: str, content: str):
        vec = self.embedding_fn(content)
        self.messages.append({"role": role, "content": content})
        self.vectors.append(vec)

    def get_context(self, query: str = "") -> list:
        if not query:
            return self.messages[-self.top_k:]
        q_vec = self.embedding_fn(query)
        scores = [cosine_similarity(q_vec, v) for v in self.vectors]
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:self.top_k]
        return [self.messages[i] for i in sorted(top_indices)]
```

### 实体记忆

从消息中提取命名实体，维护一个结构化知识库。

```python
class EntityMemory(MemoryBase):
    def __init__(self, extract_fn):
        self.extract_fn = extract_fn
        self.entities: dict = {}
        self.messages: list[dict] = []

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        extracted = self.extract_fn(content)
        for key, value in extracted.items():
            self.entities[key] = value

    def get_context(self, query: str = "") -> list:
        if not self.entities:
            return self.messages[-5:]
        entity_summary = "已知用户信息：\n" + "\n".join(
            f"- {k}: {v}" for k, v in self.entities.items()
        )
        return [
            {"role": "system", "content": entity_summary},
            *self.messages[-5:],
        ]
```

---

## 五、安装与使用

```bash
cd phase2-context-memory
python3 -m venv .venv
source .venv/bin/activate
pip install -r memory_system/requirements.txt

# 运行对比实验
python3 experiments/compare_strategies.py
```

---

## 六、实验对比

| 策略 | 召回率 | 实现成本 | 适用场景 |
|------|--------|---------|---------|
| 滑动窗口 | 低 | 极低 | 闲聊、无关轮次可丢 |
| 摘要压缩 | 中 | 中 | 长文档、咨询对话 |
| 向量检索 | 高 | 高 | 知识库、需要跨轮引用 |
| 实体记忆 | 中 | 中 | 个性化、用户画像 |

---

## 七、实践路线

1. **跑通滑动窗口** — 理解最基础的上下文裁剪
2. **加入摘要压缩** — 感受 LLM 自己"总结自己"的效果
3. **实现向量检索** — 用 embedding 实现语义搜索
4. **添加实体记忆** — 让模型记住用户的偏好和事实
5. **综合对比** — 运行 `compare_strategies.py` 看四种策略的实际表现

---

## 八、常见陷阱

- **滑动窗口切太短**：关键信息被丢掉，模型"失忆"
- **摘要过于抽象**：频繁压缩导致细节丢失，生成的摘要越来越空洞
- **向量检索维度灾难**：短文本向量区分度低，返回不相关结果
- **实体记忆出现矛盾**：用户改变想法后，旧实体信息干扰新判断
- **混合策略权重失衡**：多种记忆拼在一起时上下文暴涨，反而更贵

---

## 九、配套资源

- 完整代码：https://github.com/thirtyminus/LLM-Agent-Learning-Journey
- OpenAI Embeddings：https://platform.openai.com/docs/guides/embeddings
- Sentence-Transformers：https://www.sbert.net/

> 下一阶段预告：工具使用与 Agent 循环 —— 从零实现 ReAct 模式，让模型学会调用工具。
>
> 如果本文对你有帮助，欢迎 Star 仓库。
