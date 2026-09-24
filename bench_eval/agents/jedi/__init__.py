"""Jedi family registration (two-stage planner + grounder).

Action space: the planner writes one line of pyautogui per step with the target
described in a `#` comment; the Jedi VL grounder answers with a `computer_use`
tool call whose coordinate is absolute on the smart-resized image.

Set ``JEDI_PLANNER_MODEL`` (and optionally ``JEDI_PLANNER_BASE_URL`` /
``JEDI_PLANNER_API_KEY``) to plan with a different model than the grounder.
"""

from __future__ import annotations

from bench_eval.agents.core.actions import ActionSpace, ActionType
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.registry import ModelSpec, VLLMSpec, register

JEDI_ACTION_SPACE = ActionSpace(
    name="jedi/planner+grounder",
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
            ActionType.NOOP,
        }
    ),
    description="planner: one pyautogui line + `# target description`; "
    "grounder: computer_use tool call returning the coordinate",
)

_AGENT = "bench_eval.agents.jedi.agent:JediAgent"


def _spec(
    name: str,
    hf_repo: str,
    *,
    aliases: tuple[str, ...] = (),
    tensor_parallel_size: int = 1,
    max_model_len: int = 32768,
    min_gpus: int = 1,
) -> ModelSpec:
    return ModelSpec(
        name=name,
        family="jedi",
        agent_ref=_AGENT,
        action_space=JEDI_ACTION_SPACE,
        coordinate_space=CoordinateSpace.RESIZED,
        aliases=aliases,
        temperature=0.5,
        top_p=0.9,
        max_tokens=1500,
        history_n=5,
        resize_factor=28,
        # Jedi grounds on the 1080p-tuned budget from the reference implementation.
        max_pixels=2700 * 28 * 28,
        options={
            # Empty planner_model => plan with the Jedi checkpoint itself.
            "planner_model": "",
            "planner_base_url": "",
            "planner_api_key": "",
        },
        vllm=VLLMSpec(
            hf_repo=hf_repo,
            served_model_name=name,
            max_model_len=max_model_len,
            tensor_parallel_size=tensor_parallel_size,
            limit_mm_per_prompt={"image": 6},
            min_gpus=min_gpus,
        ),
        notes="Grounding specialist: pair it with a stronger planner for best results.",
    )


JEDI_7B = register(
    _spec("jedi-7b", "xlangai/Jedi-7B-1080p", aliases=("jedi", "jedi-7b-1080p"))
)

JEDI_3B = register(
    _spec("jedi-3b", "xlangai/Jedi-3B-1080p", aliases=("jedi-3b-1080p",))
)

__all__ = ["JEDI_3B", "JEDI_7B", "JEDI_ACTION_SPACE"]
