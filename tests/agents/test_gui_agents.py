"""Parser, registry and coordinate-mapping tests for the GUI agent families.

These run without a GPU, a served model, or a browser: every case feeds a
realistic raw model response through the family parser and asserts the canonical
action that comes out.

    pytest tests/agents/test_gui_agents.py
"""

from __future__ import annotations

import json

import pytest

from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.coordinates import CoordinateScaler, CoordinateSpace
from bench_eval.agents.core.executor import normalize_key
from bench_eval.agents.core.parsers import parse_pyautogui_code
from bench_eval.agents.core.registry import list_families, list_models, resolve
from bench_eval.agents.evocua import EVOCUA_ACTION_SPACE
from bench_eval.agents.opencua import parser as opencua_parser
from bench_eval.agents.qwen3_vl import parser as qwen_parser
from bench_eval.agents.uitars import parser as uitars_parser

SCREEN = (1280, 720)


def screen_scaler(space: CoordinateSpace = CoordinateSpace.SCREEN, **kwargs) -> CoordinateScaler:
    return CoordinateScaler(
        space=space, screen_width=SCREEN[0], screen_height=SCREEN[1], **kwargs
    )


# --------------------------------------------------------------- registry


def test_all_families_are_registered():
    assert set(list_families()) == {
        "qwen3_vl",
        "uitars",
        "jedi",
        "opencua",
        "evocua",
        "fara",
    }


@pytest.mark.parametrize(
    "name,expected",
    [
        ("qwen3_vl", "qwen3-vl-8b"),
        ("uitars", "uitars-1.5-7b"),
        ("jedi", "jedi-7b"),
        ("opencua", "opencua-7b"),
        ("evocua", "evocua-s2"),
        ("ui-tars", "uitars-1.5-7b"),
        ("qwen3vl", "qwen3-vl-8b"),
    ],
)
def test_family_and_alias_resolution(name, expected):
    assert resolve(name).name == expected


def test_every_spec_can_build_a_vllm_command():
    for spec in list_models():
        argv = spec.vllm.command(port=8000)
        assert argv[:2] == ["vllm", "serve"]
        assert spec.vllm.served_model_name in argv
        assert "--limit-mm-per-prompt" in argv


def test_unknown_model_raises():
    with pytest.raises(KeyError):
        resolve("not-a-model")


# ------------------------------------------------------------ coordinates


@pytest.mark.parametrize(
    "space,raw,expected",
    [
        (CoordinateSpace.SCREEN, (640, 360), (640, 360)),
        (CoordinateSpace.NORM_1, (0.5, 0.5), (640, 360)),
        (CoordinateSpace.NORM_999, (999, 999), (1279, 719)),
        (CoordinateSpace.NORM_1000, (500, 250), (640, 180)),
    ],
)
def test_coordinate_spaces_map_to_screen(space, raw, expected):
    assert screen_scaler(space).to_screen(*raw) == expected


def test_resized_space_rescales_from_processed_image():
    scaler = screen_scaler(CoordinateSpace.RESIZED).with_processed(640, 360)
    assert scaler.to_screen(320, 180) == (640, 360)


def test_coordinates_are_clamped_into_the_viewport():
    assert screen_scaler().to_screen(5000, -20) == (1279, 0)


# --------------------------------------------------------------- qwen3-vl


def test_qwen3_vl_tool_call_click():
    response = (
        "Action: Click the search field.\n"
        "<tool_call>\n"
        '{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [320, 180]}}\n'
        "</tool_call>"
    )
    scaler = screen_scaler(CoordinateSpace.RESIZED).with_processed(640, 360)
    actions, description = qwen_parser.parse_response(response, scaler)

    assert [a.type for a in actions] == [ActionType.CLICK]
    assert (actions[0].x, actions[0].y) == (640, 360)
    assert description == "Click the search field."


