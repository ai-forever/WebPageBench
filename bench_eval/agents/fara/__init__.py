"""Fara-1.5 family registration.

Microsoft Fara — браузерный CUA поверх Qwen3.5-9B: скриншот на вход, вызов
`computer_use` на выход. От `qwen3_vl` отличается тремя вещами: координаты в
нормализованной сетке 0..1000 (а не в пикселях resized-картинки), расширенный
набор действий (`visit_url`, `history_back`, `web_search`, `ask_user_question`
и другие) и собственный системный промпт с блоком «критических точек».
"""

from __future__ import annotations

from bench_eval.agents.core.actions import ActionSpace, ActionType
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.registry import ModelSpec, VLLMSpec, register

FARA_ACTION_SPACE = ActionSpace(
    name="fara/computer_use",
    supported=frozenset(
        {
            ActionType.CLICK,
            ActionType.DOUBLE_CLICK,
            ActionType.TRIPLE_CLICK,
            ActionType.RIGHT_CLICK,
            ActionType.MOVE,
            ActionType.DRAG,
            ActionType.TYPE,
            ActionType.KEY,
            ActionType.SCROLL,
            ActionType.WAIT,
            ActionType.NAVIGATE,
            ActionType.TERMINATE,
            ActionType.CALL_USER,
            ActionType.NOOP,
        }
    ),
    description=(
        "computer_use tool calls в сетке 0..1000; плюс visit_url, history_back, "
        "web_search, read_page_answer_question, pause_and_memorize_fact, "
        "ask_user_question"
    ),
)

_AGENT = "bench_eval.agents.fara.agent:FaraAgent"

FARA_1_5_9B = register(
    ModelSpec(
        name="fara-1.5-9b",
        family="fara",
        agent_ref=_AGENT,
        action_space=FARA_ACTION_SPACE,
        # Референс (src/fara/agents/coord_spaces.py): FARA_DISPLAY_SIZE = 1000,
        # координаты пересчитываются как x * viewport_w / 1000.
        coordinate_space=CoordinateSpace.NORM_1000,
        aliases=("fara", "fara-1.5"),
        # Fara15AgentConfig: temperature 0, max_n_images 3, min/max_pixels ниже;
        # smart_resize идёт с factor = PATCH_SIZE * MERGE_SIZE = 16 * 2.
        temperature=0.0,
        top_p=1.0,
        max_tokens=2048,
        history_n=3,
        resize_factor=32,
        min_pixels=3136,
        max_pixels=12845056,
        options={"base_model": "Qwen3.5-9B"},
        vllm=VLLMSpec(
            hf_repo="microsoft/Fara1.5-9B",
            served_model_name="fara-1.5-9b",
            max_model_len=32768,
            tensor_parallel_size=1,
            limit_mm_per_prompt={"image": 4},
            trust_remote_code=True,
            min_gpus=1,
        ),
        notes=(
            "Рекомендованный вьюпорт обучения — 1440x900; на стенде 1280x720, "
            "координаты нормализованы, так что пересчёт не страдает. Действия без "
            "смысла на стенде (web_search, read_page_answer_question, "
            "pause_and_memorize_fact, history_back) исполняются как no-op."
        ),
    )
)

FARA_1_5_27B = register(
    ModelSpec(
        name="fara-1.5-27b",
        family="fara",
        agent_ref=_AGENT,
        action_space=FARA_ACTION_SPACE,
        # Та же сетка 0..1000, что у 9B — проверено на живом чекпоинте.
        coordinate_space=CoordinateSpace.NORM_1000,
        aliases=("fara-27b", "fara-1.5-27b"),
        temperature=0.0,
        top_p=1.0,
        max_tokens=2048,
        history_n=3,
        resize_factor=32,
        min_pixels=3136,
        max_pixels=12845056,
        # Отдельной идентичности под 27B в microsoft/fara нет: IDENTITY_REGISTRY
        # знает только fara_qwen35 (9B) и fara_qwen3vl (8B). База взята по
        # соответствию размеру редакции.
        options={"base_model": "Qwen3.5-27B"},
        vllm=VLLMSpec(
            hf_repo="microsoft/Fara1.5-27B",
            served_model_name="fara-1.5-27b",
            max_model_len=262144,
            tensor_parallel_size=1,
            limit_mm_per_prompt={"image": 4},
            trust_remote_code=True,
            min_gpus=2,
        ),
        notes=(
            "Старшая редакция Fara-1.5. Формат действий и сетка координат те же, "
            "что у 9B; отличается только база в идентичности и размер контекста."
        ),
    )
)

__all__ = ["FARA_ACTION_SPACE", "FARA_1_5_9B", "FARA_1_5_27B"]
