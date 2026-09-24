"""Qwen3-VL family registration.

Action space: `computer_use` tool calls inside `<tool_call>` tags.
Coordinates: absolute pixels of the smart-resized image (`resized`), or a
0..999 grid when ``GUI_AGENT_COORDINATE_SPACE=relative999``.
"""

from __future__ import annotations

from bench_eval.agents.core.actions import ActionSpace, ActionType
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.registry import ModelSpec, VLLMSpec, register

QWEN3_VL_ACTION_SPACE = ActionSpace(
    name="qwen3-vl/computer_use",
    supported=frozenset(
        {
            ActionType.CLICK,
            ActionType.DOUBLE_CLICK,
            ActionType.RIGHT_CLICK,
            ActionType.MIDDLE_CLICK,
            ActionType.MOVE,
            ActionType.DRAG,
            ActionType.TYPE,
            ActionType.KEY,
            ActionType.SCROLL,
            ActionType.WAIT,
            ActionType.TERMINATE,
            ActionType.ANSWER,
            ActionType.NOOP,
        }
    ),
    description="key/type/mouse_move/left_click/left_click_drag/right_click/"
    "middle_click/double_click/scroll/wait/terminate as JSON tool calls",
)

_AGENT = "bench_eval.agents.qwen3_vl.agent:Qwen3VLAgent"


def _spec(
    name: str,
    hf_repo: str,
    *,
    aliases: tuple[str, ...] = (),
    tensor_parallel_size: int = 1,
    max_model_len: int = 32768,
    min_gpus: int = 1,
    extra_args: tuple[str, ...] = (),
) -> ModelSpec:
    return ModelSpec(
        name=name,
        family="qwen3_vl",
        agent_ref=_AGENT,
        action_space=QWEN3_VL_ACTION_SPACE,
        coordinate_space=CoordinateSpace.RESIZED,
        aliases=aliases,
        temperature=0.0,
        top_p=0.9,
        max_tokens=2048,
        history_n=3,
        # Qwen3-VL uses a 32px patch grid (qwen2.5-VL used 28).
        resize_factor=32,
        max_pixels=16 * 16 * 4 * 12800,
        options={"coordinate_type": "absolute"},
        vllm=VLLMSpec(
            hf_repo=hf_repo,
            served_model_name=name,
            max_model_len=max_model_len,
            tensor_parallel_size=tensor_parallel_size,
            limit_mm_per_prompt={"image": 5},
            min_gpus=min_gpus,
            extra_args=extra_args,
        ),
        notes="Single-stage computer-use model; grounding and planning in one call.",
    )


QWEN3_VL_8B = register(
    _spec(
        "qwen3-vl-8b",
        "Qwen/Qwen3-VL-8B-Instruct",
        aliases=("qwen3vl", "qwen3-vl", "qwen3vl-8b"),
    )
)

QWEN3_VL_4B = register(
    _spec("qwen3-vl-4b", "Qwen/Qwen3-VL-4B-Instruct", aliases=("qwen3vl-4b",))
)

QWEN3_VL_32B = register(
    _spec(
        "qwen3-vl-32b",
        "Qwen/Qwen3-VL-32B-Instruct",
        aliases=("qwen3vl-32b",),
        tensor_parallel_size=2,
        min_gpus=2,
    )
)

QWEN3_VL_30B_A3B = register(
    _spec(
        "qwen3-vl-30b-a3b",
        "Qwen/Qwen3-VL-30B-A3B-Instruct",
        aliases=("qwen3vl-30b", "qwen3-vl-moe"),
        tensor_parallel_size=2,
        min_gpus=2,
    )
)

QWEN3_VL_235B_A22B = register(
    _spec(
        "qwen3-vl-235b-a22b",
        "Qwen/Qwen3-VL-235B-A22B-Instruct",
        aliases=("qwen3vl-235b",),
        tensor_parallel_size=8,
        min_gpus=8,
    )
)

__all__ = [
    "QWEN3_VL_ACTION_SPACE",
    "QWEN3_VL_4B",
    "QWEN3_VL_8B",
    "QWEN3_VL_30B_A3B",
    "QWEN3_VL_32B",
    "QWEN3_VL_235B_A22B",
]
