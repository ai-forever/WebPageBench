"""Validation helpers for unified bench configs (tests/bench)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from bench_eval.task_dates import apply_booking_dates

REPO_ROOT = Path(__file__).resolve().parents[1]

BENCH_TESTS_DIR = REPO_ROOT / "tests" / "bench"
BENCH_REGISTRY_PATH = REPO_ROOT / "site/frontend/src/views/bench/registry.js"

BENCH_VIEW_PREFIXES = (
    "bench_hub",
    "bench_catalog_",
    "bench_books_",
    "bench_grocery_",
    "bench_rail_",
    "bench_hotel_",
    "bench_files_",
)


def merge(base: dict, update: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def build_test_configs(tests_dir: Path | str) -> dict[str, dict]:
    tests_path = Path(tests_dir)
    mock_config = json.loads((tests_path / "config.json").read_text(encoding="utf-8"))
    mock_config.pop("extends", None)
    res: dict[str, dict] = {}
    for file in sorted((tests_path / "tasks").glob("*.json")):
        task = json.loads(file.read_text(encoding="utf-8"))
        merged = merge(mock_config, task)
        apply_booking_dates(merged)
        merged["test_data"]["test_name"] = file.stem
        res[file.name] = merged
    return res


def collect_view_types(obj, found: set[str] | None = None) -> set[str]:
    if found is None:
        found = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("view_type", "to_view_type") and isinstance(v, str):
                found.add(v)
            else:
                collect_view_types(v, found)
    elif isinstance(obj, list):
        for x in obj:
            collect_view_types(x, found)
    return found


def is_bench_view_type(vt: str) -> bool:
    if vt in ("bench_main", "bench_hub"):
        return True
    return any(vt.startswith(p) for p in BENCH_VIEW_PREFIXES)


def load_registry_routes(registry_path: Path | None = None) -> set[str]:
    registry = registry_path or BENCH_REGISTRY_PATH
    text = registry.read_text(encoding="utf-8")
    names: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("bench_") and ":" in line:
            names.add(line.split(":")[0].strip())
    names.add("bench_main")
    return names


def validate_config(fname: str, cfg: dict, registry: set[str]) -> list[str]:
    errors: list[str] = []
    vts = collect_view_types(cfg)
    for vt in vts:
        if not is_bench_view_type(vt):
            errors.append(f"{fname}: legacy view_type '{vt}' in merged config")
        if vt not in registry and vt != "bench_main":
            errors.append(f"{fname}: view_type '{vt}' not in bench registry")

    td = cfg.get("test_data", {})
    domain = td.get("bench_first_domain")
    state = td.get("bench_first_state") or "state_hub"
    if domain:
        if domain not in cfg.get("domain_configs", {}):
            errors.append(f"{fname}: unknown bench_first_domain '{domain}'")
        else:
            dom = cfg["domain_configs"][domain]
            if state not in dom and state not in cfg:
                errors.append(f"{fname}: bench_first_state '{state}' missing")

    if state in cfg:
        vt = cfg[state].get("view_type")
        if vt and vt not in registry:
            errors.append(f"{fname}: start state view_type '{vt}' not in registry")

    td = cfg.get("test_data", {})
    ui = td.get("ui_taxonomy")
    if ui:
        primary = ui.get("primary")
        classes = ui.get("classes")
        if not primary or not isinstance(classes, list) or not classes:
            errors.append(f"{fname}: ui_taxonomy must have primary and non-empty classes")
        else:
            from bench_eval.ui_taxonomy_classify import validate_task_taxonomy
            from bench_eval.ui_taxonomy_registry import UI_TAXONOMY_CLASS_IDS as VALID_IDS

            if primary not in VALID_IDS:
                errors.append(f"{fname}: invalid ui_taxonomy.primary '{primary}'")
            errors.extend(validate_task_taxonomy(cfg, task_stem=fname.replace(".json", "")))

    errors.extend(validate_ui_variants_in_config(fname, cfg))

    return errors


def validate_ui_variants_in_config(fname: str, cfg: dict) -> list[str]:
    from bench_eval.ui_variants import validate_ui_variants

    return validate_ui_variants(cfg, label=fname)


def validate_all_configs(
    configs: dict[str, dict],
    registry: set[str] | None = None,
) -> list[str]:
    registry = registry if registry is not None else load_registry_routes()
    errors: list[str] = []
    for fname, cfg in configs.items():
        errors.extend(validate_config(fname, cfg, registry))
    return errors


def verify_tracks_via_api(
    configs: dict[str, dict],
    *,
    address: str = "localhost:9000",
    sample_size: int = 5,
    build_dir: Path | None = None,
) -> list[str]:
    import requests
    from lib.src.agent_bench import client

    errors: list[str] = []
    out_dir = build_dir or (BENCH_TESTS_DIR / "build")
    out_dir.mkdir(exist_ok=True)

    sample = list(configs.items())[:sample_size]
    for fname, cfg in sample:
        path = out_dir / fname.replace(".json", "_verify.json")
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        track_id = f"bench_verify_{path.stem}"[:40]
        created = client.create_track(
            name=track_id,
            id=track_id,
            filepath=str(path),
            address=address,
            delete_existing=True,
        )
        if not created:
            errors.append(f"API: create_track failed for {track_id}")
            continue
        response = requests.post(
            f"http://{address}/track/get",
            data={"track_id": track_id},
            timeout=10,
        )
        response.raise_for_status()
        result = json.loads(response.content.decode("utf-8"))
        config_str = result.get("config", "")
        if not config_str or config_str == "{}":
            errors.append(f"API: empty config for {track_id}")
            continue
        stored = json.loads(config_str)
        if not stored.get("test_data", {}).get("unified_bench"):
            errors.append(f"API: unified_bench flag missing for {track_id}")

    return errors


def run_verification(
    *,
    tests_dir: Path | None = None,
    check_api: bool = True,
    api_address: str = "localhost:9000",
) -> list[str]:
    tests_path = tests_dir or BENCH_TESTS_DIR
    registry = load_registry_routes()
    configs = build_test_configs(tests_path)
    errors = validate_all_configs(configs, registry)
    if check_api:
        try:
            errors.extend(
                verify_tracks_via_api(configs, address=api_address)
            )
        except Exception as e:
            errors.append(f"API (backend may be down): {e}")
    return errors
