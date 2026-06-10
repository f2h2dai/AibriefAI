from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aibrief.graph.state import AibriefState


class Agent(Protocol):
    name: str

    def run(self, state: AibriefState) -> AibriefState:
        ...


@dataclass
class AgentResult:
    agent: str
    summary: str
    count: int = 0
