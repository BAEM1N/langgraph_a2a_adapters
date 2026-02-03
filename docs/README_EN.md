# LangGraph A2A Adapters

[![PyPI version](https://badge.fury.io/py/langgraph-a2a-adapters.svg)](https://badge.fury.io/py/langgraph-a2a-adapters)
[![Python](https://img.shields.io/pypi/pyversions/langgraph-a2a-adapters.svg)](https://pypi.org/project/langgraph-a2a-adapters/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[한국어](../README.md) | [中文](README_CN.md) | [日本語](README_JP.md)**

> This document was automatically translated.

---

An adapter that lets you run LangGraph agents as Google A2A protocol servers.

If you already have a LangGraph agent, you can convert it to an A2A server with just a few lines of code. Useful when calling agents over HTTP or combining multiple agents.

## Installation

```bash
pip install langgraph-a2a-adapters
```

Development (using uv):

```bash
git clone https://github.com/baem1n/langgraph-a2a-adapters.git
cd langgraph-a2a-adapters
uv sync --all-extras
```

## Basic Usage

### 1. Create an Agent

First, create an agent with LangGraph. Here's a simple weather agent example.

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"{city}: Sunny, 15°C"

llm = ChatOpenAI(model="gpt-4.1")
agent = create_react_agent(llm, [get_weather])
```

### 2. Run as A2A Server

Wrap the agent with the adapter to create an A2A server.

```python
from langgraph_a2a_adapters import LangGraphA2AAdapter, AgentConfig, AgentSkill

adapter = LangGraphA2AAdapter.from_graph(
    graph=agent,
    config=AgentConfig(
        name="Weather Agent",
        description="Weather lookup agent",
        port=8001,
        skills=[
            AgentSkill(id="weather", name="Weather", description="Weather lookup"),
        ],
    ),
)

adapter.serve()
```

### 3. Call the Agent

Once the server is running, call it via JSON-RPC.

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
                "parts": [{"kind": "text", "text": "What's the weather in Seoul?"}]
            }
        }
    }
)
print(response.json())
```

## Connecting Agents

The advantage of A2A is that agents can call each other.

For example, a SQL Agent can find the most popular artist in a database, then call a Search Agent to look up additional information about that artist on the web.

### Search Agent (port 8002)

```python
# examples/search_agent/agent.py
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

def search_node(state):
    tavily = TavilySearch(max_results=5)
    response = tavily.invoke(state["query"])
    results = response.get("results", []) if isinstance(response, dict) else response
    return {"search_results": results}

# ... add analysis, summary nodes ...

graph = builder.compile()
```

### SQL Agent Calling Search Agent

```python
# examples/text_to_sql/tools.py
import httpx
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
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
    return "No search results"
```

Add this tool to the SQL Agent, and it will call the Search Agent when needed.

## A2A Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/.well-known/agent.json` | Agent info (Agent Card) |
| POST | `/` | JSON-RPC 2.0 |

### JSON-RPC Methods

| Method | Description |
|--------|-------------|
| `message/send` | Send message |
| `message/stream` | Streaming (SSE) |
| `tasks/get` | Get task |
| `tasks/cancel` | Cancel task |

## Project Structure

```
langgraph-a2a-adapters/
├── src/langgraph_a2a_adapters/
│   ├── adapter.py         # Core adapter
│   ├── config.py          # Config classes
│   ├── executor.py        # Executor
│   └── decorators.py      # Decorators
├── examples/              # Usage examples
│   ├── search_agent/      # Web search agent
│   └── text_to_sql/       # SQL agent (calls Search Agent)
└── docs/                  # Multilingual docs
```

## Running Examples

```bash
# Set environment variables (.env file)
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key

# Run Search Agent (port 8002)
python examples/search_agent/a2a_agent.py

# Run SQL Agent (port 8001)
python examples/text_to_sql/a2a_agent.py
```

## Related Links

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [A2A Protocol](https://github.com/google/A2A)
- [a2a-python](https://github.com/google/a2a-python)

## Contributing

Issues and PRs are welcome.

## License

MIT License
