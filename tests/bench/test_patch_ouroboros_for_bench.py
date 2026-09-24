"""Tests for ouroboros submodule bench patch script."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_patch_module():
    path = _REPO_ROOT / "scripts" / "patch_ouroboros_for_bench.py"
    spec = importlib.util.spec_from_file_location("patch_ouroboros_for_bench", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_patch_ouroboros_repo_replaces_expensive_defaults(tmp_path):
    mod = _load_patch_module()
    repo_dir = tmp_path / "repo"
    config_dir = repo_dir / "ouroboros"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.py"
    config_path.write_text(
        "\n".join(
            [
                "SETTINGS_DEFAULTS = {",
                '    "OUROBOROS_MODEL": "google/gemini-3.5-flash",',
                '    "OUROBOROS_MODEL_FALLBACKS": "anthropic/claude-sonnet-4.6",',
                '    "OUROBOROS_MODEL_DEEP_SELF_REVIEW": "openai/gpt-5.5-pro",',
                '    "OUROBOROS_WEBSEARCH_MODEL": "gpt-5.2",',
                '    "OUROBOROS_REVIEW_MODELS": "openai/gpt-5.5,google/gemini-3.5-flash,anthropic/claude-opus-4.8",',
                '    "OUROBOROS_SCOPE_REVIEW_MODELS": "openai/gpt-5.5",',
                '    "OUROBOROS_SCOPE_REVIEW_MODEL": "openai/gpt-5.5",',
                "}",
            ]
        ),
        encoding="utf-8",
    )
    llm_path = config_dir / "llm.py"
    llm_path.write_text(
        "\n".join(
            [
                'DEFAULT_LIGHT_MODEL = "google/gemini-3.5-flash"',
                'return os.environ.get("OUROBOROS_MODEL", "google/gemini-3.5-flash")\n',
            ]
        ),
        encoding="utf-8",
    )
    consolidator_path = config_dir / "consolidator.py"
    consolidator_path.write_text(
        'CONSOLIDATION_MODEL = "google/gemini-3.5-flash"\n',
        encoding="utf-8",
    )

    changed = mod.patch_ouroboros_repo(repo_dir)
    assert len(changed) >= 3
    text = config_path.read_text(encoding="utf-8")
    assert "google/gemini-2.5-flash" in text
    assert "gemini-3.5-flash" not in text
    assert "claude-sonnet-4.6" not in text
    assert "gpt-5.5" not in text
    assert mod.MARKER in text
    llm_text = llm_path.read_text(encoding="utf-8")
    assert "gemini-3.5-flash" not in llm_text
    assert '"google/gemini-2.5-flash"' in llm_text
    consolidator_text = consolidator_path.read_text(encoding="utf-8")
    assert consolidator_text == (
        f'CONSOLIDATION_MODEL = "google/gemini-2.5-flash"  {mod.MARKER}\n'
    )
    namespace: dict[str, object] = {}
    exec(consolidator_text, namespace)
    assert namespace["CONSOLIDATION_MODEL"] == "google/gemini-2.5-flash"
    assert isinstance(namespace["CONSOLIDATION_MODEL"], str)


def test_patch_ouroboros_repo_repairs_broken_tuple_assignment(tmp_path):
    mod = _load_patch_module()
    repo_dir = tmp_path / "repo"
    config_dir = repo_dir / "ouroboros"
    config_dir.mkdir(parents=True)
    (config_dir / "config.py").write_text("SETTINGS_DEFAULTS = {}\n", encoding="utf-8")
    consolidator_path = config_dir / "consolidator.py"
    consolidator_path.write_text(
        f'CONSOLIDATION_MODEL = "google/gemini-2.5-flash",  {mod.MARKER}\n',
        encoding="utf-8",
    )

    changed = mod.patch_ouroboros_repo(repo_dir)
    assert str(consolidator_path) in changed
    text = consolidator_path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {}
    exec(text, namespace)
    assert namespace["CONSOLIDATION_MODEL"] == "google/gemini-2.5-flash"
    assert isinstance(namespace["CONSOLIDATION_MODEL"], str)


def test_validate_bench_safe_blocks_gemini_35_flash():
    import pytest

    from bench_eval.ouroboros_llm_sync import validate_bench_safe_ouroboros_models

    with pytest.raises(ValueError, match="Blocked model family"):
        validate_bench_safe_ouroboros_models(
            {"OUROBOROS_MODEL": "google/gemini-3.5-flash"},
            env={"EVAL_MOCK": "bench"},
        )