def test_qwen3_vl_type_key_and_terminate():
    response = "\n".join(
        [
            "Action: Type the query and submit.",
            "<tool_call>",
            json.dumps({"name": "computer_use", "arguments": {"action": "type", "text": "чайник"}}),
            "</tool_call>",
            "<tool_call>",
            json.dumps({"name": "computer_use", "arguments": {"action": "key", "keys": ["ctrl", "a"]}}),
            "</tool_call>",
            "<tool_call>",
            json.dumps(
                {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
            ),
            "</tool_call>",
        ]
    )
    actions, _ = qwen_parser.parse_response(response, screen_scaler())

    assert [a.type for a in actions] == [ActionType.TYPE, ActionType.KEY, ActionType.TERMINATE]
    assert actions[0].text == "чайник"
    assert actions[1].keys == ("ctrl", "a")
    assert actions[2].is_terminal and actions[2].is_success


def test_qwen3_vl_scroll_direction_matches_wheel_sign():
    response = (
        "<tool_call>"
        '{"name": "computer_use", "arguments": {"action": "scroll", "pixels": -300}}'
        "</tool_call>"
    )
    actions, _ = qwen_parser.parse_response(response, screen_scaler())
    # Negative `pixels` means scroll down, i.e. a positive wheel delta.
    assert actions[0].scroll_dy > 0


def test_qwen3_vl_key_up_is_dropped_to_a_noop():
    response = (
        "<tool_call>"
        '{"name": "computer_use", "arguments": {"action": "key_up", "keys": ["shift"]}}'
        "</tool_call>"
    )
    actions, _ = qwen_parser.parse_response(response, screen_scaler())
    assert actions[0].type is ActionType.NOOP


def test_qwen3_vl_accepts_the_mobile_use_tool_alias():
    # Qwen ships one schema under two names; some checkpoints emit the mobile one.
    response = (
        "<tool_call>"
        '{"name": "mobile_use", "arguments": {"action": "left_click", "coordinate": [320, 180]}}'
        "</tool_call>"
    )
    scaler = screen_scaler(CoordinateSpace.RESIZED).with_processed(640, 360)
    actions, _ = qwen_parser.parse_response(response, scaler)

    assert [a.type for a in actions] == [ActionType.CLICK]
    assert (actions[0].x, actions[0].y) == (640, 360)


def test_qwen3_vl_repairs_a_tool_call_missing_its_closing_brace():
    response = (
        "<tool_call>\n"
        '{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [320, 180]}'
        "\n</tool_call>"
    )
    scaler = screen_scaler(CoordinateSpace.RESIZED).with_processed(640, 360)
    actions, _ = qwen_parser.parse_response(response, scaler)

    assert [a.type for a in actions] == [ActionType.CLICK]
    assert (actions[0].x, actions[0].y) == (640, 360)


def test_qwen3_vl_flattens_a_doubly_nested_arguments_object():
    response = (
        "<tool_call>\n"
        '{"name": "computer_use", "arguments": {"action": "left_click", '
        '"arguments": {"coordinate": [320, 180]}}'
        "\n</tool_call>"
    )
    scaler = screen_scaler(CoordinateSpace.RESIZED).with_processed(640, 360)
    actions, _ = qwen_parser.parse_response(response, scaler)

    assert [a.type for a in actions] == [ActionType.CLICK]
    assert (actions[0].x, actions[0].y) == (640, 360)


def test_qwen3_vl_ignores_a_tool_call_that_is_not_repairable():
    response = "<tool_call>{\"name\": \"computer_use\", not json at all}</tool_call>"
    actions, _ = qwen_parser.parse_response(response, screen_scaler())
    assert actions == []


# ------------------------------------------------------------------ uitars


def test_uitars_click_with_thought():
    response = (
        "Thought: I need to open the catalogue first.\n"
        "Action: click(start_box='<|box_start|>(500,250)<|box_end|>')"
    )
    actions, thought, description = uitars_parser.parse_response(
        response, screen_scaler(CoordinateSpace.NORM_1000)
    )

    assert (actions[0].type, actions[0].x, actions[0].y) == (ActionType.CLICK, 640, 180)
    assert thought == "I need to open the catalogue first."
    assert description.startswith("click(")


def test_uitars_type_unescapes_and_submits():
    response = "Thought: search\nAction: type(content='чайник\\n')"
    actions, _, _ = uitars_parser.parse_response(response, screen_scaler(CoordinateSpace.NORM_1000))
    assert actions[0].type is ActionType.TYPE
    assert actions[0].text == "чайник\n"


def test_uitars_drag_carries_both_endpoints():
    response = (
        "Action: drag(start_box='<|box_start|>(100,100)<|box_end|>', "
        "end_box='<|box_start|>(900,500)<|box_end|>')"
    )
    actions, _, _ = uitars_parser.parse_response(response, screen_scaler(CoordinateSpace.NORM_1000))
    action = actions[0]
    assert action.type is ActionType.DRAG
    assert (action.x, action.y) == (128, 72)
    assert (action.to_x, action.to_y) == (1152, 360)


def test_uitars_scroll_and_finished():
    actions, _, _ = uitars_parser.parse_response(
        "Action: scroll(start_box='<|box_start|>(500,500)<|box_end|>', direction='down')",
        screen_scaler(CoordinateSpace.NORM_1000),
    )
    assert actions[0].scroll_dy > 0

    actions, _, _ = uitars_parser.parse_response(
        "Action: finished(content='Товар добавлен')", screen_scaler()
    )
    assert actions[0].is_terminal and actions[0].text == "Товар добавлен"


def test_uitars_multiple_actions_in_one_step():
    response = (
        "Thought: type and submit\n"
        "Action: click(start_box='<|box_start|>(500,250)<|box_end|>')\n\n"
        "type(content='книга')"
    )
    actions, _, _ = uitars_parser.parse_response(response, screen_scaler(CoordinateSpace.NORM_1000))
    assert [a.type for a in actions] == [ActionType.CLICK, ActionType.TYPE]


# ----------------------------------------------------------------- opencua


def test_opencua_sections_and_pyautogui_code():
    response = """## Thought:
I should open the search field.

## Action:
Click the search input at the top of the page.

## Code:
```python
pyautogui.click(x=0.5, y=0.25)
```"""
    sections = opencua_parser.parse_response(response, screen_scaler(CoordinateSpace.NORM_1))

    assert sections.thought.startswith("I should open")
    assert sections.action.startswith("Click the search input")
    assert [a.type for a in sections.actions] == [ActionType.CLICK]
    assert (sections.actions[0].x, sections.actions[0].y) == (640, 180)


def test_opencua_terminate_and_wait_helpers():
    done = opencua_parser.parse_response(
        "## Action:\nDone\n\n## Code:\n```python\ncomputer.terminate(status='success')\n```",
        screen_scaler(),
    )
    assert done.actions[0].is_terminal and done.actions[0].is_success

    failed = opencua_parser.parse_response(
        "## Action:\nGive up\n\n## Code:\n```python\ncomputer.terminate(status='failure')\n```",
        screen_scaler(),
    )
    assert failed.actions[0].is_terminal and not failed.actions[0].is_success

    waiting = opencua_parser.parse_response(
        "## Action:\nWait\n\n## Code:\n```python\ncomputer.wait()\n```", screen_scaler()
    )
    assert waiting.actions[0].type is ActionType.WAIT


def test_opencua_missing_code_block_is_reported():
    sections = opencua_parser.parse_response("## Action:\nClick something", screen_scaler())
    assert sections.actions == []
    assert "no code block" in sections.error


# -------------------------------------------------------- pyautogui parser


def test_pyautogui_write_press_and_hotkey():
    actions = parse_pyautogui_code(
        "pyautogui.write('hello')\npyautogui.press('enter')\npyautogui.hotkey('ctrl', 'c')",
        screen_scaler(),
    )
    assert [a.type for a in actions] == [ActionType.TYPE, ActionType.KEY, ActionType.KEY]
    assert actions[0].text == "hello"
    assert actions[1].keys == ("enter",)
    assert actions[2].keys == ("ctrl", "c")


def test_pyautogui_repeated_press_is_expanded():
    actions = parse_pyautogui_code("pyautogui.press('tab', presses=3)", screen_scaler())
    assert len(actions) == 3
    assert all(a.keys == ("tab",) for a in actions)


def test_pyautogui_click_variants():
    actions = parse_pyautogui_code(
        "pyautogui.click(x=10, y=20, button='right')\n"
        "pyautogui.doubleClick(x=30, y=40)\n"
        "pyautogui.click(x=50, y=60, clicks=2)",
        screen_scaler(),
    )
    assert [a.type for a in actions] == [
        ActionType.RIGHT_CLICK,
        ActionType.DOUBLE_CLICK,
        ActionType.DOUBLE_CLICK,
    ]


def test_pyautogui_scroll_sign_and_sentinels():
    down = parse_pyautogui_code("pyautogui.scroll(-3)", screen_scaler())
    assert down[0].scroll_dy > 0
    up = parse_pyautogui_code("pyautogui.scroll(3)", screen_scaler())
    assert up[0].scroll_dy < 0

    assert parse_pyautogui_code("DONE", screen_scaler())[0].is_success
    assert not parse_pyautogui_code("FAIL", screen_scaler())[0].is_success


def test_pyautogui_survives_a_broken_line():
    actions = parse_pyautogui_code(
        "pyautogui.click(x=10, y=20)\nthis is not python\n", screen_scaler()
    )
    assert [a.type for a in actions] == [ActionType.CLICK]


# ------------------------------------------------------------ action space


def test_unsupported_action_degrades_instead_of_crashing():
    space = resolve("uitars-1.5-7b").action_space
    coerced = space.coerce(Action(type=ActionType.TRIPLE_CLICK, x=1, y=2))
    # UI-TARS has no triple_click, so it falls back to the nearest supported click.
    assert coerced.type is ActionType.DOUBLE_CLICK
    assert coerced.metadata["coerced_from"] == "triple_click"


def test_supported_action_passes_through_untouched():
    action = Action.click(10, 20)
    assert EVOCUA_ACTION_SPACE.coerce(action) is action


# ---------------------------------------------------------------- executor


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ctrl", "Control"),
        ("cmd", "Meta"),
        ("enter", "Enter"),
        ("pagedown", "PageDown"),
        ("f5", "F5"),
        ("a", "a"),
    ],
)
def test_key_names_map_to_playwright(raw, expected):
    assert normalize_key(raw) == expected


