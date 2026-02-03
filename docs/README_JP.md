# LangGraph A2A Adapters

[![PyPI version](https://badge.fury.io/py/langgraph-a2a-adapters.svg)](https://badge.fury.io/py/langgraph-a2a-adapters)
[![Python](https://img.shields.io/pypi/pyversions/langgraph-a2a-adapters.svg)](https://pypi.org/project/langgraph-a2a-adapters/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[한국어](../README.md) | [English](README_EN.md) | [中文](README_CN.md)**

> このドキュメントは自動翻訳されました。

---

LangGraphで作成したエージェントをGoogle A2Aプロトコルサーバーとして実行できるアダプターです。

既存のLangGraphエージェントがあれば、数行のコードでA2Aサーバーに変換できます。HTTPでエージェントを呼び出したり、複数のエージェントを組み合わせて使用する際に便利です。

## インストール

```bash
pip install langgraph-a2a-adapters
```

開発環境（uvを使用）：

```bash
git clone https://github.com/baem1n/langgraph-a2a-adapters.git
cd langgraph-a2a-adapters
uv sync --all-extras
```

## 基本的な使い方

### 1. エージェントを作成

まず、LangGraphでエージェントを作成します。ここでは簡単な天気エージェントの例です。

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

@tool
def get_weather(city: str) -> str:
    """都市の現在の天気を取得します。"""
    return f"{city}: 晴れ, 15°C"

llm = ChatOpenAI(model="gpt-4.1")
agent = create_react_agent(llm, [get_weather])
```

### 2. A2Aサーバーとして実行

アダプターでエージェントをラップしてA2Aサーバーを作成します。

```python
from langgraph_a2a_adapters import LangGraphA2AAdapter, AgentConfig, AgentSkill

adapter = LangGraphA2AAdapter.from_graph(
    graph=agent,
    config=AgentConfig(
        name="Weather Agent",
        description="天気検索エージェント",
        port=8001,
        skills=[
            AgentSkill(id="weather", name="天気", description="天気検索"),
        ],
    ),
)

adapter.serve()
```

### 3. エージェントを呼び出す

サーバーが起動したら、JSON-RPCで呼び出します。

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
                "parts": [{"kind": "text", "text": "ソウルの天気を教えて"}]
            }
        }
    }
)
print(response.json())
```

## エージェント間の連携

A2Aの利点は、エージェント同士が互いに呼び出せることです。

例えば、SQL Agentがデータベースで最も人気のあるアーティストを見つけ、Search Agentを呼び出してそのアーティストの追加情報をウェブで検索するといったことができます。

### Search Agent（ポート8002）

```python
# examples/search_agent/agent.py
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

def search_node(state):
    tavily = TavilySearch(max_results=5)
    response = tavily.invoke(state["query"])
    results = response.get("results", []) if isinstance(response, dict) else response
    return {"search_results": results}

# ... 分析、要約ノードを追加 ...

graph = builder.compile()
```

### SQL AgentからSearch Agentを呼び出す

```python
# examples/text_to_sql/tools.py
import httpx
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """ウェブで情報を検索します。"""
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
    return "検索結果なし"
```

このツールをSQL Agentに追加すると、必要に応じてSearch Agentを呼び出します。

## A2Aエンドポイント

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/.well-known/agent.json` | エージェント情報（Agent Card） |
| POST | `/` | JSON-RPC 2.0 |

### JSON-RPCメソッド

| メソッド | 説明 |
|----------|------|
| `message/send` | メッセージ送信 |
| `message/stream` | ストリーミング（SSE） |
| `tasks/get` | タスク取得 |
| `tasks/cancel` | タスクキャンセル |

## プロジェクト構造

```
langgraph-a2a-adapters/
├── src/langgraph_a2a_adapters/
│   ├── adapter.py         # コアアダプター
│   ├── config.py          # 設定クラス
│   ├── executor.py        # エグゼキューター
│   └── decorators.py      # デコレーター
├── examples/              # 使用例
│   ├── search_agent/      # ウェブ検索エージェント
│   └── text_to_sql/       # SQLエージェント（Search Agentを呼び出す）
└── docs/                  # 多言語ドキュメント
```

## サンプルの実行

```bash
# 環境変数を設定（.envファイル）
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key

# Search Agentを実行（ポート8002）
python examples/search_agent/a2a_agent.py

# SQL Agentを実行（ポート8001）
python examples/text_to_sql/a2a_agent.py
```

## 関連リンク

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [A2A Protocol](https://github.com/google/A2A)
- [a2a-python](https://github.com/google/a2a-python)

## コントリビュート

IssueやPRを歓迎します。

## ライセンス

MIT License
