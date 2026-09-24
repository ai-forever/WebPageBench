"""Agent contract every GUI model family implements."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from bench_eval.agents.core.actions import Action
from bench_eval.agents.core.client import TokenLedger, VLMClient
from bench_eval.agents.core.coordinates import CoordinateScaler

if TYPE_CHECKING:  # pragma: no cover - typing only
    from bench_eval.agents.core.registry import ModelSpec
    from bench_eval.agents.core.settings import AgentSettings


@dataclass
class Observation:
    """What the agent sees at one step."""

    screenshot: bytes
    screen_width: int
    screen_height: int
    url: Optional[str] = None
    step_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def screen_size(self) -> tuple[int, int]:
        return self.screen_width, self.screen_height


@dataclass
class Prediction:
    """What the agent decided, already lowered into the canonical action IR."""

    actions: list[Action]
    raw_response: str = ""
    thought: Optional[str] = None
    action_description: Optional[str] = None
    #: Extra model calls (e.g. jedi grounder) worth keeping in the trajectory.
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "actions": [action.to_dict() for action in self.actions],
            "raw_response": self.raw_response,
        }
        for key in ("thought", "action_description", "error"):
            value = getattr(self, key)
            if value:
                payload[key] = value
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


class GUIAgent(abc.ABC):
    """Screenshot in, canonical actions out.

    Subclasses own their prompt format, their response parser, and their
    coordinate space. Everything downstream (executor, loop, harness, reports)
    is family-agnostic.
    """

    def __init__(
        self,
        spec: "ModelSpec",
        settings: "AgentSettings",
        client: VLMClient,
    ) -> None:
        self.spec = spec
        self.settings = settings
        self.client = client
        self.step_index = 0

    @property
    def ledger(self) -> TokenLedger:
        return self.client.ledger

    @property
    def name(self) -> str:
        return self.spec.name

    def scaler(self, observation: Observation) -> CoordinateScaler:
        return CoordinateScaler(
            space=self.settings.coordinate_space,
            screen_width=observation.screen_width,
            screen_height=observation.screen_height,
            smart_resize_factor=self.settings.resize_factor,
        )

    def reset(self) -> None:
        """Clear per-episode state. Called before every benchmark task."""
        self.step_index = 0

    @abc.abstractmethod
    async def predict(self, instruction: str, observation: Observation) -> Prediction:
        """Return the next actions for this observation."""

    async def close(self) -> None:
        await self.client.close()

    def coerce(self, actions: list[Action]) -> list[Action]:
        """Drop actions the family's declared space cannot express."""
        space = self.spec.action_space
        return [space.coerce(action) for action in actions]
