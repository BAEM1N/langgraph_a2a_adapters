"""Tavily 기반 Search Agent Graph."""

import operator
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END


class SearchState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    query: str
    search_results: list[dict]
    analysis: str
    summary: str


def search_node(state: SearchState) -> dict:
    """Tavily 웹 검색 실행."""
    tavily = TavilySearch(max_results=5)
    try:
        response = tavily.invoke(state["query"])
        results = response.get("results", []) if isinstance(response, dict) else response
        search_results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            }
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


def analyze_node(state: SearchState) -> dict:
    """검색 결과 분석."""
    results = state["search_results"]
    if not results:
        return {
            "analysis": "검색 결과가 없습니다.",
            "messages": [AIMessage(content="분석할 문서가 없습니다.")],
        }

    llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    prompt = f"""검색 결과를 분석해주세요.

쿼리: {state['query']}

결과:
{chr(10).join([f"- [{r['title']}]({r['url']}): {r['content'][:200]}..." for r in results])}

분석: 1) 주요 주제 2) 정보 신뢰도 3) 핵심 인사이트"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {
        "analysis": response.content,
        "messages": [AIMessage(content="분석 완료")],
    }


def summarize_node(state: SearchState) -> dict:
    """최종 요약 생성."""
    llm = ChatOpenAI(model="gpt-4.1", temperature=0.3)
    prompt = f"""검색 결과를 요약해주세요.

질문: {state['query']}

검색 결과:
{chr(10).join([f"- {r['title']}" for r in state['search_results']])}

분석:
{state['analysis']}

요약 규칙: 핵심만 간결하게, 출처 URL 포함, 한국어로 친근하게"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {
        "summary": response.content,
        "messages": [AIMessage(content=response.content)],
    }


def create_search_graph():
    """Search Agent StateGraph 생성."""
    builder = StateGraph(SearchState)
    builder.add_node("search", search_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("summarize", summarize_node)
    builder.add_edge(START, "search")
    builder.add_edge("search", "analyze")
    builder.add_edge("analyze", "summarize")
    builder.add_edge("summarize", END)
    return builder.compile()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    graph = create_search_graph()
    result = graph.invoke({"query": "2025 AI 트렌드"})
    print(result["summary"])
