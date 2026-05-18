# 阶段三：工具使用与 Agent 循环

> 让 LLM 从"只会说话"进化到"会动手"—— 从零实现 ReAct 模式，一步步解锁工具调用能力。

`Python 3.10+` · `DeepSeek` · `MIT License`

---

## 一、为什么要有 Agent 循环？

大模型本身是一个"大脑"——它能理解语言、推理、生成文本。但它有一个致命的局限：**它活在真空里**。

它不能查天气、不能算算术、不能搜索网页、不能读写文件。如果你问它"今天北京气温多少度？"，它要么尴尬地说不知道，要么编一个答案。

Agent 循环要解决的就是这个问题：**给模型装上手和眼睛**。

```
用户提问 → 模型思考（需要什么工具？）→ 调用工具 → 获取结果 → 模型继续推理 → 给出最终答案
```

这就是 ReAct（Reasoning + Acting）模式。

---

## 二、核心概念

### ReAct 循环

ReAct 的全称是 **Reasoning + Acting**，核心思路是让模型在每一轮中交替执行两个步骤：

1. **Thought（思考）**：分析当前状态，决定下一步需要什么
2. **Action（行动）**：调用一个工具，传入参数
3. **Observation（观察）**：获取工具返回的结果
4. **循环**：回到第 1 步，直到模型给出 Final Answer

```
Thought: 用户想知道天气，我需要查天气工具
Action: get_weather(city="北京")
Observation: 北京今天 15°C，晴
Thought: 现在可以回答了
Final Answer: 北京今天 15°C，天气晴朗。
```

### Function Calling（函数调用）

要让模型调用工具，需要做两件事：

1. **告诉模型有哪些工具可用** —— 在 System Prompt 中定义工具及其参数
2. **让模型输出结构化的工具调用指令** —— 用 JSON 格式输出函数名和参数

```json
{
  "action": "get_weather",
  "action_input": {"city": "北京"}
}
```

### 工具的定义

每个工具需要三个要素：

- **名称**：模型用来引用工具的标识
- **描述**：告诉模型这个工具是干什么的（决定模型会不会用它）
- **参数**：工具需要哪些输入，每个参数的类型和含义

---

## 三、代码结构

```text
phase3-agent-loop-tools/
├── README.md                    # 本文件
├── tools/                       # 工具定义
│   ├── __init__.py
│   ├── tool_base.py             # 工具基类
│   ├── calculator.py            # 计算器工具
│   ├── weather.py               # 天气查询工具（模拟）
│   └── search.py                # 搜索工具（模拟）
└── react_agent/                 # ReAct 循环实现
    ├── __init__.py
    ├── agent.py                 # 核心 Agent 循环
    ├── prompts.py               # ReAct System Prompt
    └── requirements.txt         # 依赖
```

---

## 四、工具实现

### 工具基类

所有工具继承自同一个基类，统一注册和调用接口：

```python
class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass
```

### 计算器工具

让模型能进行精确的数学计算（LLM 自己算算术经常出错）：

```python
class Calculator(BaseTool):
    name = "calculator"
    description = "执行数学计算。输入数学表达式，返回计算结果。"

    def run(self, expression: str) -> str:
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"计算错误：{e}"
```

### 天气查询工具（模拟）

```python
class GetWeather(BaseTool):
    name = "get_weather"
    description = "查询指定城市的当前天气。输入城市名称。"

    def run(self, city: str) -> str:
        data = {
            "北京": "15°C，晴，空气质量：良",
            "上海": "20°C，多云，空气质量：优",
        }
        return data.get(city, f"未找到 {city} 的天气数据")
```

### 搜索工具（模拟）

```python
class WebSearch(BaseTool):
    name = "web_search"
    description = "搜索互联网信息。输入查询词。"

    def run(self, query: str) -> str:
        results = {
            "Python": "Python 是一种广泛使用的高级编程语言。",
            "AI": "人工智能是计算机科学的一个分支。",
        }
        return results.get(query, f"未找到 {query} 的相关信息")
```

---

## 五、ReAct Agent 实现

核心循环逻辑：

```python
class ReActAgent:
    def __init__(self, tools: list[BaseTool], llm_fn, max_steps: int = 5):
        self.tools = {t.name: t for t in tools}
        self.llm_fn = llm_fn
        self.max_steps = max_steps
        self.messages = [{"role": "system", "content": REACT_SYSTEM_PROMPT}]

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for step in range(self.max_steps):
            response = self.llm_fn(self.messages)

            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()

            action, action_input = self._parse_action(response)

            if action in self.tools:
                result = self.tools[action].run(**action_input)
            else:
                result = f"错误：未知工具 {action}"

            self.messages.append({"role": "assistant", "content": response})
            self.messages.append({"role": "system", "content": f"Observation: {result}"})

        return "达到最大步骤限制。"
```

---

## 六、安装与使用

```bash
cd phase3-agent-loop-tools
python3 -m venv .venv
source .venv/bin/activate
pip install -r react_agent/requirements.txt

# 交互式 Agent
python3 -m react_agent.agent
```

---

## 七、实践路线

1. **理解 ReAct 模式** — 读通 prompts.py 中的 System Prompt
2. **跑通基础 Agent** — 用内置工具（计算器/天气/搜索）测试循环
3. **自己写一个工具** — 按照 BaseTool 接口实现自定义工具
4. **多步推理** — 给一个需要连续调用多个工具的任务
5. **增加错误处理** — 工具调用失败时自动重试
6. **接入真实 API** — 把模拟工具换成真实 API

---

## 八、常见陷阱

- **工具描述写得太模糊**：模型不知道什么时候该用
- **Action 格式不匹配**：模型输出的 JSON 解析失败，需要 prompt 和解析都做好容错
- **循环过深**：设 max_steps 上限防止死循环
- **工具结果太长**：撑爆上下文，需要截断或摘要
- **幻觉工具调用**：模型编造不存在的工具，需要做校验

---

## 九、配套资源

- 完整代码：https://github.com/thirtyminus/LLM-Agent-Learning-Journey
- ReAct 原论文：https://arxiv.org/abs/2210.03629
- OpenAI Function Calling：https://platform.openai.com/docs/guides/function-calling

> 下一阶段预告：推理、规划与技能化 —— Chain-of-Thought、Plan-and-Execute、技能注册表。
>
> 如果本文对你有帮助，欢迎 Star 仓库。
