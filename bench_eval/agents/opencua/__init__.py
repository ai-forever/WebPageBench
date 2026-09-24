"""OpenCUA family registration.

Action space: pyautogui code blocks plus `computer.wait` / `computer.triple_click`
/ `computer.terminate`. Coordinates: normalized 0..1 by default (``relative``);
the qwen2.5-VL grid (``qwen25``) is available via GUI_AGENT_COORDINATE_SPACE.
"""

from __future__ import annotations

from bench_eval.agents.core.actions import PYAUTOGUI_ACTION_SPACE
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.registry import ModelSpec, VLLMSpec, register

OPENCUA_ACTION_SPACE = PYAUTOGUI_ACTION_SPACE

_AGENT = "bench_eval.agents.opencua.agent:OpenCUAAgent"


def _spec(
    name: str,
    hf_repo: str,
    *,
    aliases: tuple[str, ...] = (),
    coordinate_space: CoordinateSpace = CoordinateSpace.NORM_1,
    tensor_parallel_size: int = 1,
    max_model_len: int = 32768,
    min_gpus: int = 1,
) -> ModelSpec:
    return ModelSpec(
        name=name,
        family="opencua",
        agent_ref=_AGENT,
        action_space=OPENCUA_ACTION_SPACE,
        coordinate_space=coordinate_space,
        aliases=aliases,
        temperature=0.0,
        top_p=0.9,
        max_tokens=1500,
        history_n=3,
        resize_factor=28,
        options={
            # l1 = action only, l2 = thought + action, l3 = observation + thought.
            "cot_level": "l2",
            "history_type": "thought_history",
        },
        vllm=VLLMSpec(
            hf_repo=hf_repo,
            served_model_name=name,
            max_model_len=max_model_len,
            tensor_parallel_size=tensor_parallel_size,
            limit_mm_per_prompt={"image": 5},
            # OpenCUA ships a custom modelling file.
            trust_remote_code=True,
            min_gpus=min_gpus,
        ),
        notes="CoT-level configurable (l1/l2/l3); emits pyautogui code blocks.",
    )


OPENCUA_7B = register(
    _spec("opencua-7b", "xlangai/OpenCUA-7B", aliases=("opencua",))
)

OPENCUA_32B = register(
    _spec(
        "opencua-32b",
        "xlangai/OpenCUA-32B",
        tensor_parallel_size=2,
        min_gpus=2,
    )
)

#: The 72B checkpoint predicts on the qwen2.5-VL grid rather than 0..1 floats.
OPENCUA_72B = register(
    _spec(
        "opencua-72b",
        "xlangai/OpenCUA-72B",
        coordinate_space=CoordinateSpace.QWEN25,
        tensor_parallel_size=4,
        min_gpus=4,
    )
)

__all__ = ["OPENCUA_ACTION_SPACE", "OPENCUA_32B", "OPENCUA_72B", "OPENCUA_7B"]
