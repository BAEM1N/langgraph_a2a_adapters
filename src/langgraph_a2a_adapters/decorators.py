"""A2A 데코레이터."""

from __future__ import annotations

from typing import Callable, List, Optional

from langgraph_a2a_adapters.adapter import LangGraphA2AAdapter
from langgraph_a2a_adapters.config import AgentConfig, AgentSkill


def a2a_agent(
    name: str,
    description: str = "",
    port: int = 8000,
    host: str = "0.0.0.0",
    skills: Optional[List[AgentSkill]] = None,
    version: str = "1.0.0",
):
    """함수를 A2A 에이전트로 변환."""

    def decorator(func: Callable):
        config = AgentConfig(
            name=name,
            description=description or func.__doc__ or "",
            port=port,
            host=host,
            version=version,
            skills=skills
            or [
                AgentSkill(
                    id="main",
                    name=name,
                    description=description or func.__doc__ or f"{name} 기능",
                )
            ],
        )

        adapter = LangGraphA2AAdapter.from_function(func, config)

        func.invoke = adapter.invoke
        func.ainvoke = adapter.ainvoke
        func.batch = adapter.batch
        func.abatch = adapter.abatch
        func.serve = adapter.serve
        func.app = adapter.app
        func.adapter = adapter
        func.config = config

        return func

    return decorator


def a2a_class(
    name: str,
    method_name: str = "invoke",
    description: str = "",
    port: int = 8000,
    host: str = "0.0.0.0",
    skills: Optional[List[AgentSkill]] = None,
    version: str = "1.0.0",
):
    """클래스를 A2A 에이전트로 변환."""

    def decorator(cls):
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)

            config = AgentConfig(
                name=name,
                description=description or cls.__doc__ or "",
                port=port,
                host=host,
                version=version,
                skills=skills
                or [
                    AgentSkill(
                        id="main",
                        name=name,
                        description=description or cls.__doc__ or f"{name} 기능",
                    )
                ],
            )

            adapter = LangGraphA2AAdapter.from_class(self, config, method_name)

            self.invoke = adapter.invoke
            self.ainvoke = adapter.ainvoke
            self.batch = adapter.batch
            self.abatch = adapter.abatch
            self.serve = adapter.serve
            self.app = adapter.app
            self.adapter = adapter
            self.config = config

        cls.__init__ = new_init
        return cls

    return decorator
