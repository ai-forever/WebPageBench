"""Unit tests for OpenManus harness configuration."""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.openmanus_config import load_openmanus_harness_config


def test_load_openmanus_harness_config_prefers_submodule_prompts():
    config = load_openmanus_harness_config("configs/openmanus.default.json")
    if os.path.isdir(os.path.join(_REPO_ROOT, "openmanus", "app")):
        assert config.prompt_source == "openmanus-submodule"
        assert "OpenManus" in config.extend_system_message
    else:
        assert config.integration_mode == "browser-use-manus-prompts"


def test_load_openmanus_harness_config_reads_default_file_fallback():
    config = load_openmanus_harness_config("configs/openmanus.default.json")
    assert config.integration_mode == "browser-use-manus-prompts"
    assert config.extend_system_message
