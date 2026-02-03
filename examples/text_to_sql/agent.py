"""DeepAgents 기반 Text-to-SQL Graph."""

import urllib.request
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from tools import search_web


def download_chinook_db() -> Path:
    """Chinook DB 다운로드."""
    db_path = Path(__file__).parent / "chinook.db"
    if not db_path.exists():
        url = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
        urllib.request.urlretrieve(url, db_path)
    return db_path


def create_text_to_sql_graph():
    """Text-to-SQL Deep Agent 그래프 생성."""
    base_dir = Path(__file__).parent
    db_path = download_chinook_db()

    db = SQLDatabase.from_uri(f"sqlite:///{db_path}", sample_rows_in_table_info=3)
    model = ChatOpenAI(model="gpt-4.1", temperature=0)
    toolkit = SQLDatabaseToolkit(db=db, llm=model)

    # SQL 도구 + Search Agent 호출 도구
    tools = toolkit.get_tools() + [search_web]

    graph = create_deep_agent(
        model=model,
        memory=[str(base_dir / "AGENTS.md")],
        skills=[str(base_dir / "skills/")],
        tools=tools,
        subagents=[],
        backend=FilesystemBackend(root_dir=str(base_dir)),
    )
    return graph


if __name__ == "__main__":
    from dotenv import load_dotenv
    from langchain_core.messages import HumanMessage

    load_dotenv()

    graph = create_text_to_sql_graph()
    result = graph.invoke({"messages": [HumanMessage(content="가장 인기있는 아티스트 찾고 웹에서 정보 검색해줘")]})
    print(result["messages"][-1].content)
