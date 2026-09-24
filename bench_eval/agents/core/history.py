"""Per-episode memory shared by the agent families.

All five families feed back the last N screenshots plus some textual record of
what they did; they differ only in how that record is rendered into messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MemoryStep:
    index: int
    image_base64: Optional[str] = None
    response: Optional[str] = None
    action_description: Optional[str] = None
    thought: Optional[str] = None
    observation: Optional[str] = None
    code: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class StepMemory:
    """Rolling window of steps with an image budget."""

    def __init__(self, max_images: int = 3) -> None:
        self.max_images = max(int(max_images), 0)
        self.steps: list[MemoryStep] = []

    def reset(self) -> None:
        self.steps.clear()

    def __len__(self) -> int:
        return len(self.steps)

    def start_step(self, image_base64: Optional[str] = None) -> MemoryStep:
        step = MemoryStep(index=len(self.steps), image_base64=image_base64)
        self.steps.append(step)
        return step

    @property
    def current(self) -> Optional[MemoryStep]:
        return self.steps[-1] if self.steps else None

    def recent(self, count: Optional[int] = None) -> list[MemoryStep]:
        """Last ``count`` steps (defaults to the image budget)."""
        limit = self.max_images if count is None else count
        if limit <= 0:
            return []
        return self.steps[-limit:]

    def previous(self, count: Optional[int] = None) -> list[MemoryStep]:
        """Completed steps only — excludes the step currently being predicted."""
        finished = self.steps[:-1]
        limit = self.max_images if count is None else count
        if limit <= 0 or not finished:
            return []
        return finished[-limit:]

    def action_log(
        self, *, limit: Optional[int] = None, exclude_recent: int = 0
    ) -> str:
        """Numbered plain-text list of past actions, or ``None`` when empty.

        ``exclude_recent`` drops the newest N steps, so a family that already
        replays those steps as screenshots can keep the text log complementary
        instead of describing the same steps twice.
        """
        finished = self.steps[:-1] if self.steps else []
        if exclude_recent > 0:
            finished = finished[:-exclude_recent] if exclude_recent < len(finished) else []
        if limit is not None:
            finished = finished[-limit:]
        lines = [
            f"Step {step.index + 1}: {step.action_description}"
            for step in finished
            if step.action_description
        ]
        return "\n".join(lines) if lines else "None"

    def image_history(self, count: Optional[int] = None) -> list[str]:
        return [
            step.image_base64
            for step in self.recent(count)
            if step.image_base64 is not None
        ]
