"""Parse Fara-1.5 `computer_use` tool calls into canonical actions.

Формат тот же, что у Qwen3-VL (`<tool_call>` с JSON), поэтому извлечение блоков и
починку оборванного JSON переиспользуем у `qwen3_vl`. Отличается набор действий:
Fara добавляет `visit_url`, `history_back`, `web_search`, `read_page_answer_question`,
`pause_and_memorize_fact` и `ask_user_question`, а скролл задаёт в той же
нормализованной сетке 0..1000, что и координаты.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.coordinates import CoordinateScaler
from bench_eval.agents.qwen3_vl.parser import (
    _clean_keys,
    extract_action_description,
    extract_tool_calls,
)

#: Сетка, в которой модель называет координаты (FARA_DISPLAY_SIZE в референсе).
DISPLAY_SIZE = 1000

_POINTER_ACTIONS = {
    "left_click": ActionType.CLICK,
    "double_click": ActionType.DOUBLE_CLICK,
    "triple_click": ActionType.TRIPLE_CLICK,
    "right_click": ActionType.RIGHT_CLICK,
    "mouse_move": ActionType.MOVE,
    "left_click_drag": ActionType.DRAG,
}

#: Действия, которых на стенде нет: внешнего поиска и живого пользователя тут не
#: существует, а чтение страницы и запоминание факта ничего не делают с UI. Чтобы
#: шаг не пропадал впустую, они становятся NOOP, а текст остаётся в описании хода.
_INERT_ACTIONS = {
    "web_search",
    "read_page_answer_question",
    "pause_and_memorize_fact",
    "history_back",
}


def tool_call_to_action(
    payload: dict[str, Any], scaler: CoordinateScaler
) -> Optional[Action]:
    if payload.get("name") not in {"computer_use", None}:
        return None
    args = payload.get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return None
    if not isinstance(args, dict):
        return None
    name = str(args.get("action") or "").strip()
    raw = json.dumps(payload, ensure_ascii=False)

    if name in _POINTER_ACTIONS:
        action = Action(type=_POINTER_ACTIONS[name], raw=raw)
        coordinate = args.get("coordinate")
        if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 2:
            x, y = scaler.to_screen(float(coordinate[0]), float(coordinate[1]))
            if action.type is ActionType.DRAG:
                action.to_x, action.to_y = x, y
            else:
                action.x, action.y = x, y
        return action

    if name == "type":
        return Action.type_text(str(args.get("text") or ""), raw=raw)

    if name == "key":
        keys = _clean_keys(args.get("keys") or args.get("text"))
        return Action.hotkey(*keys, raw=raw) if keys else None

    if name in {"scroll", "hscroll"}:
        # Референс: pixels * viewport_size / DISPLAY_SIZE, положительное — вверх.
        # Наш исполнитель крутит колесо, и положительный dy листает вниз.
        pixels = float(args.get("pixels") or 0)
        action = Action(type=ActionType.SCROLL, raw=raw)
        if name == "hscroll":
            action.scroll_dx = -pixels * scaler.screen_width / DISPLAY_SIZE
        else:
            action.scroll_dy = -pixels * scaler.screen_height / DISPLAY_SIZE
        return action

    if name == "visit_url":
        url = str(args.get("url") or "").strip()
        if not url:
            return None
        return Action(type=ActionType.NAVIGATE, url=url, raw=raw)

    if name == "wait":
        return Action.wait(float(args.get("time") or 3.0), raw=raw)

    if name == "terminate":
        action = Action.terminate(status="success", raw=raw)
        answer = args.get("answer")
        if answer:
            action.text = str(answer)
        return action

    if name == "ask_user_question":
        # На стенде пользователя нет, ответа модель не дождётся. Референс в этом
        # месте останавливает эпизод (WAITING_FOR_USER) — у нас это CALL_USER,
        # который пространство действий при необходимости сведёт к terminate.
        return Action(
            type=ActionType.CALL_USER, text=str(args.get("question") or ""), raw=raw
        )

    if name in _INERT_ACTIONS:
        return Action(type=ActionType.NOOP, raw=raw)

    return None


def parse_response(
    response: str, scaler: CoordinateScaler
) -> tuple[list[Action], Optional[str]]:
    """Вернуть (действия, однострочное описание хода)."""
    actions = [
        action
        for action in (
            tool_call_to_action(payload, scaler)
            for payload in extract_tool_calls(response)
        )
        if action is not None
    ]
    description = extract_action_description(response)
    if not description and actions:
        description = actions[0].describe()
    return actions, description
