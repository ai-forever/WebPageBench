#!/usr/bin/env bash
# Serve a opencua checkpoint with vLLM.
#
# pyautogui code blocks with CoT levels l1/l2/l3 (OPENCUA_COT_LEVEL). Needs --trust-remote-code (already in the spec).
#
#   ./serve_opencua.sh                       # default: opencua-7b
#   MODEL=<name> PORT=8001 TP=2 ./serve_opencua.sh
#
# Registered checkpoints: python -m bench_eval.agents.cli.models --family opencua

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

serve_model "opencua-7b" "$@"
