"""Model registry: the single place a new GUI model is declared.

Adding a model is one :func:`register` call — the benchmark harness, the vLLM
launcher, and the CLIs all read from here. Agent classes are referenced as
``"module:attr"`` strings so importing the registry never imports torch/PIL/
playwright transitively.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Optional

from bench_eval.agents.core.actions import ActionSpace
from bench_eval.agents.core.coordinates import CoordinateSpace


@dataclass(frozen=True)
class VLLMSpec:
    """Everything needed to bring the model up with ``vllm serve``."""

    hf_repo: str
    #: ``--served-model-name``; this is what LLM_MODEL / GUI_AGENT_MODEL must match.
    served_model_name: str
    max_model_len: int = 32768
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.9
    limit_mm_per_prompt: dict[str, int] = field(default_factory=lambda: {"image": 5})
    trust_remote_code: bool = False
    dtype: str = "bfloat16"
    #: Raw extra flags appended verbatim (rope scaling, quantization, ...).
    extra_args: tuple[str, ...] = ()
    #: Minimum GPUs the checkpoint realistically needs; informational.
    min_gpus: int = 1

    def command(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8000,
        tensor_parallel_size: Optional[int] = None,
        max_model_len: Optional[int] = None,
        gpu_memory_utilization: Optional[float] = None,
        model_path: Optional[str] = None,
        extra_args: Iterable[str] = (),
    ) -> list[str]:
        """Build the ``vllm serve`` argv for this checkpoint."""
        import json

        argv = [
            "vllm",
            "serve",
            model_path or self.hf_repo,
            "--served-model-name",
            self.served_model_name,
            "--host",
            host,
            "--port",
            str(port),
            "--dtype",
            self.dtype,
            "--max-model-len",
            str(max_model_len or self.max_model_len),
            "--tensor-parallel-size",
            str(tensor_parallel_size or self.tensor_parallel_size),
            "--gpu-memory-utilization",
            str(gpu_memory_utilization or self.gpu_memory_utilization),
        ]
        if self.limit_mm_per_prompt:
            argv += ["--limit-mm-per-prompt", json.dumps(self.limit_mm_per_prompt)]
        if self.trust_remote_code:
            argv.append("--trust-remote-code")
        argv.extend(self.extra_args)
        argv.extend(extra_args)
        return argv


@dataclass(frozen=True)
class ModelSpec:
    """One benchmarkable GUI model."""

    name: str
    family: str
    #: ``"package.module:ClassName"`` implementing :class:`GUIAgent`.
    agent_ref: str
    action_space: ActionSpace
    coordinate_space: CoordinateSpace
    vllm: Optional[VLLMSpec] = None
    aliases: tuple[str, ...] = ()
    #: Default sampling / prompting knobs, overridable from env.
    temperature: float = 0.0
    top_p: float = 0.9
    max_tokens: int = 2048
    history_n: int = 3
    resize_factor: int = 28
    max_pixels: int = 14 * 14 * 4 * 1280
    min_pixels: int = 56 * 56
    #: Family-specific switches (cot level, prompt style, grounder endpoint...).
    options: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def load_agent_class(self) -> type:
        module_name, _, attr = self.agent_ref.partition(":")
        module = importlib.import_module(module_name)
        return getattr(module, attr)

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "family": self.family,
            "action_space": self.action_space.summary(),
            "coordinate_space": self.coordinate_space.value,
            "aliases": list(self.aliases),
            "hf_repo": self.vllm.hf_repo if self.vllm else None,
            "served_model_name": self.vllm.served_model_name if self.vllm else None,
            "options": dict(self.options),
            "notes": self.notes,
        }


_REGISTRY: dict[str, ModelSpec] = {}
_ALIASES: dict[str, str] = {}
#: First checkpoint registered for a family — what a bare family name resolves to.
_FAMILY_DEFAULTS: dict[str, str] = {}
_FAMILY_MODULES: dict[str, str] = {
    "qwen3_vl": "bench_eval.agents.qwen3_vl",
    "uitars": "bench_eval.agents.uitars",
    "jedi": "bench_eval.agents.jedi",
    "opencua": "bench_eval.agents.opencua",
    "evocua": "bench_eval.agents.evocua",
    "fara": "bench_eval.agents.fara",
}
_loaded = False


def _key(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def register(spec: ModelSpec, *, override: bool = False) -> ModelSpec:
    """Add a model to the registry (idempotent for re-imported modules)."""
    key = _key(spec.name)
    if key in _REGISTRY and not override and _REGISTRY[key] != spec:
        raise ValueError(f"Model {spec.name!r} is already registered")
    _REGISTRY[key] = spec
    _ALIASES[key] = key
    for alias in spec.aliases:
        _ALIASES[_key(alias)] = key
    _FAMILY_DEFAULTS.setdefault(_key(spec.family), key)
    return spec


def load_builtin_families() -> None:
    """Import every family package so its ``register`` calls run."""
    global _loaded
    if _loaded:
        return
    _loaded = True
    for module_name in _FAMILY_MODULES.values():
        importlib.import_module(module_name)


def resolve(name: str) -> ModelSpec:
    """Look up a model by name, alias, or family (family → its default model)."""
    load_builtin_families()
    key = _ALIASES.get(_key(name))
    if key is not None:
        return _REGISTRY[key]

    default_key = _FAMILY_DEFAULTS.get(_key(name))
    if default_key is not None:
        # A bare family name selects that family's default checkpoint.
        return _REGISTRY[default_key]

    known = ", ".join(sorted(_REGISTRY)) or "<empty>"
    raise KeyError(f"Unknown GUI model {name!r}. Registered: {known}")


def list_models() -> tuple[ModelSpec, ...]:
    load_builtin_families()
    return tuple(_REGISTRY[key] for key in sorted(_REGISTRY))


def list_families() -> tuple[str, ...]:
    load_builtin_families()
    return tuple(sorted({spec.family for spec in _REGISTRY.values()}))


def models_for_family(family: str) -> tuple[ModelSpec, ...]:
    load_builtin_families()
    return tuple(
        spec for spec in list_models() if _key(spec.family) == _key(family)
    )


def derive(spec: ModelSpec, **changes: Any) -> ModelSpec:
    """Copy a spec with overrides — handy for registering sibling checkpoints."""
    return replace(spec, **changes)
