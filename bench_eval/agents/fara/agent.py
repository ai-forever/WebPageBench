"""Fara-1.5 agent: screenshot + `computer_use` tool call per step.

Раскладка сообщений повторяет `Fara15Agent` из референса: системный промпт,
первый ход пользователя несёт скриншот и текст задачи, каждый следующий — новый
скриншот и фиксированную фразу USER_MESSAGE. Ответы модели возвращаются в историю
как есть, чтобы она видела собственные рассуждения.
"""

from __future__ import annotations

from typing import Any

from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.client import image_part, text_part
from bench_eval.agents.core.history import StepMemory
from bench_eval.agents.core.images import process_screenshot
from bench_eval.agents.fara import parser, prompts


class FaraAgent(GUIAgent):
    """Один скриншот + история последних N ходов → один `computer_use` вызов."""

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

        # Разрешение в схеме инструмента — это сетка, в которой модель называет
        # координаты (display_size=FARA_DISPLAY_SIZE в референсе), а не размер
        # картинки. Поэтому 1000x1000, и обратный пересчёт делает NORM_1000.
        system_prompt = prompts.build_system_prompt(
            parser.DISPLAY_SIZE,
            parser.DISPLAY_SIZE,
            # Редакции отличаются базой в последнем абзаце идентичности; какая
            # именно — задаёт ModelSpec.options, см. bench_eval/agents/fara/__init__.py.
            # Читаем из settings, а не из spec: там options уже слиты с
            # GUI_AGENT_OPTIONS / FARA_BASE_MODEL.
            self.settings.option("base_model", prompts.DEFAULT_BASE_MODEL),
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": [text_part(system_prompt)]}
        ]

        # Окно истории: последние history_n ходов целиком (скриншот + ответ).
        #
        # Референс (Fara15Agent.maybe_remove_old_screenshots) устроен иначе — там
        # сохраняются ВСЕ ответы модели, а режутся только скриншоты. Эта версия была
        # реализована и замерена на полном бенчмарке 21.09.2026: 86/152 против 95/152
        # у окна (тест Макнемара p=0.081), плюс вдвое больше обрезаний по max_tokens
        # (19 против 9) из-за разросшегося промпта. Полную историю откатили по
        # результатам замера; если возвращать — сперва поднять max_tokens.
        previous_steps = self.memory.previous()
        for index, previous in enumerate(previous_steps):
            if previous.image_base64:
                content = [image_part(previous.image_base64)]
                # Задача едет только на самом старом воспроизводимом ходу — так же,
                # как первый ход собирается в референсе; повтор инструкции на каждом
                # ходу превращает прошлые ходы в новые запросы.
                content.append(
                    text_part(instruction if index == 0 else prompts.USER_MESSAGE)
                )
                messages.append({"role": "user", "content": content})
            if previous.response:
                messages.append(
                    {"role": "assistant", "content": [text_part(previous.response)]}
                )

        current_content = [image_part(image.base64_png)]
        current_content.append(
            text_part(instruction if not previous_steps else prompts.USER_MESSAGE)
        )
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
