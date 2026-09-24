"""End-to-end agent loop test with a stubbed model endpoint and a stubbed browser.

Covers what the parser tests cannot: settings resolution, message construction,
the loop's termination rules, and the trajectory shape the bench report expects.
No GPU, no served model, no Chromium.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest

from bench_eval.agents.core.actions import ActionType
from bench_eval.agents.core.client import ChatResponse, VLMClient
from bench_eval.agents.core.executor import ActionResult
from bench_eval.agents.core.loop import run_agent_loop
from bench_eval.agents.core.settings import build_agent, build_settings

SCREEN = (1280, 720)


def png_bytes(size: tuple[int, int] = SCREEN) -> bytes:
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", size, (240, 240, 240)).save(buffer, format="PNG")
    return buffer.getvalue()


class StubComputer:
    """Records actions instead of driving Chromium."""

    def __init__(self) -> None:
        self.width, self.height = SCREEN
        self.url = "http://127.0.0.1:5173/track/state_hub/bench_hub"
        self.executed: list[Any] = []

    async def screenshot(self) -> bytes:
        return png_bytes()

    async def execute_all(self, actions):
        self.executed.extend(actions)
        return [ActionResult(action=action, ok=True) for action in actions]


class StubClient(VLMClient):
    """Replays canned responses in order, then repeats the last one."""

    def __init__(self, endpoint, responses: list[str]) -> None:
        super().__init__(endpoint)
        self.responses = responses
        self.calls: list[list[dict]] = []

    async def chat(self, messages, *, sampling=None, model=None) -> ChatResponse:
        self.calls.append(messages)
        index = min(len(self.calls) - 1, len(self.responses) - 1)
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "llm_calls": 1,
        }
        self.ledger.add(model or self.endpoint.model, usage)
        return ChatResponse(text=self.responses[index], usage=usage)

    async def close(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _endpoint_env(monkeypatch):
    monkeypatch.setenv("GUI_AGENT_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("GUI_AGENT_API_KEY", "EMPTY")
    monkeypatch.delenv("GUI_AGENT_MODEL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)


def make_agent(model: str, responses: list[str], **overrides):
    settings = build_settings(model, overrides={"max_steps": 5, **overrides})
    agent = build_agent(settings)
    agent.client = StubClient(settings.endpoint, responses)
    if hasattr(agent, "grounder"):
        agent.grounder = agent.client
        agent.planner = agent.client
    return agent, settings


@pytest.mark.asyncio
async def test_qwen3_vl_loop_clicks_then_terminates():
    responses = [
        "Action: Click the catalogue tile.\n"
        '<tool_call>{"name": "computer_use", "arguments": '
        '{"action": "left_click", "coordinate": [100, 100]}}</tool_call>',
        "Action: Task complete.\n"
        '<tool_call>{"name": "computer_use", "arguments": '
        '{"action": "terminate", "status": "success"}}</tool_call>',
    ]
    agent, settings = make_agent("qwen3-vl-8b", responses)
    computer = StubComputer()

    result = await run_agent_loop(agent, computer, "Открой каталог", settings=settings)

    assert result.is_done and result.status == "success"
    assert result.step_count == 2
    assert [a.type for a in computer.executed] == [ActionType.CLICK, ActionType.TERMINATE]
    assert result.token_usage["llm_calls"] == 2


@pytest.mark.asyncio
async def test_loop_stops_at_max_steps_when_the_model_never_finishes():
    response = (
        "Action: keep clicking\n"
        '<tool_call>{"name": "computer_use", "arguments": '
        '{"action": "left_click", "coordinate": [10, 10]}}</tool_call>'
    )
    agent, settings = make_agent("qwen3-vl-8b", [response], max_steps=3)
    computer = StubComputer()

    result = await run_agent_loop(agent, computer, "endless", settings=settings)

    assert not result.is_done
    assert result.status == "max_steps"
    assert result.step_count == 3


@pytest.mark.asyncio
async def test_loop_gives_up_after_repeated_unparsable_responses():
    agent, settings = make_agent(
        "qwen3-vl-8b", ["I cannot help with that."], max_steps=10, max_failures=2
    )
    computer = StubComputer()

    result = await run_agent_loop(agent, computer, "nonsense", settings=settings)

    assert result.status == "max_failures"
    assert computer.executed == []


@pytest.mark.asyncio
async def test_uitars_history_grows_with_screenshots_and_replies():
    responses = [
        "Thought: open it\nAction: click(start_box='<|box_start|>(500,500)<|box_end|>')",
        "Thought: done\nAction: finished(content='ok')",
    ]
    agent, settings = make_agent("uitars-1.5-7b", responses)
    computer = StubComputer()

    result = await run_agent_loop(agent, computer, "Открой книги", settings=settings)

    assert result.is_done
    # Second turn must carry the first screenshot and the first reply.
    second_call = agent.client.calls[1]
    assert any(message["role"] == "assistant" for message in second_call)
    assert sum(1 for m in second_call if m["role"] == "user") >= 2


@pytest.mark.asyncio
async def test_opencua_pyautogui_response_reaches_the_executor():
    responses = [
        "## Thought:\nI will click search.\n\n## Action:\nClick the search field.\n\n"
        "## Code:\n```python\npyautogui.click(x=0.5, y=0.5)\n```",
        "## Thought:\nDone.\n\n## Action:\nFinish.\n\n"
        "## Code:\n```python\ncomputer.terminate(status='success')\n```",
    ]
    agent, settings = make_agent("opencua-7b", responses)
    computer = StubComputer()

    result = await run_agent_loop(agent, computer, "Найди товар", settings=settings)

    assert result.is_done and result.status == "success"
    click = computer.executed[0]
    assert (click.type, click.x, click.y) == (ActionType.CLICK, 640, 360)


@pytest.mark.asyncio
async def test_jedi_grounds_the_planner_target():
    planner = (
        "Observation:\nThe hub page is shown.\n"
        "Thought:\nOpen the books section.\n"
        "```python\n# The 'Книги' tile in the hub grid\npyautogui.click(x=0, y=0)\n```"
    )
    grounder = (
        "Action: click the tile\n"
        '<tool_call>{"name": "computer_use", "arguments": '
        '{"action": "left_click", "coordinate": [200, 100]}}</tool_call>'
    )
    agent, settings = make_agent("jedi-7b", [planner, grounder])
    computer = StubComputer()

    prediction = await agent.predict("Открой книги", _observation())

    assert [a.type for a in prediction.actions] == [ActionType.CLICK]
    # The planner's placeholder (0, 0) must be replaced by the grounder's point.
    assert (prediction.actions[0].x, prediction.actions[0].y) != (0, 0)
    assert prediction.metadata["grounding"][0]["description"].startswith("The 'Книги' tile")


@pytest.mark.asyncio
async def test_evocua_s1_style_uses_the_pyautogui_parser(monkeypatch):
    monkeypatch.setenv("EVOCUA_PROMPT_STYLE", "S1")
    responses = [
        "## Thought:\nClick it.\n\n## Action:\nClick the button.\n\n"
        "## Code:\n```python\npyautogui.click(x=0.25, y=0.5)\n```"
    ]
    agent, settings = make_agent("evocua-s1", responses)

    prediction = await agent.predict("do it", _observation())

    assert prediction.metadata["prompt_style"] == "S1"
    assert (prediction.actions[0].x, prediction.actions[0].y) == (320, 360)


@pytest.mark.asyncio
async def test_trajectory_has_the_shape_the_bench_report_expects():
    responses = [
        "Action: done\n"
        '<tool_call>{"name": "computer_use", "arguments": '
        '{"action": "terminate", "status": "success"}}</tool_call>'
    ]
    agent, settings = make_agent("qwen3-vl-8b", responses)
    result = await run_agent_loop(agent, StubComputer(), "task", settings=settings)

    trajectory = result.trajectory(harness="qwen3-vl", metadata={"model": "qwen3-vl-8b"})
    assert set(trajectory) == {"steps", "summary", "harness", "metadata"}
    summary = trajectory["summary"]
    assert summary["step_count"] == 1
    assert summary["is_done"] is True
    assert summary["action_names"] == ["terminate"]
    step = trajectory["steps"][0]
    assert step["step"] == 1
    assert step["model_output"]["actions"][0]["type"] == "terminate"


def _observation():
    from bench_eval.agents.core.base import Observation

    return Observation(
        screenshot=png_bytes(),
        screen_width=SCREEN[0],
        screen_height=SCREEN[1],
        url="http://127.0.0.1:5173/track",
    )


# ----------------------------------------------- qwen3-vl context layout


@pytest.mark.asyncio
async def test_qwen3_vl_context_matches_the_reference_layout(monkeypatch):
    """Mirror OSWorld/mm_agents/qwen3vl_agent.py message assembly.

    The recent steps are replayed as screenshot/reply turns; only the steps that
    fell out of that window are described in the text log; the task instruction
    rides on the oldest turn alone. Repeating the instruction on every turn makes
    each past turn read as a fresh request and pushes the model into a loop.
    """
    monkeypatch.setenv("GUI_AGENT_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("GUI_AGENT_SERVED_MODEL", "Qwen3.6-27B")

    settings = build_settings("qwen3-vl-8b", overrides={"history_n": 3})
    client = StubClient(
        settings.endpoint,
        [
            "Action: step.\n<tool_call>\n"
            '{"name": "computer_use", "arguments": {"action": "left_click", '
            '"coordinate": [100, 100]}}\n</tool_call>'
        ],
    )
    from bench_eval.agents.core.base import Observation
    from bench_eval.agents.qwen3_vl.agent import Qwen3VLAgent

    agent = Qwen3VLAgent(settings.spec, settings, client)
    observation = Observation(screenshot=png_bytes(), screen_width=1280, screen_height=720)
    for _ in range(6):
        await agent.predict("Найди сыр и добавь в корзину", observation)

    messages = client.calls[-1]
    shape = [
        (m["role"], tuple(part["type"] for part in m["content"])) for m in messages
    ]
    assert shape == [
        ("system", ("text",)),
        ("user", ("image_url", "text")),  # instruction only on the oldest turn
        ("assistant", ("text",)),  # a content part list, not a bare string
        ("user", ("image_url",)),
        ("assistant", ("text",)),
        ("user", ("image_url",)),
        ("assistant", ("text",)),
        ("user", ("image_url",)),  # current observation carries no text
    ]

    logs = [
        part["text"]
        for m in messages
        for part in m["content"]
        if part["type"] == "text" and "Previous actions" in part["text"]
    ]
    assert len(logs) == 1
    steps_in_log = logs[0].split("Previous actions:")[1].strip()
    # Steps 3-5 are already present as screenshots; only 1-2 belong in the text.
    assert "Step 1:" in steps_in_log and "Step 2:" in steps_in_log
    assert "Step 3:" not in steps_in_log


def test_action_log_can_exclude_the_steps_shown_as_screenshots():
    from bench_eval.agents.core.history import StepMemory

    memory = StepMemory(max_images=3)
    for index in range(6):
        step = memory.start_step(image_base64="x")
        step.action_description = f"act{index + 1}"
    memory.start_step(image_base64="x")  # the step being predicted

    assert memory.action_log(exclude_recent=0).count("Step ") == 6
    assert memory.action_log(exclude_recent=3).count("Step ") == 3
    assert memory.action_log(exclude_recent=99) == "None"
