# 🧠 LLM & Agent 学习仓库

> 从零掌握大模型调用、Agent 系统设计与生产级工程实践  
> 涵盖 Prompt Engineering、Context Engineering、Harness Engineering 等核心课题

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/status-进行中-yellow" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 📖 关于本仓库

这是我在学习 **LLM 基础机制、Agent 系统、模型上下文工程、缰绳工程** 过程中的代码、笔记和项目集合。整个学习过程分为六个阶段，从裸模型调用开始，一步步构建出可协作、可观测、可落地的生产级多代理系统。

如果你也在学习这些内容，希望这个仓库能为你提供清晰的路径和可复用的参考代码。

---

## 🗺️ 学习路线图

- [ ] **阶段一：API 调用与提示工程** — [phase1-prompt-engineering](./phase1-prompt-engineering/)  
  掌握 LLM API 使用、参数控制、结构化输出，系统训练提示工程思维。

- [ ] **阶段二：上下文与记忆系统** — [phase2-context-memory](./phase2-context-memory/)  
  学习短期/长期记忆实现：滑动窗口、摘要压缩、向量检索与实体记忆。

- [ ] **阶段三：工具使用与 Agent 循环** — [phase3-agent-loop-tools](./phase3-agent-loop-tools/)  
  从零实现 ReAct 模式，赋予模型调用工具的能力，理解 Agent Loop。

- [ ] **阶段四：推理、规划与技能化** — [phase4-reasoning-planning-skills](./phase4-reasoning-planning-skills/)  
  引入 Chain-of-Thought、Plan-and-Execute、自一致性推理，构建技能注册表。

- [ ] **阶段五：KV Cache 与 MCP 协议** — [phase5-kvcache-mcp](./phase5-kvcache-mcp/)  
  深入推理性能优化（前缀缓存、KV Cache）与标准化工具连接（MCP）。

- [ ] **阶段六：多代理与生产级缰绳工程** — [phase6-multi-agent-harness](./phase6-multi-agent-harness/)  
  实现子代理、多代理协作，加入容错、护栏、可观测性与成本控制，打造完整服务。

---

## 🚀 快速开始

### 获取仓库

```bash
git clone https://github.com/thirtyminus/LLM-Agent-Learning-Journey.git
cd LLM-Agent-Learning-Journey
```

### 环境要求

- **Python** 3.10+
- **LLM API 密钥**（如 OpenAI、Anthropic 等）
- **（阶段五）** 可选的 GPU 环境用于推理优化实验

### 虚拟环境与依赖安装

本项目分六个阶段推进，各阶段依赖可能不同。建议**每个阶段单独创建虚拟环境**，互不污染。

```bash
# 进入目标阶段
cd phase1-prompt-engineering

# 创建虚拟环境
python3 -m venv .venv

# 激活
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate   # Windows

# 安装该阶段依赖
pip install -r playground/requirements.txt
```

> **国内加速：** 如果直接 `pip install` 速度慢，可选用以下方式之一：
>
> **方式一：镜像源（推荐）**
> ```bash
> # 永久配置（一次生效）
> pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
>
> # 或单次使用
> pip install -r playground/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```
>
> **方式二：代理**
> ```bash
> pip install --proxy http://127.0.0.1:7890 -r playground/requirements.txt
> ```

### 仓库结构

```text
LLM-Agent-Learning-Journey/
├── README.md
├── .gitignore
├── LICENSE
├── phase1-prompt-engineering/        # 提示工程实战
│   ├── playground/                   # 聊天工具、流式输出
│   └── prompts/                      # 常用提示模板
├── phase2-context-memory/            # 上下文与记忆
│   ├── memory_system/                # 向量、摘要、实体记忆实现
│   └── experiments/                  # 策略对比实验
├── phase3-agent-loop-tools/          # Agent 循环与工具
│   ├── react_agent/                  # 从零实现的 ReAct 循环
│   └── tools/                        # 天气、计算器、搜索等工具
├── phase4-reasoning-planning-skills/ # 推理、规划、技能
│   ├── planner/                      # 旅行规划、动态计划
│   └── skills/                       # 技能注册表与示例
├── phase5-kvcache-mcp/               # 推理优化与连接协议
│   ├── kvcache_demo/                 # 前缀缓存实验
│   └── mcp_server/                   # 自定义 MCP 服务器
└── phase6-multi-agent-harness/       # 多代理与工程化
    ├── multi_agent/                  # 模拟团队、辩论系统
    └── production_harness/           # FastAPI 服务、护栏、监控
```

---

## ✍️ 学习笔记

每个阶段文件夹下的 `README.md` 都记录了该阶段的核心概念、工程要点与个人实践心得，你可以从这些笔记中快速了解相关知识。

---

## 🛠️ 技术栈与关键词

| 类别 | 关键词 |
|------|--------|
| 模型基础 | `LLM API` · `KV Cache` · `Context Engineering` |
| 智能体核心 | `Agent Loop` · `Tool Use` · `Reasoning` · `Planning` · `Skills` |
| 连接与优化 | `MCP` · `Memory` · `Subagent` |
| 工程实践 | `Multi-Agent` · `Prompt Engineering` · `Harness Engineering` |

---

## 📌 学习原则

> **每一行核心代码都亲手写** — 不盲目套用框架，先理解机制再选择性借用轮子。
>
> **用实验巩固认知** — 每个阶段都设计对比实验，让数据说话。
>
> **文档即思考** — 把写作当成梳理和深化的过程。

---

## 🌟 参与贡献

这是一个持续生长的仓库，欢迎 **Star** ⭐ 或 **Watch** 👀 一起见证学习轨迹。

如果任何内容对你有帮助，或想一起探讨，欢迎 [提 Issue](https://github.com/thirtyminus/LLM-Agent-Learning-Journey/issues) 交流！