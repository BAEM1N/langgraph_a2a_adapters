"""Dynamic Search Agent A2A 서버."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv

from langgraph_a2a_adapters import LangGraphA2AAdapter, AgentConfig, AgentSkill
from agent import create_dynamic_search_graph

load_dotenv()


def main():
    graph = create_dynamic_search_graph()
    adapter = LangGraphA2AAdapter.from_graph(
        graph=graph,
        config=AgentConfig(
            name="Dynamic Search Agent",
            description="HTTP 헤더로 API 키를 동적으로 받는 검색 에이전트",
            version="1.0.0",
            host="0.0.0.0",
            port=8003,
            skills=[
                AgentSkill(
                    id="dynamic-search",
                    name="동적 검색",
                    description="요청별 API 키로 웹 검색",
                    examples=["AI 최신 뉴스", "Python 3.13 새 기능"],
                ),
            ],
        ),
        input_key="query",
        output_key="messages",
        use_langchain_messages=False,
    )
    adapter.serve()


if __name__ == "__main__":
    main()