# ---------------------------------------------------------------- fara editions


def test_fara_editions_differ_only_in_base_model():
    """Редакции 9B и 27B делят один промпт; меняется только база в идентичности."""
    from bench_eval.agents.fara import prompts

    nine = prompts.build_system_prompt(1000, 1000, "Qwen3.5-9B")
    twentyseven = prompts.build_system_prompt(1000, 1000, "Qwen3.5-27B")

    assert "Qwen3.5-9B" in nine
    assert "Qwen3.5-27B" in twentyseven
    assert nine.replace("Qwen3.5-9B", "X") == twentyseven.replace("Qwen3.5-27B", "X")


def test_fara_default_prompt_is_the_9b_edition():
    """Дефолт остаётся дословным промптом из microsoft/fara (identity fara_qwen35)."""
    from bench_eval.agents.fara import prompts

    assert prompts.build_system_prompt(1000, 1000) == prompts.build_system_prompt(
        1000, 1000, "Qwen3.5-9B"
    )
    assert "The screen's resolution is 1000x1000." in prompts.build_system_prompt(
        1000, 1000
    )


def test_both_fara_checkpoints_share_grid_and_action_space():
    from bench_eval.agents.core.registry import resolve

    nine = resolve("fara-1.5-9b")
    twentyseven = resolve("fara-1.5-27b")

    assert nine.coordinate_space is twentyseven.coordinate_space
    assert nine.action_space is twentyseven.action_space
    assert twentyseven.options["base_model"] == "Qwen3.5-27B"


def test_fara_history_is_a_window_not_full_log():
    """Окно последних history_n ходов — осознанный отход от референса.

    Референс сохраняет все ответы модели и режет только скриншоты. Эта версия
    замерена 21.09.2026 на полном бенчмарке и оказалась хуже (86/152 против
    95/152, p=0.081), поэтому оставлено окно. См. комментарий в fara/agent.py.
    """
    from bench_eval.agents.core.history import StepMemory

    memory = StepMemory(max_images=3)
    for i in range(12):
        step = memory.start_step(image_base64=f"img{i}")
        step.response = f"ответ шага {i}"
    # В запрос едут только последние 3 завершённых хода, а не все 11.
    assert len(memory.previous()) == 3
    assert [s.response for s in memory.previous()] == [
        "ответ шага 8",
        "ответ шага 9",
        "ответ шага 10",
    ]
