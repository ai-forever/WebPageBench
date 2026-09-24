"""Build and supervise ``vllm serve`` commands for registered GUI models."""

from __future__ import annotations

import asyncio
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from bench_eval.agents.core.registry import ModelSpec, resolve

DEFAULT_PORT = 8000


@dataclass(frozen=True)
class ServePlan:
    """A concrete launch plan for one checkpoint."""

    spec: ModelSpec
    argv: list[str]
    host: str
    port: int
    base_url: str
    served_model_name: str

    def as_shell(self) -> str:
        return " ".join(shlex.quote(part) for part in self.argv)

    def env_exports(self) -> list[str]:
        """Env lines that point the bench at this server."""
        return [
            f"export GUI_AGENT_MODEL={shlex.quote(self.spec.name)}",
            f"export GUI_AGENT_SERVED_MODEL={shlex.quote(self.served_model_name)}",
            f"export GUI_AGENT_BASE_URL={shlex.quote(self.base_url)}",
            "export GUI_AGENT_API_KEY=EMPTY",
        ]


def build_serve_plan(
    model: str,
    *,
    host: str = "0.0.0.0",
    port: int = DEFAULT_PORT,
    tensor_parallel_size: Optional[int] = None,
    max_model_len: Optional[int] = None,
    gpu_memory_utilization: Optional[float] = None,
    model_path: Optional[str] = None,
    extra_args: Iterable[str] = (),
) -> ServePlan:
    spec = resolve(model)
    if spec.vllm is None:
        raise ValueError(
            f"Model {spec.name!r} has no vLLM spec (API-only model?); "
            "serve it yourself and set GUI_AGENT_BASE_URL."
        )
    argv = spec.vllm.command(
        host=host,
        port=port,
        tensor_parallel_size=tensor_parallel_size,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        model_path=model_path,
        extra_args=extra_args,
    )
    reachable_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return ServePlan(
        spec=spec,
        argv=argv,
        host=host,
        port=port,
        base_url=f"http://{reachable_host}:{port}/v1",
        served_model_name=spec.vllm.served_model_name,
    )


def launch(plan: ServePlan, *, env: Optional[dict[str, str]] = None) -> subprocess.Popen:
    """Start vLLM in a child process (the caller owns its lifetime)."""
    merged = {**os.environ, **(env or {})}
    return subprocess.Popen(plan.argv, env=merged)


async def wait_for_server(base_url: str, *, timeout: float = 1800.0, interval: float = 5.0) -> bool:
    """Poll ``/models`` until vLLM finishes loading weights."""
    import httpx

    deadline = asyncio.get_event_loop().time() + timeout
    url = base_url.rstrip("/") + "/models"
    async with httpx.AsyncClient(timeout=10.0) as client:
        while asyncio.get_event_loop().time() < deadline:
            try:
                response = await client.get(url, headers={"Authorization": "Bearer EMPTY"})
                if response.status_code < 400:
                    return True
            except Exception:  # noqa: BLE001 - server still booting
                pass
            await asyncio.sleep(interval)
    return False


async def probe_endpoint(
    base_url: str, api_key: str = "EMPTY", *, verify: Any = None
) -> list[str]:
    """Return the model ids a served endpoint advertises.

    vLLM answers with OpenAI's ``{"data": [{"id": ...}]}``; GigaHF answers with
    ``{"models": [{"name": ...}]}``, so both shapes are accepted.
    """
    import httpx

    from bench_eval.agents.core.client import PLATFORM_GIGAHF, resolve_platform
    from bench_eval.agents.core.gigahf import GigaHFClient, model_ids

    if verify is None:
        # Match the transport a real run would use for this host.
        platform = resolve_platform(None, base_url=base_url)
        verify = GigaHFClient.ssl_verify if platform == PLATFORM_GIGAHF else True

    url = base_url.rstrip("/") + "/models"
    async with httpx.AsyncClient(timeout=15.0, verify=verify) as client:
        response = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        response.raise_for_status()
        data = response.json()
    return model_ids(data)
