#!/usr/bin/env bash
# Serve a jedi checkpoint with vLLM.
#
# Grounding specialist. Pair it with a planner: JEDI_PLANNER_MODEL / JEDI_PLANNER_BASE_URL.
#
#   ./serve_jedi.sh                       # default: jedi-7b
#   MODEL=<name> PORT=8001 TP=2 ./serve_jedi.sh
#
# Registered checkpoints: python -m bench_eval.agents.cli.models --family jedi

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

serve_model "jedi-7b" "$@"
