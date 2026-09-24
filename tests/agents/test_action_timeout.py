"""A wedged browser call must cost a task, not the whole run.

Reproduces the hang that stopped a 152-task run: all four workers blocked
forever on one ``page.mouse.click`` (rail passenger stepper), because
``mouse.click`` takes no timeout and Playwright's own timeouts are enforced by
the Node driver, which a wedged CDP pipe never reaches.

    pytest tests/agents/test_action_timeout.py
"""

from __future__ import annotations

import asyncio

import pytest

from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.executor import BrowserComputer


class WedgedPage:
    """A page whose calls never return, like a CDP pipe that stopped answering."""

    def __init__(self) -> None:
        self.url = "http://127.0.0.1:5173/rail"
        self.calls = 0

    async def _never(self) -> None:
        self.calls += 1
        await asyncio.Event().wait()

    async def screenshot(self, **_kwargs) -> bytes:
        await self._never()

    class _Mouse:
        def __init__(self, page: "WedgedPage") -> None:
            self.page = page

        async def click(self, *_args, **_kwargs) -> None:
            await self.page._never()

    @property
    def mouse(self) -> "WedgedPage._Mouse":
        return WedgedPage._Mouse(self)


def wedged_computer(timeout: float = 0.05) -> BrowserComputer:
    computer = BrowserComputer(action_timeout=timeout, settle_seconds=0.0)
    computer._page = WedgedPage()
    return computer


def click(x: float = 843, y: float = 761) -> Action:
    return Action(type=ActionType.CLICK, x=x, y=y)


@pytest.mark.asyncio
async def test_a_wedged_click_fails_the_action_instead_of_hanging():
    computer = wedged_computer()
    result = await computer.execute(click())
    assert result.ok is False
    assert "TimeoutError" in (result.error or "")
    assert "wedged" in (result.error or "")


@pytest.mark.asyncio
async def test_a_wedged_screenshot_raises_instead_of_hanging():
    computer = wedged_computer()
    with pytest.raises(TimeoutError, match="screenshot"):
        await computer.screenshot()


@pytest.mark.asyncio
async def test_every_action_is_bounded_so_a_task_ends_on_max_failures():
    computer = wedged_computer()
    results = await computer.execute_all([click(), click(), click()])
    assert [r.ok for r in results] == [False, False, False]
    # Each one was actually attempted — the loop counts them toward max_failures.
    assert computer._page.calls == 3


@pytest.mark.asyncio
async def test_teardown_is_bounded_too():
    """A stuck page must not hang the worker on cleanup either."""

    class WedgedCloser:
        async def close(self) -> None:
            await asyncio.Event().wait()

        async def stop(self) -> None:
            await asyncio.Event().wait()

    computer = wedged_computer()
    computer._context = computer._browser = WedgedCloser()
    computer._playwright = WedgedCloser()
    await asyncio.wait_for(computer.close(), timeout=2.0)
    assert computer._page is None


@pytest.mark.asyncio
async def test_zero_timeout_disables_the_deadline():
    computer = BrowserComputer(action_timeout=0.0, settle_seconds=0.0)
    computer._page = WedgedPage()
    with pytest.raises(asyncio.TimeoutError):
        # No client-side deadline, so only the test's own bound stops it.
        await asyncio.wait_for(computer.screenshot(), timeout=0.05)
