"""동적 API 키를 지원하는 Search Agent."""

import operator
from typing import Annotated, Any, Optional, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END


class SearchState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    query: str
    search_results: list[dict]
    summary: str
    api_config: Optional[dict[str, Any]]


def get_openai_client(api_config: dict) -> ChatOpenAI:
    """api_config 기반으로 OpenAI 클라이언트 생성."""
    return ChatOpenAI(
        model=api_config.get('openai_model') or "gpt-4.1",
        api_key=api_config.get('openai_api_key'),
        base_url=api_config.get('openai_base_url'),
        temperature=0,
    )


def get_tavily_client(api_config: dict) -> TavilySearch:
    """api_config 기반으로 Tavily 클라이언트 생성."""
    return TavilySearch(
        api_key=api_config.get('tavily_api_key'),
        max_results=5,
    )


def search_node(state: SearchState) -> dict:
    """웹 검색 실행."""
    api_config = state.get('api_config') or {}
    tavily = get_tavily_client(api_config)

    try:
        response = tavily.invoke(state["query"])
        results = response.get("results", []) if isinstance(response, dict) else response
        search_results = [
            {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
            for r in results
        ]
        return {
            "search_results": search_results,
            "messages": [AIMessage(content=f"검색 완료: {len(search_results)}개 결과")],
        }
    except Exception as e:
        return {
            "search_results": [],
            "messages": [AIMessage(content=f"검색 오류: {e}")],
        }


def summarize_node(state: SearchState) -> dict:
    """검색 결과 요약."""
    api_config = state.get('api_config') or {}
    results = state["search_results"]

    if not results:
        return {"summary": "검색 결과가 없습니다.", "messages": [AIMessage(content="검색 결과 없음")]}

    llm = get_openai_client(api_config)
    prompt = f"""검색 결과를 요약해주세요.

질문: {state['query']}

검색 결과:
{chr(10).join([f"- [{r['title']}]({r['url']}): {r['content'][:200]}..." for r in results])}

요약 규칙: 핵심만 간결하게, 출처 URL 포함"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"summary": response.content, "messages": [AIMessage(content=response.content)]}


def create_dynamic_search_graph():
    """동적 API 키를 지원하는 Search Graph 생성."""
    builder = StateGraph(SearchState)
    builder.add_node("search", search_node)
    builder.add_node("summarize", summarize_node)
    builder.add_edge(START, "search")
    builder.add_edge("search", "summarize")
    builder.add_edge("summarize", END)
    return builder.compile()
