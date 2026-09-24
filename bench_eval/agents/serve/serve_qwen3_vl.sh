#!/usr/bin/env bash
# Serve a qwen3_vl checkpoint with vLLM.
#
# Single-stage computer-use model: tool calls with absolute coordinates on the resized image.
#
#   ./serve_qwen3_vl.sh                       # default: qwen3-vl-8b
#   MODEL=<name> PORT=8001 TP=2 ./serve_qwen3_vl.sh
#
# Registered checkpoints: python -m bench_eval.agents.cli.models --family qwen3_vl

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

serve_model "qwen3-vl-8b" "$@"
