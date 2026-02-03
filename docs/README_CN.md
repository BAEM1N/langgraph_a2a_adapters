# LangGraph A2A Adapters

[![PyPI version](https://badge.fury.io/py/langgraph-a2a-adapters.svg)](https://badge.fury.io/py/langgraph-a2a-adapters)
[![Python](https://img.shields.io/pypi/pyversions/langgraph-a2a-adapters.svg)](https://pypi.org/project/langgraph-a2a-adapters/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[한국어](../README.md) | [English](README_EN.md) | [日本語](README_JP.md)**

> 本文档为自动翻译。

---

这是一个适配器，可以将 LangGraph 代理作为 Google A2A 协议服务器运行。

如果你已经有一个 LangGraph 代理，只需几行代码就可以将其转换为 A2A 服务器。在通过 HTTP 调用代理或组合多个代理时非常有用。

## 安装

```bash
pip install langgraph-a2a-adapters
```

开发环境（使用 uv）：

```bash
git clone https://github.com/baem1n/langgraph-a2a-adapters.git
cd langgraph-a2a-adapters
uv sync --all-extras
```

## 基本用法

### 1. 创建代理

首先，使用 LangGraph 创建一个代理。这是一个简单的天气代理示例。

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

@tool
def get_weather(city: str) -> str:
    """查询城市当前天气。"""
    return f"{city}: 晴天, 15°C"

llm = ChatOpenAI(model="gpt-4.1")
agent = create_react_agent(llm, [get_weather])
```

### 2. 作为 A2A 服务器运行

用适配器包装代理，创建 A2A 服务器。

```python
from langgraph_a2a_adapters import LangGraphA2AAdapter, AgentConfig, AgentSkill

adapter = LangGraphA2AAdapter.from_graph(
    graph=agent,
    config=AgentConfig(
        name="Weather Agent",
        description="天气查询代理",
        port=8001,
        skills=[
            AgentSkill(id="weather", name="天气", description="天气查询"),
        ],
    ),
)

adapter.serve()
```

### 3. 调用代理

服务器运行后，通过 JSON-RPC 调用。

```python
import httpx

response = httpx.post(
    "http://localhost:8001/",
    json={
        "jsonrpc": "2.0",
        "id": "1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "msg-001",
                "parts": [{"kind": "text", "text": "首尔天气怎么样？"}]
            }
        }
    }
)
print(response.json())
```

## 连接代理

A2A 的优势是代理之间可以相互调用。

例如，SQL Agent 可以在数据库中找到最受欢迎的艺术家，然后调用 Search Agent 在网上搜索该艺术家的更多信息。

### Search Agent（端口 8002）

```python
# examples/search_agent/agent.py
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

def search_node(state):
    tavily = TavilySearch(max_results=5)
    response = tavily.invoke(state["query"])
    results = response.get("results", []) if isinstance(response, dict) else response
    return {"search_results": results}

# ... 添加分析、摘要节点 ...

graph = builder.compile()
```

### SQL Agent 调用 Search Agent

```python
# examples/text_to_sql/tools.py
import httpx
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """在网上搜索信息。"""
    response = httpx.post(
        "http://localhost:8002/",
        json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "messageId": "msg-001",
                    "parts": [{"kind": "text", "text": query}]
                }
            }
        }
    )
    data = response.json()
    for msg in data.get("result", {}).get("history", []):
        if msg.get("role") == "agent":
            for part in msg.get("parts", []):
                if part.get("kind") == "text":
                    return part.get("text", "")
    return "无搜索结果"
```

将此工具添加到 SQL Agent，它会在需要时调用 Search Agent。

## A2A 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/.well-known/agent.json` | 代理信息（Agent Card） |
| POST | `/` | JSON-RPC 2.0 |

### JSON-RPC 方法

| 方法 | 描述 |
|------|------|
| `message/send` | 发送消息 |
| `message/stream` | 流式传输（SSE） |
| `tasks/get` | 获取任务 |
| `tasks/cancel` | 取消任务 |

## 项目结构

```
langgraph-a2a-adapters/
├── src/langgraph_a2a_adapters/
│   ├── adapter.py         # 核心适配器
│   ├── config.py          # 配置类
│   ├── executor.py        # 执行器
│   └── decorators.py      # 装饰器
├── examples/              # 使用示例
│   ├── search_agent/      # 网络搜索代理
│   └── text_to_sql/       # SQL 代理（调用 Search Agent）
└── docs/                  # 多语言文档
```

## 运行示例

```bash
# 设置环境变量（.env 文件）
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key

# 运行 Search Agent（端口 8002）
python examples/search_agent/a2a_agent.py

# 运行 SQL Agent（端口 8001）
python examples/text_to_sql/a2a_agent.py
```

## 相关链接

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [A2A Protocol](https://github.com/google/A2A)
- [a2a-python](https://github.com/google/a2a-python)

## 贡献

欢迎提交 Issue 和 PR。

## 许可证

MIT License
