"""OpenCUA agent: markdown CoT sections with a pyautogui code block per step."""

from __future__ import annotations

from typing import Any

from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.client import image_part, text_part
from bench_eval.agents.core.history import StepMemory
from bench_eval.agents.core.images import encode_image
from bench_eval.agents.opencua import parser, prompts


class OpenCUAAgent(GUIAgent):
    def __init__(self, spec: Any, settings: Any, client: Any) -> None:
        super().__init__(spec, settings, client)
        self.memory = StepMemory(max_images=settings.history_n)
        self.cot_level = str(settings.option("cot_level", "l2"))
        self.history_type = str(settings.option("history_type", "thought_history"))
        self.system_prompt = prompts.build_system_prompt(self.cot_level)
        self.history_template = prompts.history_template(self.history_type)

    def reset(self) -> None:
        super().reset()
        self.memory.reset()

    def _history_block(self, index: int, step: Any) -> str:
        return prompts.STEP_TEMPLATE.format(step_num=index + 1) + self.history_template.format(
            observation=step.observation or "",
            thought=step.thought or "",
            action=step.action_description or "",
        )

    async def predict(self, instruction: str, observation: Observation) -> Prediction:
        # OpenCUA is trained on raw screenshots; the server applies its own resize.
        screenshot_b64 = encode_image(observation.screenshot)
        step = self.memory.start_step(image_base64=screenshot_b64)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt}
        ]

        finished = self.memory.steps[:-1]
        image_budget = max(self.settings.history_n, 0)
        text_only = finished[: max(len(finished) - image_budget, 0)]
        with_images = finished[max(len(finished) - image_budget, 0) :]

        if text_only:
            messages.append(
                {
                    "role": "assistant",
                    "content": "\n".join(
                        self._history_block(index, item)
                        for index, item in enumerate(text_only)
                    ),
                }
            )
        offset = len(text_only)
        for index, item in enumerate(with_images):
            if item.image_base64:
                messages.append(
                    {"role": "user", "content": [image_part(item.image_base64)]}
                )
            messages.append(
                {"role": "assistant", "content": self._history_block(offset + index, item)}
            )

        messages.append(
            {
                "role": "user",
                "content": [
                    image_part(screenshot_b64),
                    text_part(prompts.INSTRUCTION_TEMPLATE.format(instruction=instruction)),
                ],
            }
        )

        response = await self.client.chat(messages, sampling=self.settings.sampling())
        scaler = self.scaler(observation)
        sections = parser.parse_response(response.text, scaler)

        step.response = response.text
        step.observation = sections.observation
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
            metadata={
                "cot_level": self.cot_level,
                "history_type": self.history_type,
                "coordinate_space": self.settings.coordinate_space.value,
                **sections.as_metadata(),
            },
        )
