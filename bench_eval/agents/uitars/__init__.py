"""UI-TARS family registration.

Action space: a compact DSL (`click(start_box='(x,y)')`, `type(content='')`, ...).
Coordinates differ by generation — UI-TARS 1.0/DPO (Qwen2-VL) predicts on a
0..1000 grid, UI-TARS-1.5 (Qwen2.5-VL) predicts absolute pixels of the
smart-resized image.
"""

from __future__ import annotations

from bench_eval.agents.core.actions import ActionSpace, ActionType
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.registry import ModelSpec, VLLMSpec, register

UITARS_ACTION_SPACE = ActionSpace(
    name="uitars/dsl",
    supported=frozenset(
        {
            ActionType.CLICK,
            ActionType.DOUBLE_CLICK,
            ActionType.RIGHT_CLICK,
            ActionType.MOVE,
            ActionType.DRAG,
            ActionType.TYPE,
            ActionType.KEY,
            ActionType.SCROLL,
            ActionType.WAIT,
            ActionType.TERMINATE,
            ActionType.CALL_USER,
            ActionType.NOOP,
        }
    ),
    description="click / left_double / right_single / drag / hotkey / type / "
    "scroll / wait / finished / call_user",
)

_AGENT = "bench_eval.agents.uitars.agent:UITarsAgent"


def _spec(
    name: str,
    hf_repo: str,
    *,
    coordinate_space: CoordinateSpace,
    aliases: tuple[str, ...] = (),
    tensor_parallel_size: int = 1,
    max_model_len: int = 32768,
    min_gpus: int = 1,
) -> ModelSpec:
    return ModelSpec(
        name=name,
        family="uitars",
        agent_ref=_AGENT,
        action_space=UITARS_ACTION_SPACE,
        coordinate_space=coordinate_space,
        aliases=aliases,
        # UI-TARS is served with a non-zero temperature in the reference setup.
        temperature=0.0,
        top_p=0.9,
        max_tokens=1024,
        history_n=5,
        resize_factor=28,
        max_pixels=16384 * 28 * 28,
        min_pixels=100 * 28 * 28,
        options={
            "language": "English",
            "use_thought": True,
            "allow_call_user": False,
        },
        vllm=VLLMSpec(
            hf_repo=hf_repo,
            served_model_name=name,
            max_model_len=max_model_len,
            tensor_parallel_size=tensor_parallel_size,
            limit_mm_per_prompt={"image": 6},
            min_gpus=min_gpus,
        ),
        notes="Native GUI agent: thought + one DSL action per step.",
    )


UITARS_15_7B = register(
    _spec(
        "uitars-1.5-7b",
        "ByteDance-Seed/UI-TARS-1.5-7B",
        coordinate_space=CoordinateSpace.RESIZED,
        aliases=("uitars", "ui-tars", "uitars15", "ui-tars-1.5-7b"),
    )
)

UITARS_7B_DPO = register(
    _spec(
        "uitars-7b-dpo",
        "bytedance-research/UI-TARS-7B-DPO",
        coordinate_space=CoordinateSpace.NORM_1000,
        aliases=("ui-tars-7b-dpo",),
    )
)

UITARS_72B_DPO = register(
    _spec(
        "uitars-72b-dpo",
        "bytedance-research/UI-TARS-72B-DPO",
        coordinate_space=CoordinateSpace.NORM_1000,
        aliases=("ui-tars-72b-dpo",),
        tensor_parallel_size=4,
        min_gpus=4,
    )
)

__all__ = [
    "UITARS_ACTION_SPACE",
    "UITARS_15_7B",
    "UITARS_72B_DPO",
    "UITARS_7B_DPO",
]
