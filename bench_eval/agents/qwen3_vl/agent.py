"""Qwen3-VL computer-use agent (single-stage, tool-call action space)."""

from __future__ import annotations

from typing import Any

from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.client import image_part, text_part
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.history import StepMemory
from bench_eval.agents.core.images import process_screenshot
from bench_eval.agents.qwen3_vl import parser, prompts


class Qwen3VLAgent(GUIAgent):
    """One screenshot + N previous turns → one `computer_use` tool call."""

    def __init__(self, spec: Any, settings: Any, client: Any) -> None:
        super().__init__(spec, settings, client)
        self.memory = StepMemory(max_images=settings.history_n)

    def reset(self) -> None:
        super().reset()
        self.memory.reset()

    async def predict(self, instruction: str, observation: Observation) -> Prediction:
        image = process_screenshot(
            observation.screenshot,
            factor=self.settings.resize_factor,
            min_pixels=self.settings.min_pixels,
            max_pixels=self.settings.max_pixels,
        )
        step = self.memory.start_step(image_base64=image.base64_png)

        absolute = self.settings.coordinate_space is CoordinateSpace.RESIZED
        system_prompt = prompts.build_system_prompt(
            width=image.width,
            height=image.height,
            absolute=absolute,
        )
        # Message layout mirrors the reference agent (OSWorld/mm_agents/qwen3vl_agent.py):
        # the recent steps are replayed as screenshot/reply turns, and only the steps
        # that fell out of that image window are described in the text log. The task
        # instruction rides on the oldest turn alone — repeating it on every turn makes
        # each past turn look like a fresh request and invites the model to answer it
        # the same way again.
        previous_steps = self.memory.previous()
        instruction_prompt = prompts.INSTRUCTION_PROMPT.format(
            instruction=instruction,
            previous_actions=self.memory.action_log(
                exclude_recent=self.settings.history_n
            ),
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": [text_part(system_prompt)]}
        ]
        for index, previous in enumerate(previous_steps):
            if previous.image_base64:
                content = [image_part(previous.image_base64)]
                if index == 0:
                    content.append(text_part(instruction_prompt))
                messages.append({"role": "user", "content": content})
            if previous.response:
                messages.append(
                    {"role": "assistant", "content": [text_part(previous.response)]}
                )

        current_content = [image_part(image.base64_png)]
        if not previous_steps:
            current_content.append(text_part(instruction_prompt))
        messages.append({"role": "user", "content": current_content})

        response = await self.client.chat(messages, sampling=self.settings.sampling())
        scaler = self.scaler(observation).with_processed(image.width, image.height)
        actions, description = parser.parse_response(response.text, scaler)

        step.response = response.text
        step.action_description = description
        self.step_index += 1

        return Prediction(
            actions=actions,
            raw_response=response.text,
            action_description=description,
            metadata={
                "processed_size": [image.width, image.height],
                "coordinate_space": self.settings.coordinate_space.value,
                "finish_reason": response.finish_reason,
            },
        )
