"""UI variant profiles for bench taxonomy widgets (docs/UI_TAXONOMY.md)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from bench_eval.bench_verify import BENCH_TESTS_DIR, merge
from bench_eval.ui_variants import DOMAIN_WIDGETS, UI_VARIANT_SCHEMA, profile_taxonomy_classes, validate_ui_variants


CONFIGS_DIR = BENCH_TESTS_DIR / "configs"


def load_base_config() -> dict[str, Any]:
    return json.loads((BENCH_TESTS_DIR / "config.json").read_text(encoding="utf-8"))


def load_variant_overlay(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_variant_config(overlay: dict[str, Any], *, base: dict[str, Any] | None = None) -> dict[str, Any]:
    base_cfg = copy.deepcopy(base or load_base_config())
    return merge(base_cfg, overlay)


def list_variant_configs(configs_dir: Path | str | None = None) -> list[Path]:
    root = Path(configs_dir) if configs_dir else CONFIGS_DIR
    if not root.is_dir():
        return []
    return sorted(root.glob("*.json"))


def profile_domain_variants(profile: dict[str, Any], domain: str) -> dict[str, str]:
    return dict((profile.get("domain_configs") or {}).get(domain, {}).get("ui_variants") or {})


def profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    """Human-readable summary for docs and tests."""
    domains = {}
    for domain, cfg in (profile.get("domain_configs") or {}).items():
        variants = cfg.get("ui_variants") or {}
        if variants:
            domains[domain] = variants
    return {
        "profile_id": profile.get("profile_id", ""),
        "description": profile.get("description", ""),
        "domains": domains,
        "taxonomy_classes": profile_taxonomy_classes(profile),
    }
