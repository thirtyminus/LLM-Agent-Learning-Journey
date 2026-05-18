# 阶段一：API 调用与提示工程

> 掌握 LLM API 调用、参数控制、结构化输出，系统训练提示工程思维。  
> 本文包含完整的代码、模板和对比案例，建议配合仓库实操。

`Python 3.10+` · `DeepSeek` · `MIT License`

---

## 一、准备工作

### 1. 获取仓库

```bash
git clone https://github.com/thirtyminus/LLM-Agent-Learning-Journey.git
cd LLM-Agent-Learning-Journey/phase1-prompt-engineering
```

### 2. 设置 API Key

本阶段默认使用 DeepSeek API（兼容 OpenAI 格式），也支持 OpenAI 和 Anthropic。

```bash
export DEEPSEEK_API_KEY="sk-你的密钥"
```

> 注册地址：https://platform.deepseek.com/api_keys

### 3. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r playground/requirements.txt
```

> 国内加速：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r playground/requirements.txt`

### 4. 验证安装

```bash
python3 playground/chat.py --prompt "你好"
```

一切正常的话，你会看到模型返回的回复。如果看到交互界面，就说明环境已就绪。

![chat.py 运行界面](../images/001.png)

---

## 二、你需要理解的核心概念

### 消息结构

每次调用 LLM 时，你发送的不是一段孤立的文本，而是一组有角色的消息：

```
System    → 设定角色、行为边界、输出格式
User      → 你的输入或问题
Assistant → 模型的回复（也可手动提供作为示例）
```

**System Prompt 是输出质量的分水岭。** 只写一句话等于没写，给出清晰的边界和格式，模型的输出会天差地别。

### 关键参数

- **temperature**（0~2）：越低越确定，越高越有创造力。事实性问题用 0~0.3，创意任务用 0.7~1.2。
- **top_p**（0~1）：核采样，与 temperature 二选一，不同时使用。
- **max_tokens**：防止无限生成，也避免被截断。
- **stop**：遇到指定内容时停止，控制输出终点。

### 提示技巧速览

| 技巧 | 一句话概括 |
|------|-----------|
| **Zero-Shot** | 直接下指令，适合简单明确的任务 |
| **Few-Shot** | 给 2~3 个示例再提问，格式复杂时效果显著 |
| **Chain-of-Thought** | 让模型"一步步思考"，解决推理和数学问题 |
| **Role Prompting** | 给模型一个身份（律师、导师、翻译），输出风格随之变化 |
| **JSON Mode** | 要求输出 JSON 格式，方便程序解析 |
| **Step-back** | 先让模型理解原理再回答，提升复杂问题的准确率 |

---

## 三、交互式聊天工具

`playground/chat.py` 是一个支持多轮对话、流式输出的 CLI 聊天客户端。

### 交互模式

```bash
python3 playground/chat.py
```

进入交互模式后，支持多行输入：

- **Enter** 换行，**Option+Enter**（Mac）或 **Alt+Enter**（Win）发送
- `/` 开头的命令（如 `/exit`、`/clear`）按 Enter 直接执行

### 单次提问模式

```bash
# 一句提问
python3 playground/chat.py --prompt "什么是提示工程？"

# 搭配角色使用
python3 playground/chat.py --system "你是翻译官" --prompt "Hello world"

# 低温度输出（更确定）
python3 playground/chat.py --temperature 0.2 --prompt "1+1="
```

### 从模板加载

```bash
python3 playground/chat.py --system-file prompts/prompt_templates.md
```

![面试官角色运行效果](../images/002.png)
![面试官角色运行效果](../images/003.png)

### 常用参数一览

| 参数 | 作用 |
|------|------|
| `--prompt` | 单次提问，输出后退出 |
| `--system` | 设置 System Prompt |
| `--system-file` | 从文件加载 System Prompt |
| `--temperature` | 温度参数 0.0~2.0 |
| `--max-tokens` | 最大输出 token 数 |
| `--provider` | 切换 API 提供商（deepseek / openai / anthropic） |
| `--model` | 指定模型名称 |

---

## 四、提示模板库

`prompts/prompt_templates.md` 收集了 5 大类 12 个可以直接使用的模板：

**角色扮演类：** 面试官、编程导师、翻译官  
**结构化输出类：** JSON 通用、数据分析、Few-Shot 转 JSON  
**推理思考类：** Chain-of-Thought、数学推理、Step-back  
**内容创作类：** 博客生成、代码审查  
**对话管理类：** 上下文限定、反幻觉 Prompt

每个模板都经过实际测试，直接 `--system-file` 加载即可使用。

---

## 五、实战对比案例

`prompts/examples.md` 中收录了 5 组对比实验，这里挑三个最有代表性的讲：

### 案例 1：Zero-Shot vs Few-Shot

同样是"从邮件提取待办事项"：

**Zero-Shot：** 模型会用自然语言回复，格式随缘，容易遗漏信息。  
**Few-Shot：** 给 2 个输入输出示例后，模型准确输出结构化待办列表。

这就是 Few-Shot 的价值 —— 当输出格式复杂时，给例子比说一万字都管用。

### 案例 2：不要角色 vs 角色 Prompting

同样是"转行 AI 工程师的建议"：

**没角色：** 回答笼统、教科书式。  
**加角色：** "你是一名有 8 年经验的 AI 工程师"—— 回答变成了过来人的经验分享，实操性大幅提升。

### 案例 3：直接问 vs Chain-of-Thought

经典题："李华的爸爸有三个儿子：大毛、二毛，三儿子叫什么？"

**直接问：** 模型容易惯性回答"三毛"。  
**加一句"请一步步推理"：** 模型会识别出"李华的爸爸"这个关键信息，意识到第三子就是李华本人。

---

## 六、实践路线建议

1. **先跑通**：`--prompt "你好"`，感受第一次调通 API 的反馈
2. **调参数**：分别试 `temperature=0` 和 `temperature=1.5`，观察差异
3. **设计角色**：给个面试官角色，看回答风格的变化
4. **做对比**：拿一个模板分别用 Zero-Shot 和 Few-Shot 试，数据说话
5. **JSON Mode**：让模型输出 JSON，体验可解析的结构化数据
6. **Chain-of-Thought**：找个逻辑题，对比加不加"一步步思考"的效果

建议每次只改变一个变量，记录输出，对比分析。

---

## 七、常见陷阱

- **Temperature 太高导致幻觉**：事实性问题用 0~0.3
- **System Prompt 太短**：一句话等于没写，给出明确边界
- **JSON Mode 不设 Schema**：模型可能输出意料之外的字段
- **忘记设 max_tokens**：长回复可能被截断

---

## 八、配套资源

- 完整代码：https://github.com/thirtyminus/LLM-Agent-Learning-Journey
- DeepSeek API 文档：https://platform.deepseek.com/api-docs
- OpenAI 提示工程指南：https://platform.openai.com/docs/guides/prompt-engineering

> 下一阶段预告：上下文与记忆系统 —— 滑动窗口、摘要压缩、向量检索与实体记忆。
>
> 如果本文对你有帮助，欢迎 Star 仓库，一起见证学习轨迹。
