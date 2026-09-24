"""Print or run the ``vllm serve`` command for a registered GUI model.

    python -m bench_eval.agents.cli.serve qwen3-vl-8b --print
    python -m bench_eval.agents.cli.serve uitars-1.5-7b --port 8001 --tp 2
    python -m bench_eval.agents.cli.serve opencua-7b --model-path /data/OpenCUA-7B
    python -m bench_eval.agents.cli.serve --health http://127.0.0.1:8000/v1
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from bench_eval.agents.core.vllm import build_serve_plan, launch, probe_endpoint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="vLLM launcher for GUI agent models")
    parser.add_argument("model", nargs="?", help="Registered model name or alias")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--tp", type=int, dest="tensor_parallel_size", help="Tensor parallel size")
    parser.add_argument("--max-model-len", type=int)
    parser.add_argument("--gpu-memory-utilization", type=float)
    parser.add_argument("--model-path", help="Local checkpoint path instead of the HF repo")
    parser.add_argument("--print", action="store_true", help="Print the command instead of running it")
    parser.add_argument("--env", action="store_true", help="Print the matching bench env exports")
    parser.add_argument("--health", metavar="BASE_URL", help="Query /models of a running server and exit")
    parser.add_argument("--api-key", help="Bearer token for --health (default: $GUI_AGENT_API_KEY)")
    parser.epilog = "Unrecognized flags are forwarded to `vllm serve` unchanged."
    # Unknown flags belong to vllm, so they are forwarded rather than rejected.
    args, extra = parser.parse_known_args(argv)

    if args.health:
        # A hosted platform (GigaHF) needs the bearer token to answer /models.
        api_key = args.api_key or os.getenv("GUI_AGENT_API_KEY") or "EMPTY"
        try:
            ids = asyncio.run(probe_endpoint(args.health, api_key))
        except Exception as exc:  # noqa: BLE001 - CLI reports, does not raise
            print(f"unreachable: {exc}", file=sys.stderr)
            return 1
        print("\n".join(ids) or "<no models>")
        return 0

    if not args.model:
        parser.error("model is required unless --health is used")

    extra = [item for item in extra if item != "--"]
    plan = build_serve_plan(
        args.model,
        host=args.host,
        port=args.port,
        tensor_parallel_size=args.tensor_parallel_size,
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
        model_path=args.model_path,
        extra_args=extra,
    )

    if args.env:
        print("\n".join(plan.env_exports()))
        return 0

    if args.print:
        print(plan.as_shell())
        return 0

    print(f"[serve] {plan.as_shell()}", flush=True)
    print("[serve] point the bench at this server with:", flush=True)
    print("\n".join(f"  {line}" for line in plan.env_exports()), flush=True)
    try:
        process = launch(plan)
    except FileNotFoundError:
        print(
            "vllm not found in PATH — install it (pip install vllm) or use --print "
            "to get the command for another host.",
            file=sys.stderr,
        )
        return 127
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
