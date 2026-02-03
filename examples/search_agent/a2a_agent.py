"""Search Agent A2A 서버."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from langgraph_a2a_adapters import LangGraphA2AAdapter, AgentConfig, AgentSkill
from agent import create_search_graph

load_dotenv()


def main():
    graph = create_search_graph()
    adapter = LangGraphA2AAdapter.from_graph(
        graph=graph,
        config=AgentConfig(
            name="Search Agent",
            description="Tavily 기반 웹 검색 에이전트",
            version="1.0.0",
            host="0.0.0.0",
            port=8002,
            skills=[
                AgentSkill(
                    id="web-search",
                    name="웹 검색",
                    description="Tavily 실시간 웹 검색",
                    examples=["AI 최신 트렌드", "Python 3.12 새 기능"],
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
