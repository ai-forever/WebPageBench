"""Jedi agent: a planner writes pyautogui, the Jedi VL grounder resolves targets.

The two stages can run on different endpoints — set ``JEDI_PLANNER_MODEL`` and
``JEDI_PLANNER_BASE_URL`` to plan with a large general model while grounding with
a small Jedi checkpoint, which is the configuration the Jedi papers report.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from bench_eval.agents.core.actions import Action, ActionType
from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.client import Endpoint, VLMClient, image_part, text_part
from bench_eval.agents.core.coordinates import CoordinateScaler, CoordinateSpace
from bench_eval.agents.core.history import StepMemory
from bench_eval.agents.core.images import encode_image, process_screenshot
from bench_eval.agents.core.parsers import call_to_action, extract_code_blocks, parse_calls
from bench_eval.agents.jedi import prompts
from bench_eval.agents.qwen3_vl.parser import extract_tool_calls

_OBSERVATION_RE = re.compile(r"Observation\s*:\s*(.*?)(?=\n\s*Thought\s*:|\Z)", re.DOTALL)
_THOUGHT_RE = re.compile(r"Thought\s*:\s*(.*?)(?=\n\s*```|\Z)", re.DOTALL)

_POINTER_FUNCS = {"click", "leftClick", "rightClick", "doubleClick", "middleClick", "moveTo", "dragTo"}


class JediAgent(GUIAgent):
    def __init__(self, spec: Any, settings: Any, client: Any) -> None:
        super().__init__(spec, settings, client)
        self.memory = StepMemory(max_images=settings.history_n)
        self.grounder = client
        self.planner, self.planner_model = self._build_planner(settings, client)

    def _build_planner(self, settings: Any, grounder: VLMClient) -> tuple[VLMClient, str]:
        """Planner defaults to the grounder endpoint unless JEDI_PLANNER_* is set."""
        planner_model = settings.option("planner_model")
        if not planner_model:
            return grounder, grounder.endpoint.model

        planner_base_url = settings.option("planner_base_url") or grounder.endpoint.base_url
        planner_api_key = settings.option("planner_api_key") or grounder.endpoint.api_key
        endpoint = Endpoint(
            model=str(planner_model),
            base_url=str(planner_base_url).rstrip("/"),
            api_key=str(planner_api_key),
            timeout=grounder.endpoint.timeout,
            max_retries=grounder.endpoint.max_retries,
        )
        # Share the ledger and the dumper so planner + grounder land in one
        # report and one set of call dumps.
        return (
            VLMClient(endpoint, ledger=grounder.ledger, dumper=grounder.dumper),
            endpoint.model,
        )

    def reset(self) -> None:
        super().reset()
        self.memory.reset()

    async def close(self) -> None:
        if self.planner is not self.grounder:
            await self.planner.close()
        await self.grounder.close()

    async def predict(self, instruction: str, observation: Observation) -> Prediction:
        screenshot_b64 = encode_image(observation.screenshot)
        step = self.memory.start_step(image_base64=screenshot_b64)

        plan = await self._plan(instruction, observation, screenshot_b64)
        code_blocks = extract_code_blocks(plan)
        code = code_blocks[-1] if code_blocks else ""

        actions, grounding = await self._ground(code, instruction, observation)

        step.response = plan
        step.observation = _match(_OBSERVATION_RE, plan)
        step.thought = _match(_THOUGHT_RE, plan)
        step.code = code
        step.action_description = _first_comment(code) or (actions[0].describe() if actions else None)
        self.step_index += 1

        return Prediction(
            actions=actions,
            raw_response=plan,
            thought=step.thought,
            action_description=step.action_description,
            error=None if actions else f"no action parsed from planner code: {code[:200]}",
            metadata={
                "planner_model": self.planner_model,
                "grounder_model": self.grounder.endpoint.model,
                "observation": step.observation,
                "code": code,
                "grounding": grounding,
            },
        )

    async def _plan(self, instruction: str, observation: Observation, screenshot_b64: str) -> str:
        system_prompt = prompts.build_planner_system_prompt(
            width=observation.screen_width,
            height=observation.screen_height,
            current_step=self.step_index + 1,
            max_steps=self.settings.max_steps,
        )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": [text_part(system_prompt)]},
            {
                "role": "user",
                "content": [text_part(prompts.PLANNER_TASK_TEMPLATE.format(instruction=instruction))],
            },
        ]
        for previous in self.memory.previous():
            if previous.image_base64:
                messages.append({"role": "user", "content": [image_part(previous.image_base64)]})
            if previous.response:
                messages.append({"role": "assistant", "content": previous.response})
        messages.append({"role": "user", "content": [image_part(screenshot_b64)]})

        response = await self.planner.chat(
            messages,
            sampling=self.settings.sampling(),
            model=self.planner_model,
        )
        return response.text

    async def _ground(
        self,
        code: str,
        instruction: str,
        observation: Observation,
    ) -> tuple[list[Action], list[dict[str, Any]]]:
        """Turn planner code into actions, resolving pointer targets with Jedi."""
        screen_scaler = CoordinateScaler(
            space=CoordinateSpace.SCREEN,
            screen_width=observation.screen_width,
            screen_height=observation.screen_height,
        )
        calls, sentinels = parse_calls(code)
        actions: list[Action] = []
        grounding: list[dict[str, Any]] = []

        for call in calls:
            action = call_to_action(call, screen_scaler)
            if action is None:
                continue
            if call.func.split(".")[-1] in _POINTER_FUNCS and call.comment:
                point = await self._locate(call.comment, observation)
                grounding.append(
                    {
                        "description": call.comment,
                        "call": call.source,
                        "point": list(point) if point else None,
                    }
                )
                if point is None:
                    # Grounding failed; a placeholder coordinate would click at random.
                    continue
                if action.type is ActionType.DRAG:
                    action.to_x, action.to_y = point
                else:
                    action.x, action.y = point
            actions.append(action)

        for sentinel in sentinels:
            if sentinel == "DONE":
                actions.append(Action.terminate("success", raw=sentinel))
            elif sentinel == "FAIL":
                actions.append(Action.terminate("failure", raw=sentinel))
            elif sentinel == "WAIT":
                actions.append(Action.wait(3.0, raw=sentinel))
        return actions, grounding

    async def _locate(self, description: str, observation: Observation) -> Optional[tuple[int, int]]:
        image = process_screenshot(
            observation.screenshot,
            factor=self.settings.resize_factor,
            min_pixels=self.settings.min_pixels,
            max_pixels=self.settings.max_pixels,
        )
        messages = [
            {
                "role": "system",
                "content": [
                    text_part(
                        prompts.build_grounder_system_prompt(
                            width=image.width, height=image.height
                        )
                    )
                ],
            },
            {
                "role": "user",
                "content": [image_part(image.base64_png), text_part("\n" + description)],
            },
        ]
        response = await self.grounder.chat(messages, sampling=self.settings.sampling())

        scaler = CoordinateScaler(
            space=CoordinateSpace.RESIZED,
            screen_width=observation.screen_width,
            screen_height=observation.screen_height,
            processed_width=image.width,
            processed_height=image.height,
        )
        for payload in extract_tool_calls(response.text):
            args = payload.get("arguments") or {}
            coordinate = args.get("coordinate") if isinstance(args, dict) else None
            if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 2:
                return scaler.to_screen(float(coordinate[0]), float(coordinate[1]))
        return None


def _match(pattern: re.Pattern[str], text: str) -> Optional[str]:
    match = pattern.search(text or "")
    return match.group(1).strip() if match else None


def _first_comment(code: str) -> Optional[str]:
    for line in (code or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None


__all__ = ["JediAgent"]
