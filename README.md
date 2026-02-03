# LangGraph A2A Adapters

[![PyPI version](https://badge.fury.io/py/langgraph-a2a-adapters.svg)](https://badge.fury.io/py/langgraph-a2a-adapters)
[![Python](https://img.shields.io/pypi/pyversions/langgraph-a2a-adapters.svg)](https://pypi.org/project/langgraph-a2a-adapters/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[English](docs/README_EN.md) | [中文](docs/README_CN.md) | [日本語](docs/README_JP.md)**

---

LangGraph로 만든 에이전트를 Google A2A 프로토콜 서버로 바로 띄울 수 있게 해주는 어댑터입니다.

기존에 만들어둔 LangGraph 에이전트가 있다면, 코드 몇 줄이면 A2A 서버로 변환할 수 있습니다. 다른 에이전트에서 HTTP로 호출하거나, 여러 에이전트를 조합해서 쓸 때 유용합니다.

## 설치

```bash
pip install langgraph-a2a-adapters
```

개발 환경 (uv 사용):

```bash
git clone https://github.com/BAEM1N/langgraph_a2a_adapters.git
cd langgraph-a2a-adapters
uv sync --all-extras
```

## 기본 사용법

### 1. 에이전트 만들기

먼저 LangGraph로 에이전트를 만듭니다. 여기선 간단한 날씨 조회 에이전트 예시입니다.

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

@tool
def get_weather(city: str) -> str:
    """도시의 현재 날씨를 조회합니다."""
    return f"{city}: 맑음, 15°C"

llm = ChatOpenAI(model="gpt-4.1")
agent = create_react_agent(llm, [get_weather])
```

### 2. A2A 서버로 실행

만든 에이전트를 어댑터로 감싸면 A2A 서버가 됩니다.

```python
from langgraph_a2a_adapters import LangGraphA2AAdapter, AgentConfig, AgentSkill

adapter = LangGraphA2AAdapter.from_graph(
    graph=agent,
    config=AgentConfig(
        name="Weather Agent",
        description="날씨 조회 에이전트",
        port=8001,
        skills=[
            AgentSkill(id="weather", name="날씨", description="날씨 조회"),
        ],
    ),
)

adapter.serve()
```

### 3. 호출하기

서버가 뜨면 JSON-RPC로 호출하면 됩니다.

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
                "parts": [{"kind": "text", "text": "서울 날씨 알려줘"}]
            }
        }
    }
)
print(response.json())
```

## 에이전트끼리 연결하기

A2A의 장점은 에이전트끼리 서로 호출할 수 있다는 겁니다.

예를 들어, SQL Agent가 DB에서 가장 인기있는 아티스트를 찾고, Search Agent를 호출해서 그 아티스트의 추가 정보를 웹에서 검색하는 식입니다.

### Search Agent (8002 포트)

```python
# examples/search_agent/agent.py
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END

def search_node(state):
    tavily = TavilySearch(max_results=5)
    response = tavily.invoke(state["query"])
    results = response.get("results", []) if isinstance(response, dict) else response
    return {"search_results": results}

# ... 분석, 요약 노드 추가 ...

graph = builder.compile()
```

### SQL Agent에서 Search Agent 호출

```python
# examples/text_to_sql/tools.py
import httpx
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """웹에서 정보를 검색합니다."""
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
    # 응답에서 agent 메시지 추출
    for msg in data.get("result", {}).get("history", []):
        if msg.get("role") == "agent":
            for part in msg.get("parts", []):
                if part.get("kind") == "text":
                    return part.get("text", "")
    return "검색 결과 없음"
```

이 도구를 SQL Agent에 추가하면, SQL Agent가 필요할 때 Search Agent를 호출합니다.

## A2A 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/.well-known/agent.json` | 에이전트 정보 (Agent Card) |
| POST | `/` | JSON-RPC 2.0 |

### JSON-RPC 메서드

| Method | 설명 |
|--------|------|
| `message/send` | 메시지 전송 |
| `message/stream` | 스트리밍 (SSE) |
| `tasks/get` | 태스크 조회 |
| `tasks/cancel` | 태스크 취소 |

## 프로젝트 구조

```
langgraph-a2a-adapters/
├── src/langgraph_a2a_adapters/
│   ├── adapter.py         # 핵심 어댑터
│   ├── config.py          # 설정 클래스
│   ├── executor.py        # 실행기
│   └── decorators.py      # 데코레이터
├── examples/              # 사용 예제
│   ├── search_agent/      # 웹 검색 에이전트
│   └── text_to_sql/       # SQL 에이전트 (Search Agent 호출)
└── docs/                  # 다국어 문서
```

## 예제 실행

```bash
# 환경변수 설정 (.env 파일)
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key

# Search Agent 실행 (포트 8002)
python examples/search_agent/a2a_agent.py

# SQL Agent 실행 (포트 8001)
python examples/text_to_sql/a2a_agent.py
```

## 관련 링크

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [A2A Protocol](https://github.com/google/A2A)
- [a2a-python](https://github.com/google/a2a-python)

## Contributing

이슈나 PR 환영합니다.

## License

MIT License
