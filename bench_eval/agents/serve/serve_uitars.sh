#!/usr/bin/env bash
# Serve a uitars checkpoint with vLLM.
#
# Native GUI agent with its own DSL. 1.5 predicts absolute coords, the DPO checkpoints use a 0..1000 grid.
#
#   ./serve_uitars.sh                       # default: uitars-1.5-7b
#   MODEL=<name> PORT=8001 TP=2 ./serve_uitars.sh
#
# Registered checkpoints: python -m bench_eval.agents.cli.models --family uitars

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

serve_model "uitars-1.5-7b" "$@"
