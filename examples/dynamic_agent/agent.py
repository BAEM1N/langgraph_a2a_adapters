"""동적 API 키를 지원하는 Simple Agent."""

from typing import Any, Optional, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END


class SimpleState(TypedDict):
    query: str
    messages: list[BaseMessage]
    api_config: Optional[dict[str, Any]]


def _get_langfuse_callback(api_config: dict):
    """Langfuse 콜백 생성 (환경변수 기반)."""
    import os

    secret_key = api_config.get('LANGFUSE_SECRET_KEY')
    public_key = api_config.get('LANGFUSE_PUBLIC_KEY')
    if not secret_key or not public_key:
        print(f"[DEBUG] Langfuse keys missing: secret={bool(secret_key)}, public={bool(public_key)}")
        return None
    try:
        # 환경변수로 설정 (langfuse.langchain.CallbackHandler는 환경변수 사용)
        os.environ['LANGFUSE_SECRET_KEY'] = secret_key
        os.environ['LANGFUSE_PUBLIC_KEY'] = public_key
        host = api_config.get('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')
        os.environ['LANGFUSE_HOST'] = host

        print(f"[DEBUG] Creating Langfuse callback with host: {host}")

        from langfuse.langchain import CallbackHandler
        cb = CallbackHandler()

        print(f"[DEBUG] Langfuse callback created successfully")
        return cb
    except ImportError as e:
        print(f"[DEBUG] Langfuse import error: {e}")
        return None
    except Exception as e:
        print(f"[DEBUG] Langfuse callback error: {e}")
        return None


def chat_node(state: SimpleState) -> dict:
    """LLM 호출."""
    api_config = state.get('api_config') or {}
    print(f"[DEBUG] api_config keys: {list(api_config.keys())}")
    print(f"[DEBUG] LANGFUSE_SECRET_KEY: {'있음' if api_config.get('LANGFUSE_SECRET_KEY') else '없음'}")

    api_key = api_config.get('OPENAI_API_KEY')
    if not api_key:
        return {"messages": [AIMessage(content="❌ X-OPENAI-API-KEY 헤더가 필요합니다.")]}

    model = api_config.get('OPENAI_MODEL') or "gpt-4.1"
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=api_config.get('OPENAI_BASE_URL'),
        temperature=0.7,
    )

    prompt = f"""사용자 메시지에 답변하세요.

사용자: {state['query']}

답변 시 먼저 당신이 어떤 AI 모델인지 간단히 소개하고 답변해주세요."""

    # Langfuse 콜백 설정
    callbacks = []
    langfuse_cb = _get_langfuse_callback(api_config)
    if langfuse_cb:
        callbacks.append(langfuse_cb)

    config = {"callbacks": callbacks} if callbacks else None
    response = llm.invoke([HumanMessage(content=prompt)], config=config)
    return {"messages": [AIMessage(content=response.content)]}


def create_dynamic_search_graph():
    """동적 API 키를 지원하는 Simple Graph 생성."""
    builder = StateGraph(SimpleState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    return builder.compile()
