"""LangGraph Executor."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, Optional

from langgraph.graph.state import CompiledStateGraph


class BaseExecutor(ABC):
    """에이전트 실행기 인터페이스."""

    @abstractmethod
    def invoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def ainvoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        pass

    async def astream(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        result = await self.ainvoke(query, session_id, **kwargs)
        content = result.get("content", "")

        words = content.split() if content else []
        for i, word in enumerate(words):
            yield {
                "is_task_complete": False,
                "require_user_input": False,
                "content": word + (" " if i < len(words) - 1 else ""),
            }
            await asyncio.sleep(0.02)

        yield {"is_task_complete": True, "require_user_input": False, "content": ""}


class LangGraphExecutor(BaseExecutor):
    """LangGraph CompiledGraph 실행기."""

    def __init__(
        self,
        graph: CompiledStateGraph,
        input_key: str = "messages",
        output_key: str = "messages",
        use_langchain_messages: bool = True,
    ):
        self.graph = graph
        self.input_key = input_key
        self.output_key = output_key
        self.use_langchain_messages = use_langchain_messages
        self._langchain_available = self._check_langchain()

    def _check_langchain(self) -> bool:
        if not self.use_langchain_messages:
            return False
        try:
            from langchain_core.messages import HumanMessage
            return True
        except ImportError:
            return False

    def _prepare_input(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._langchain_available and self.use_langchain_messages:
            from langchain_core.messages import HumanMessage
            input_data = {self.input_key: [HumanMessage(content=query)]}
        else:
            input_data = {self.input_key: query}

        if api_config:
            input_data['api_config'] = api_config

        return input_data

    def _prepare_config(self, session_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        config = {}
        if session_id:
            config["configurable"] = {"thread_id": session_id}
        config.update(kwargs)
        return config

    def _extract_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        output = result.get(self.output_key, result)

        if isinstance(output, list) and output:
            last_message = output[-1]
            if hasattr(last_message, "content"):
                return {"content": last_message.content, "data": result, "is_task_complete": True}

        if isinstance(output, str):
            return {"content": output, "data": result, "is_task_complete": True}

        return {"content": str(output), "data": result, "is_task_complete": True}

    def invoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        input_data = self._prepare_input(query, session_id, api_config)
        config = self._prepare_config(session_id, **kwargs)
        result = self.graph.invoke(input_data, config if config else None)
        return self._extract_response(result)

    async def ainvoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        input_data = self._prepare_input(query, session_id, api_config)
        config = self._prepare_config(session_id, **kwargs)

        if hasattr(self.graph, "ainvoke"):
            result = await self.graph.ainvoke(input_data, config if config else None)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self.graph.invoke(input_data, config if config else None)
            )
        return self._extract_response(result)

    async def astream(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        input_data = self._prepare_input(query, session_id, api_config)
        config = self._prepare_config(session_id, **kwargs)

        if hasattr(self.graph, "astream"):
            async for chunk in self.graph.astream(input_data, config if config else None):
                for node_name, node_output in chunk.items():
                    if node_name == "__end__":
                        continue
                    content = self._extract_content_from_chunk(node_output)
                    if content:
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": content,
                            "node": node_name,
                        }
            yield {"is_task_complete": True, "require_user_input": False, "content": ""}
        else:
            async for chunk in super().astream(query, session_id, **kwargs):
                yield chunk

    def _extract_content_from_chunk(self, chunk: Any) -> str:
        if isinstance(chunk, dict):
            messages = chunk.get(self.output_key, [])
            if isinstance(messages, list) and messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    return last_msg.content
            if "response" in chunk:
                return chunk["response"]
            if "content" in chunk:
                return chunk["content"]
        elif hasattr(chunk, "content"):
            return chunk.content
        return ""


class FunctionExecutor(BaseExecutor):
    """함수 기반 실행기."""

    def __init__(self, func):
        self.func = func

    def invoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        try:
            result = self.func(query, **kwargs) if kwargs else self.func(query)
        except TypeError:
            result = self.func(query)
        return self._normalize_result(result)

    async def ainvoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.invoke(query, session_id, api_config, **kwargs))

    def _normalize_result(self, result: Any) -> Dict[str, Any]:
        if isinstance(result, dict):
            content = result.get("response") or result.get("content") or str(result)
            return {"content": content, "data": result, "is_task_complete": True}
        return {"content": str(result), "is_task_complete": True}


class ClassExecutor(BaseExecutor):
    """클래스 기반 실행기."""

    def __init__(self, instance: Any, method_name: str = "invoke"):
        self.instance = instance
        self.method_name = method_name
        self.method = getattr(instance, method_name)

    def invoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        try:
            result = self.method(query, **kwargs) if kwargs else self.method(query)
        except TypeError:
            result = self.method(query)
        return self._normalize_result(result)

    async def ainvoke(self, query: str, session_id: Optional[str] = None, api_config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.invoke(query, session_id, api_config, **kwargs))

    def _normalize_result(self, result: Any) -> Dict[str, Any]:
        if isinstance(result, dict):
            content = result.get("response") or result.get("content") or str(result)
            return {"content": content, "data": result, "is_task_complete": True}
        return {"content": str(result), "is_task_complete": True}
