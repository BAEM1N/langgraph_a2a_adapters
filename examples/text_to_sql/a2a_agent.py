"""Text-to-SQL Agent A2A 서버."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from langgraph_a2a_adapters import LangGraphA2AAdapter, AgentConfig, AgentSkill
from agent import create_text_to_sql_graph

load_dotenv()


def main():
    graph = create_text_to_sql_graph()
    adapter = LangGraphA2AAdapter.from_graph(
        graph=graph,
        config=AgentConfig(
            name="Text-to-SQL Agent",
            description="자연어를 SQL로 변환하여 Chinook DB 조회",
            version="1.0.0",
            host="0.0.0.0",
            port=8001,
            skills=[
                AgentSkill(
                    id="text-to-sql",
                    name="Text-to-SQL",
                    description="자연어 → SQL 변환 및 실행",
                    examples=["가장 많이 팔린 아티스트는?", "록 장르 트랙 수"],
                ),
            ],
        ),
    )
    adapter.serve()


if __name__ == "__main__":
    main()
