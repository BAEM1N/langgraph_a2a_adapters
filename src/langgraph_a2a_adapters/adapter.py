"""LangGraph A2A Adapter."""

from typing import Any, Callable, Optional, Union

import uvicorn
from langgraph.graph.state import CompiledStateGraph

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import Task, TaskState, TaskStatus, TaskStatusUpdateEvent, TextPart
from a2a.utils import new_agent_text_message

from langgraph_a2a_adapters.config import AgentConfig
from langgraph_a2a_adapters.executor import (
    BaseExecutor,
    LangGraphExecutor,
    FunctionExecutor,
    ClassExecutor,
)


class LangGraphAgentExecutor(AgentExecutor):
    """LangGraph 실행기를 A2A AgentExecutor로 래핑."""

    def __init__(self, executor: BaseExecutor):
        self.executor = executor

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id

        input_text = self._extract_input_text(context)
        api_config = self._extract_api_config(context)

        try:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    taskId=task_id,
                    contextId=context_id,
                    status=TaskStatus(state=TaskState.working),
                    final=False,
                )
            )

            result = await self.executor.ainvoke(input_text, api_config=api_config)
            response_text = result.get("content", "")
            response_message = new_agent_text_message(response_text)

            history = (
                [context.message, response_message]
                if context.message
                else [response_message]
            )
            task = Task(
                id=task_id,
                contextId=context_id,
                status=TaskStatus(state=TaskState.completed),
                history=history,
            )
            await event_queue.enqueue_event(task)

        except Exception as e:
            error_task = Task(
                id=task_id,
                contextId=context_id,
                status=TaskStatus(state=TaskState.failed, message=str(e)),
            )
            await event_queue.enqueue_event(error_task)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = Task(
            id=context.task_id,
            contextId=context.context_id,
            status=TaskStatus(state=TaskState.canceled),
        )
        await event_queue.enqueue_event(task)

    def _extract_input_text(self, context: RequestContext) -> str:
        if not context.message or not context.message.parts:
            return ""

        for part in context.message.parts:
            if hasattr(part, "root"):
                inner = part.root
                if hasattr(inner, "text"):
                    return inner.text
            elif isinstance(part, TextPart):
                return part.text
            elif isinstance(part, dict) and part.get("kind") == "text":
                return part.get("text", "")
            elif hasattr(part, "text"):
                return part.text
        return ""

    def _extract_api_config(self, context: RequestContext) -> dict:
        if not context.call_context or not context.call_context.state:
            return {}

        headers = context.call_context.state.get('headers', {})
        return {
            'openai_api_key': headers.get('x-openai-api-key'),
            'openai_base_url': headers.get('x-openai-base-url'),
            'openai_model': headers.get('x-openai-model'),
            'tavily_api_key': headers.get('x-tavily-api-key'),
        }


class LangGraphA2AAdapter:
    """LangGraph를 A2A 프로토콜로 노출하는 어댑터."""

    def __init__(self, executor: BaseExecutor, config: AgentConfig):
        self.executor = executor
        self.config = config
        self._app = None
        self._task_store = InMemoryTaskStore()
        self._agent_executor = LangGraphAgentExecutor(executor)
        self._request_handler = DefaultRequestHandler(
            agent_executor=self._agent_executor,
            task_store=self._task_store,
        )

    @classmethod
    def from_graph(
        cls,
        graph: CompiledStateGraph,
        config: AgentConfig,
        input_key: str = "messages",
        output_key: str = "messages",
        use_langchain_messages: bool = True,
    ) -> "LangGraphA2AAdapter":
        """CompiledStateGraph에서 어댑터 생성."""
        executor = LangGraphExecutor(
            graph=graph,
            input_key=input_key,
            output_key=output_key,
            use_langchain_messages=use_langchain_messages,
        )
        return cls(executor, config)

    @classmethod
    def from_function(
        cls,
        func: Callable[[str], Union[str, dict]],
        config: AgentConfig,
    ) -> "LangGraphA2AAdapter":
        """함수에서 어댑터 생성."""
        executor = FunctionExecutor(func)
        return cls(executor, config)

    @classmethod
    def from_class(
        cls,
        instance: Any,
        config: AgentConfig,
        method_name: str = "invoke",
    ) -> "LangGraphA2AAdapter":
        """클래스 인스턴스에서 어댑터 생성."""
        executor = ClassExecutor(instance, method_name)
        return cls(executor, config)

    @property
    def app(self):
        if self._app is None:
            self._app = self._create_app()
        return self._app

    def _create_app(self):
        agent_card = self.config.to_agent_card()
        a2a_app = A2AFastAPIApplication(
            agent_card=agent_card,
            http_handler=self._request_handler,
        )
        return a2a_app.build(
            title=self.config.name,
            description=self.config.description,
            version=self.config.version,
        )

    def serve(self, host: Optional[str] = None, port: Optional[int] = None):
        host = host or self.config.host
        port = port or self.config.port
        self.config.port = port

        print(f"\n{self.config.name} v{self.config.version}")
        print(f"http://{host}:{port}\n")

        uvicorn.run(self.app, host=host, port=port, log_level="info")
