"""List registered GUI models.

    python -m bench_eval.agents.cli.models
    python -m bench_eval.agents.cli.models --family uitars --json
"""

from __future__ import annotations

import argparse
import json
import sys

from bench_eval.agents.core.registry import list_families, list_models, models_for_family


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List registered GUI agent models")
    parser.add_argument("--family", help="Filter by family (qwen3_vl, uitars, jedi, opencua, evocua)")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args(argv)

    specs = models_for_family(args.family) if args.family else list_models()
    if not specs:
        print(f"No models registered for family {args.family!r}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([spec.summary() for spec in specs], indent=2, ensure_ascii=False))
        return 0

    print(f"Families: {', '.join(list_families())}\n")
    for spec in specs:
        vllm = spec.vllm
        print(f"{spec.name}")
        print(f"  family        : {spec.family}")
        print(f"  action space  : {spec.action_space.name}")
        print(f"  actions       : {', '.join(sorted(a.value for a in spec.action_space.supported))}")
        print(f"  coordinates   : {spec.coordinate_space.value}")
        if spec.aliases:
            print(f"  aliases       : {', '.join(spec.aliases)}")
        if vllm:
            print(f"  hf repo       : {vllm.hf_repo}")
            print(f"  served name   : {vllm.served_model_name}")
            print(f"  gpus (min)    : {vllm.min_gpus} (tp={vllm.tensor_parallel_size})")
        if spec.options:
            print(f"  options       : {json.dumps(spec.options, ensure_ascii=False)}")
        if spec.notes:
            print(f"  notes         : {spec.notes}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
