"""Unit tests for unified bench config validation (bench_eval.bench_verify)."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from bench_eval.bench_verify import (
    BENCH_REGISTRY_PATH,
    BENCH_TESTS_DIR,
    build_test_configs,
    collect_view_types,
    is_bench_view_type,
    load_registry_routes,
    merge,
    validate_all_configs,
    validate_config,
    verify_tracks_via_api,
)

import sys

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from ui_pattern_task_map import canonical_task_count  # noqa: E402

EXPECTED_TASK_COUNT = canonical_task_count()


class TestMerge:
    def test_deep_merge_nested_dicts(self):
        base = {"a": {"x": 1, "y": 2}, "b": 1}
        update = {"a": {"y": 3, "z": 4}}
        assert merge(base, update) == {"a": {"x": 1, "y": 3, "z": 4}, "b": 1}

    def test_merge_does_not_mutate_inputs(self):
        base = {"test_data": {"a": 1}}
        update = {"test_data": {"b": 2}}
        result = merge(base, update)
        assert base == {"test_data": {"a": 1}}
        assert result["test_data"] == {"a": 1, "b": 2}


class TestIsBenchViewType:
    @pytest.mark.parametrize(
        "view_type,expected",
        [
            ("bench_hub", True),
            ("bench_main", True),
            ("bench_catalog_main", True),
            ("bench_grocery_basket", True),
            ("bench_grocery_category", True),
            ("catalog_main", False),
            ("legacy_basket", False),
        ],
    )
    def test_prefix_rules(self, view_type: str, expected: bool):
        assert is_bench_view_type(view_type) is expected


class TestCollectViewTypes:
    def test_collects_view_type_and_to_view_type(self):
        cfg = {
            "state_a": {"view_type": "bench_hub"},
            "actions": [{"to_view_type": "bench_catalog_main"}],
        }
        assert collect_view_types(cfg) == {"bench_hub", "bench_catalog_main"}


class TestRegistry:
    def test_registry_file_exists(self):
        assert BENCH_REGISTRY_PATH.is_file()

    def test_registry_has_expected_routes(self):
        routes = load_registry_routes()
        assert "bench_hub" in routes
        assert "bench_catalog_main" in routes
        assert "bench_grocery_basket" in routes
        assert "bench_main" in routes


class TestBenchConfigs:
    @pytest.fixture(scope="module")
    def merged_configs(self) -> dict[str, dict]:
        return build_test_configs(BENCH_TESTS_DIR)

    @pytest.fixture(scope="module")
    def registry(self) -> set[str]:
        return load_registry_routes()

    def test_task_count(self, merged_configs: dict[str, dict]):
        assert len(merged_configs) == EXPECTED_TASK_COUNT

    def test_base_config_flags(self):
        base = json.loads((BENCH_TESTS_DIR / "config.json").read_text(encoding="utf-8"))
        td = base["test_data"]
        assert td.get("unified_bench") is True
        assert td.get("bench_anonymized") is True
        assert "domain_configs" in base
        assert "bench_sections" in base

    def test_no_validation_errors(self, merged_configs: dict[str, dict], registry: set[str]):
        errors = validate_all_configs(merged_configs, registry)
        assert errors == [], "\n".join(errors)

    def test_each_task_has_test_name(self, merged_configs: dict[str, dict]):
        for fname, cfg in merged_configs.items():
            assert cfg["test_data"].get("test_name"), fname

    @pytest.mark.parametrize(
        "fname",
        sorted(p.name for p in (BENCH_TESTS_DIR / "tasks").glob("*.json")),
    )
    def test_task_config_valid(self, fname: str, registry: set[str]):
        configs = build_test_configs(BENCH_TESTS_DIR)
        errors = validate_config(fname, configs[fname], registry)
        assert errors == [], "\n".join(errors)


def _backend_reachable(host: str = "localhost", port: int | None = None, timeout: float = 0.5) -> bool:
    import os
    if port is None:
        addr = os.environ.get("BENCH_API_ADDRESS", os.environ.get("EVAL_API_ADDRESS", "localhost:9000"))
        port = int(addr.rsplit(":", 1)[-1]) if ":" in addr else 9000
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.mark.integration
@pytest.mark.skipif(
    not _backend_reachable(),
    reason="WebPageBench backend not running on localhost:9000",
)
class TestBenchApi:
    def test_sample_tracks_store_config(self):
        import os

        api_address = os.environ.get(
            "BENCH_API_ADDRESS",
            os.environ.get("EVAL_API_ADDRESS", "localhost:9000"),
        )
        configs = build_test_configs(BENCH_TESTS_DIR)
        errors = verify_tracks_via_api(configs, sample_size=3, address=api_address)
        assert errors == [], "\n".join(errors)
