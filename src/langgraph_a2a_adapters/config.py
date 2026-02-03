"""A2A 설정 클래스."""

from dataclasses import dataclass, field
from typing import List, Optional

from a2a.types import (
    AgentCapabilities as A2AAgentCapabilities,
    AgentCard as A2AAgentCard,
    AgentSkill as A2AAgentSkill,
)


@dataclass
class AgentSkill:
    """에이전트 스킬."""

    id: str
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    input_modes: List[str] = field(default_factory=lambda: ["text/plain"])
    output_modes: List[str] = field(default_factory=lambda: ["text/plain"])

    def to_sdk(self) -> A2AAgentSkill:
        return A2AAgentSkill(
            id=self.id,
            name=self.name,
            description=self.description,
            tags=self.tags,
            examples=self.examples if self.examples else None,
            inputModes=self.input_modes if self.input_modes else None,
            outputModes=self.output_modes if self.output_modes else None,
        )


@dataclass
class AgentCapabilities:
    """에이전트 기능."""

    streaming: bool = True
    push_notifications: bool = False
    state_transition_history: bool = False

    def to_sdk(self) -> A2AAgentCapabilities:
        return A2AAgentCapabilities(
            streaming=self.streaming,
            pushNotifications=self.push_notifications,
            stateTransitionHistory=self.state_transition_history,
        )


@dataclass
class AgentConfig:
    """에이전트 설정."""

    name: str
    description: str = ""
    version: str = "1.0.0"
    port: int = 8000
    host: str = "0.0.0.0"
    url: Optional[str] = None
    skills: List[AgentSkill] = field(default_factory=list)
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    default_input_modes: List[str] = field(default_factory=lambda: ["text/plain"])
    default_output_modes: List[str] = field(default_factory=lambda: ["text/plain"])

    def __post_init__(self):
        if not self.skills:
            self.skills = [
                AgentSkill(
                    id="default",
                    name=self.name,
                    description=self.description or f"{self.name} 기본 스킬",
                )
            ]

    def get_url(self) -> str:
        return self.url or f"http://localhost:{self.port}"

    def to_agent_card(self) -> A2AAgentCard:
        return A2AAgentCard(
            name=self.name,
            description=self.description,
            url=self.get_url(),
            version=self.version,
            capabilities=self.capabilities.to_sdk(),
            defaultInputModes=self.default_input_modes,
            defaultOutputModes=self.default_output_modes,
            skills=[skill.to_sdk() for skill in self.skills],
        )
