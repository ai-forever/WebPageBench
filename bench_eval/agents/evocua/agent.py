"""EvoCUA agent with two selectable prompt styles.

``prompt_style=S2`` (default) mirrors the Qwen3-VL tool-call format on the
smart-resized image; ``prompt_style=S1`` mirrors the OpenCUA markdown/pyautogui
format on raw screenshots with normalized coordinates. The two styles use
different coordinate spaces, so the setting also switches the scaler.
"""

from __future__ import annotations

from typing import Any

from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.client import image_part, text_part
from bench_eval.agents.core.coordinates import CoordinateScaler, CoordinateSpace
from bench_eval.agents.core.history import StepMemory
from bench_eval.agents.core.images import encode_image, process_screenshot
from bench_eval.agents.evocua import prompts
from bench_eval.agents.opencua import parser as opencua_parser
from bench_eval.agents.qwen3_vl import parser as tool_call_parser


class EvoCUAAgent(GUIAgent):
    def __init__(self, spec: Any, settings: Any, client: Any) -> None:
        super().__init__(spec, settings, client)
        self.memory = StepMemory(max_images=settings.history_n)
        self.prompt_style = str(settings.option("prompt_style", "S2")).upper()
        if self.prompt_style not in {"S1", "S2"}:
            raise ValueError(f"Unsupported EvoCUA prompt_style={self.prompt_style!r}")

    def reset(self) -> None:
        super().reset()
        self.memory.reset()

    async def predict(self, instruction: str, observation: Observation) -> Prediction:
        if self.prompt_style == "S1":
            return await self._predict_s1(instruction, observation)
        return await self._predict_s2(instruction, observation)

    # -- S1: markdown sections + pyautogui ---------------------------------

    async def _predict_s1(self, instruction: str, observation: Observation) -> Prediction:
        screenshot_b64 = encode_image(observation.screenshot)
        step = self.memory.start_step(image_base64=screenshot_b64)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompts.S1_SYSTEM_PROMPT}
        ]
        for index, previous in enumerate(self.memory.previous()):
            if previous.image_base64:
                messages.append(
                    {"role": "user", "content": [image_part(previous.image_base64)]}
                )
            messages.append(
                {
                    "role": "assistant",
                    "content": prompts.S1_STEP_TEMPLATE.format(step_num=index + 1)
                    + prompts.S1_HISTORY_TEMPLATE.format(
                        thought=previous.thought or "",
                        action=previous.action_description or "",
                    ),
                }
            )
        messages.append(
            {
                "role": "user",
                "content": [
                    image_part(screenshot_b64),
                    text_part(
                        prompts.S1_INSTRUCTION_TEMPLATE.format(instruction=instruction)
                    ),
                ],
            }
        )

        response = await self.client.chat(messages, sampling=self.settings.sampling())
        scaler = self._s1_scaler(observation)
        sections = opencua_parser.parse_response(response.text, scaler)

        step.response = response.text
        step.thought = sections.thought
        step.action_description = sections.action
        step.code = sections.code
        self.step_index += 1

        return Prediction(
            actions=sections.actions,
            raw_response=response.text,
            thought=sections.thought,
            action_description=sections.action,
            error=sections.error,
            metadata={"prompt_style": "S1", **sections.as_metadata()},
        )

    def _s1_scaler(self, observation: Observation) -> CoordinateScaler:
        # S1 was trained with normalized coordinates regardless of the S2 setting.
        space = self.settings.coordinate_space
        if space is CoordinateSpace.RESIZED:
            space = CoordinateSpace.NORM_1
        return CoordinateScaler(
            space=space,
            screen_width=observation.screen_width,
            screen_height=observation.screen_height,
            smart_resize_factor=self.settings.resize_factor,
        )

    # -- S2: computer_use tool calls ---------------------------------------

    async def _predict_s2(self, instruction: str, observation: Observation) -> Prediction:
        image = process_screenshot(
            observation.screenshot,
            factor=self.settings.resize_factor,
            min_pixels=self.settings.min_pixels,
            max_pixels=self.settings.max_pixels,
        )
        step = self.memory.start_step(image_base64=image.base64_png)

        absolute = self.settings.coordinate_space is CoordinateSpace.RESIZED
        system_prompt = prompts.build_s2_system_prompt(
            width=image.width,
            height=image.height,
            absolute=absolute,
        )
        instruction_prompt = prompts.S2_INSTRUCTION_TEMPLATE.format(
            instruction=instruction,
            previous_actions=self.memory.action_log(),
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": [text_part(system_prompt)]}
        ]
        for previous in self.memory.previous():
            if previous.image_base64:
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            image_part(previous.image_base64),
                            text_part(instruction_prompt),
                        ],
                    }
                )
            if previous.response:
                messages.append({"role": "assistant", "content": previous.response})
        messages.append(
            {
                "role": "user",
                "content": [image_part(image.base64_png), text_part(instruction_prompt)],
            }
        )

        response = await self.client.chat(messages, sampling=self.settings.sampling())
        scaler = self.scaler(observation).with_processed(image.width, image.height)
        actions, description = tool_call_parser.parse_response(response.text, scaler)

        step.response = response.text
        step.action_description = description
        self.step_index += 1

        return Prediction(
            actions=actions,
            raw_response=response.text,
            action_description=description,
            metadata={
                "prompt_style": "S2",
                "processed_size": [image.width, image.height],
                "coordinate_space": self.settings.coordinate_space.value,
                "finish_reason": response.finish_reason,
            },
        )
