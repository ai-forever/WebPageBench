"""EvoCUA family registration.

Two action spaces in one family, selected by ``EVOCUA_PROMPT_STYLE``:
* ``S2`` (default) — `computer_use` tool calls, absolute coordinates on the
  smart-resized image, with `triple_click` / `key_down` / `key_up` added.
* ``S1`` — OpenCUA-style markdown sections with pyautogui code, normalized 0..1.
"""

from __future__ import annotations

from bench_eval.agents.core.actions import ActionSpace, ActionType
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.registry import ModelSpec, VLLMSpec, register

EVOCUA_ACTION_SPACE = ActionSpace(
    name="evocua/computer_use+pyautogui",
    supported=frozenset(
        {
            ActionType.CLICK,
            ActionType.DOUBLE_CLICK,
            ActionType.TRIPLE_CLICK,
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
            ActionType.FAIL,
            ActionType.NOOP,
        }
    ),
    description="S2: computer_use tool calls (+triple_click/key_down/key_up); "
    "S1: pyautogui code blocks with computer.wait/terminate",
)

_AGENT = "bench_eval.agents.evocua.agent:EvoCUAAgent"


def _spec(
    name: str,
    hf_repo: str,
    *,
    aliases: tuple[str, ...] = (),
    prompt_style: str = "S2",
    coordinate_space: CoordinateSpace = CoordinateSpace.RESIZED,
    tensor_parallel_size: int = 1,
    max_model_len: int = 32768,
    min_gpus: int = 1,
) -> ModelSpec:
    return ModelSpec(
        name=name,
        family="evocua",
        agent_ref=_AGENT,
        action_space=EVOCUA_ACTION_SPACE,
        coordinate_space=coordinate_space,
        aliases=aliases,
        temperature=0.0,
        top_p=0.9,
        max_tokens=4096,
        history_n=4,
        resize_factor=32,
        max_pixels=16 * 16 * 4 * 12800,
        options={"prompt_style": prompt_style},
        vllm=VLLMSpec(
            hf_repo=hf_repo,
            served_model_name=name,
            max_model_len=max_model_len,
            tensor_parallel_size=tensor_parallel_size,
            limit_mm_per_prompt={"image": 5},
            trust_remote_code=True,
            min_gpus=min_gpus,
        ),
        notes=(
            "Set EVOCUA_PROMPT_STYLE=S1 to switch to the pyautogui action space. "
            "The hf_repo below is a placeholder — confirm the checkpoint id and "
            "pass `--model-path` (or a local path) when serving."
        ),
    )


EVOCUA_S2 = register(
    _spec(
        "evocua-s2",
        "OpenGVLab/EvoCUA-S2",
        aliases=("evocua",),
        prompt_style="S2",
    )
)

EVOCUA_S1 = register(
    _spec(
        "evocua-s1",
        "OpenGVLab/EvoCUA-S1",
        prompt_style="S1",
        coordinate_space=CoordinateSpace.NORM_1,
    )
)

__all__ = ["EVOCUA_ACTION_SPACE", "EVOCUA_S1", "EVOCUA_S2"]
