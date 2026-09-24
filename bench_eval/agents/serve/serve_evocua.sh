#!/usr/bin/env bash
# Serve a evocua checkpoint with vLLM.
#
# Two prompt styles: S2 (tool calls, default) and S1 (pyautogui) via EVOCUA_PROMPT_STYLE. Verify the checkpoint id / pass MODEL_PATH.
#
#   ./serve_evocua.sh                       # default: evocua-s2
#   MODEL=<name> PORT=8001 TP=2 ./serve_evocua.sh
#
# Registered checkpoints: python -m bench_eval.agents.cli.models --family evocua

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

serve_model "evocua-s2" "$@"
