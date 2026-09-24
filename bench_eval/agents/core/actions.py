"""Canonical action IR shared by every GUI model family.

Each family (qwen3_vl, uitars, jedi, opencua, evocua) speaks a different dialect:
tool calls, a DSL, or pyautogui code. Family parsers translate their dialect into
:class:`Action` objects, and a single executor plays them back in the browser.
Adding a family therefore means writing a parser, not a new executor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ActionType(str, Enum):
    """Every primitive the browser executor knows how to perform."""

    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    TRIPLE_CLICK = "triple_click"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    MOVE = "move"
    DRAG = "drag"
    TYPE = "type"
    KEY = "key"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"
    TERMINATE = "terminate"
    ANSWER = "answer"
    CALL_USER = "call_user"
    FAIL = "fail"
    NOOP = "noop"


#: Action types that carry a screen coordinate.
POINTER_ACTIONS = frozenset(
    {
        ActionType.CLICK,
        ActionType.DOUBLE_CLICK,
        ActionType.TRIPLE_CLICK,
        ActionType.RIGHT_CLICK,
        ActionType.MIDDLE_CLICK,
        ActionType.MOVE,
        ActionType.DRAG,
    }
)

#: Action types that end the episode.
TERMINAL_ACTIONS = frozenset(
    {
        ActionType.TERMINATE,
        ActionType.ANSWER,
        ActionType.FAIL,
        ActionType.CALL_USER,
    }
)

#: Degradations applied when a family emits an action the space does not declare.
_FALLBACKS: dict[ActionType, tuple[ActionType, ...]] = {
    ActionType.TRIPLE_CLICK: (ActionType.DOUBLE_CLICK, ActionType.CLICK),
    ActionType.MIDDLE_CLICK: (ActionType.CLICK,),
    ActionType.MOVE: (ActionType.NOOP,),
    ActionType.CALL_USER: (ActionType.TERMINATE,),
    ActionType.ANSWER: (ActionType.TERMINATE,),
    ActionType.NAVIGATE: (ActionType.NOOP,),
}


@dataclass
class Action:
    """One low-level UI action in screen pixels of the current observation."""

    type: ActionType
    x: Optional[float] = None
    y: Optional[float] = None
    to_x: Optional[float] = None
    to_y: Optional[float] = None
    text: Optional[str] = None
    keys: tuple[str, ...] = ()
    #: Wheel deltas in CSS pixels; positive dy scrolls the page down.
    scroll_dx: float = 0.0
    scroll_dy: float = 0.0
    seconds: Optional[float] = None
    status: Optional[str] = None
    url: Optional[str] = None
    raw: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.type in TERMINAL_ACTIONS

    @property
    def is_success(self) -> bool:
        """True when the model terminated claiming the task is done."""
        if self.type == ActionType.ANSWER:
            return True
        if self.type != ActionType.TERMINATE:
            return False
        return (self.status or "success").lower().startswith("success")

    def describe(self) -> str:
        if self.type in POINTER_ACTIONS and self.x is not None:
            if self.type == ActionType.DRAG and self.to_x is not None:
                return (
                    f"{self.type.value}({int(self.x)}, {int(self.y or 0)}"
                    f" -> {int(self.to_x)}, {int(self.to_y or 0)})"
                )
            return f"{self.type.value}({int(self.x)}, {int(self.y or 0)})"
        if self.type == ActionType.TYPE:
            preview = (self.text or "")[:60]
            return f"type({preview!r})"
        if self.type == ActionType.KEY:
            return f"key({'+'.join(self.keys)})"
        if self.type == ActionType.SCROLL:
            return f"scroll(dx={self.scroll_dx:.0f}, dy={self.scroll_dy:.0f})"
        if self.type == ActionType.WAIT:
            return f"wait({self.seconds or 0:.1f}s)"
        if self.type == ActionType.TERMINATE:
            return f"terminate({self.status or 'success'})"
        if self.type == ActionType.ANSWER:
            preview = (self.text or "")[:80]
            return f"answer({preview!r})"
        return self.type.value

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type.value}
        for key in ("x", "y", "to_x", "to_y", "text", "seconds", "status", "url", "raw"):
            value = getattr(self, key)
            if value not in (None, ""):
                payload[key] = value
        if self.keys:
            payload["keys"] = list(self.keys)
        if self.scroll_dx or self.scroll_dy:
            payload["scroll_dx"] = self.scroll_dx
            payload["scroll_dy"] = self.scroll_dy
        if self.metadata:
            payload["metadata"] = self.metadata
        payload["description"] = self.describe()
        return payload

    # -- constructors used by family parsers -------------------------------

    @classmethod
    def click(cls, x: float, y: float, **kwargs: Any) -> "Action":
        return cls(type=ActionType.CLICK, x=x, y=y, **kwargs)

    @classmethod
    def type_text(cls, text: str, **kwargs: Any) -> "Action":
        return cls(type=ActionType.TYPE, text=text, **kwargs)

    @classmethod
    def hotkey(cls, *keys: str, **kwargs: Any) -> "Action":
        return cls(type=ActionType.KEY, keys=tuple(keys), **kwargs)

    @classmethod
    def wait(cls, seconds: float = 3.0, **kwargs: Any) -> "Action":
        return cls(type=ActionType.WAIT, seconds=seconds, **kwargs)

    @classmethod
    def terminate(cls, status: str = "success", **kwargs: Any) -> "Action":
        return cls(type=ActionType.TERMINATE, status=status, **kwargs)

    @classmethod
    def fail(cls, reason: str = "", **kwargs: Any) -> "Action":
        return cls(type=ActionType.FAIL, text=reason or None, **kwargs)


@dataclass(frozen=True)
class ActionSpace:
    """Declared capabilities of one model family.

    ``coerce`` keeps the executor total: a family that never learned
    ``triple_click`` still produces something playable when it emits one.
    """

    name: str
    supported: frozenset[ActionType]
    description: str = ""

    def supports(self, action_type: ActionType) -> bool:
        return action_type in self.supported

    def coerce(self, action: Action) -> Action:
        if action.type in self.supported or action.type is ActionType.NOOP:
            return action
        for candidate in _FALLBACKS.get(action.type, ()):
            if candidate in self.supported or candidate is ActionType.NOOP:
                downgraded = Action(**{**action.__dict__, "type": candidate})
                downgraded.metadata = {
                    **action.metadata,
                    "coerced_from": action.type.value,
                    "action_space": self.name,
                }
                return downgraded
        return Action(
            type=ActionType.NOOP,
            raw=action.raw,
            metadata={
                **action.metadata,
                "unsupported": action.type.value,
                "action_space": self.name,
            },
        )

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "actions": sorted(item.value for item in self.supported),
            "description": self.description,
        }


#: Superset used by pyautogui-style families (opencua, evocua-S1, jedi planner).
PYAUTOGUI_ACTION_SPACE = ActionSpace(
    name="pyautogui",
    supported=frozenset(ActionType) - {ActionType.NAVIGATE, ActionType.CALL_USER},
    description="pyautogui code blocks plus computer.wait/terminate helpers",
)
