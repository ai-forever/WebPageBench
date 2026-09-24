"""UI-TARS agent: system prompt carries the task, user turns carry screenshots."""

from __future__ import annotations

from typing import Any

from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.client import image_part, text_part
from bench_eval.agents.core.history import StepMemory
from bench_eval.agents.core.images import process_screenshot
from bench_eval.agents.uitars import parser, prompts


class UITarsAgent(GUIAgent):
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

        prompt = prompts.build_prompt(
            instruction,
            language=str(self.settings.option("language", "English")),
            use_thought=bool(self.settings.option("use_thought", True)),
            allow_call_user=bool(self.settings.option("allow_call_user", False)),
        )

        # UI-TARS keeps the task in the first user turn and alternates
        # screenshot → assistant response for the rest of the episode.
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [text_part(prompt)]}
        ]
        for previous in self.memory.previous():
            if previous.image_base64:
                messages.append({"role": "user", "content": [image_part(previous.image_base64)]})
            if previous.response:
                messages.append({"role": "assistant", "content": previous.response})
        messages.append({"role": "user", "content": [image_part(image.base64_png)]})

        response = await self.client.chat(messages, sampling=self.settings.sampling())
        scaler = self.scaler(observation).with_processed(image.width, image.height)
        actions, thought, description = parser.parse_response(response.text, scaler)

        step.response = response.text
        step.thought = thought
        step.action_description = description
        self.step_index += 1

        return Prediction(
            actions=actions,
            raw_response=response.text,
            thought=thought,
            action_description=description,
            metadata={
                "processed_size": [image.width, image.height],
                "coordinate_space": self.settings.coordinate_space.value,
                "finish_reason": response.finish_reason,
            },
        )
