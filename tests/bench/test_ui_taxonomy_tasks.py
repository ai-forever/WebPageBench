"""Unit tests: bench tasks must match UI taxonomy (docs/UI_TAXONOMY.md)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

from bench_eval.ui_taxonomy_classify import (
    BENCH_TASKS_DIR,
    annotate_task,
    classify_task,
    validate_task_taxonomy,
)
from bench_eval.ui_taxonomy_registry import UI_TAXONOMY_CLASS_IDS

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from ui_pattern_task_map import (
    canonical_task_count,
    clone_count,
    list_clone_specs,
    pattern_to_stems,
)

EXPECTED_TASK_COUNT = canonical_task_count()


@pytest.fixture(scope="module")
def task_files() -> list[Path]:
    files = sorted(BENCH_TASKS_DIR.glob("*.json"))
    assert len(files) == EXPECTED_TASK_COUNT
    return files


@pytest.fixture(scope="module")
def tasks_by_stem(task_files: list[Path]) -> dict[str, dict]:
    return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in task_files}


class TestTaskTaxonomyPresence:
    def test_all_tasks_have_ui_taxonomy(self, task_files: list[Path]):
        missing = []
        for path in task_files:
            task = json.loads(path.read_text(encoding="utf-8"))
            if "ui_taxonomy" not in task.get("test_data", {}):
                missing.append(path.name)
        assert not missing, f"Tasks without ui_taxonomy: {missing}"

    def test_all_condition_events_map_to_taxonomy(self, tasks_by_stem: dict[str, dict]):
        for stem, task in tasks_by_stem.items():
            conditions = task["test_data"].get("conditions") or []
            for cond in conditions:
                event = cond.get("event_name")
                if not event:
                    continue
                params = cond.get("parameters") if isinstance(cond.get("parameters"), dict) else None
                from bench_eval.ui_taxonomy_classify import classes_for_event

                assert classes_for_event(event, params), f"{stem}: unmapped event {event!r}"

    @pytest.mark.parametrize(
        "class_id",
        [
            c
            for c in UI_TAXONOMY_CLASS_IDS
            if c not in ("PASSIVE", "TXT", "BTN", "AUTH", "CHECK", "FILTER")
        ],
    )
    def test_core_taxonomy_classes_have_task(self, tasks_by_stem: dict[str, dict], class_id: str):
        found = any(
            class_id in task["test_data"]["ui_taxonomy"]["classes"]
            for task in tasks_by_stem.values()
        )
        assert found, f"No bench task covers UI class {class_id}"


class TestTaskTaxonomyConsistency:
    @pytest.mark.parametrize("task_stem", [f.stem for f in sorted(BENCH_TASKS_DIR.glob("*.json"))])
    def test_task_taxonomy_matches_conditions(self, tasks_by_stem: dict[str, dict], task_stem: str):
        errors = validate_task_taxonomy(tasks_by_stem[task_stem], task_stem=task_stem)
        assert not errors, "\n".join(errors)

    def test_primary_is_in_classes(self, tasks_by_stem: dict[str, dict]):
        for stem, task in tasks_by_stem.items():
            ui = task["test_data"]["ui_taxonomy"]
            assert ui["primary"] in ui["classes"], stem

    def test_classify_matches_stored_taxonomy(self, tasks_by_stem: dict[str, dict]):
        for stem, task in tasks_by_stem.items():
            td = task["test_data"]
            expected = classify_task(td, task_stem=stem)
            assert td["ui_taxonomy"]["primary"] == expected["primary"], stem
            assert td["ui_taxonomy"]["classes"] == expected["classes"], stem


class TestTaskTaxonomyDistribution:
    def test_primary_distribution(self, tasks_by_stem: dict[str, dict]):
        counts = Counter(t["test_data"]["ui_taxonomy"]["primary"] for t in tasks_by_stem.values())
        assert counts["BASKET"] >= 10
        assert any(
            "NAV" in t["test_data"]["ui_taxonomy"]["classes"]
            for t in tasks_by_stem.values()
        )
        assert counts["FILES"] >= 4
        assert counts["FAV"] >= 4

    def test_annotate_is_idempotent(self, tasks_by_stem: dict[str, dict]):
        for stem, task in tasks_by_stem.items():
            once = annotate_task(task, task_stem=stem)
            twice = annotate_task(once, task_stem=stem)
            assert once == twice, stem


class TestUiPatternCloneCoverage:
    def test_clone_filenames_are_unique(self):
        names = [spec.filename for spec in list_clone_specs()]
        assert len(names) == len(set(names))
        assert clone_count() == 87

    def test_nondefault_patterns_have_at_least_five_clones(self):
        coverage = pattern_to_stems()
        short = {key: stems for key, stems in coverage.items() if len(stems) < 5}
        assert not short, f"Patterns with <5 clones: { {k: len(v) for k, v in short.items()} }"
        assert len(coverage["theme:dark"]) == 12

    def test_clone_json_exists_and_keeps_source_prompts(self, tasks_by_stem: dict[str, dict]):
        for spec in list_clone_specs():
            assert spec.stem in tasks_by_stem, spec.filename
            source = tasks_by_stem[spec.source_stem]
            clone = tasks_by_stem[spec.stem]
            assert clone["test_data"]["task"] == source["test_data"]["task"], spec.stem
            assert clone["test_data"]["conditions"] == source["test_data"]["conditions"], spec.stem
            assert clone["test_data"]["ui_variants"] == spec.variants, spec.stem
            assert clone["test_data"]["ui_variant_profile"] == spec.profile_id, spec.stem

    def test_theme_clones_do_not_mix_widget_overlays(self, tasks_by_stem: dict[str, dict]):
        for spec in list_clone_specs():
            clone = tasks_by_stem[spec.stem]
            variants = clone["test_data"]["ui_variants"]
            if spec.variants.get("theme") == "dark":
                assert variants == {"theme": "dark"}, spec.stem
                assert "ui_variants" not in (clone.get("domain_configs") or {}).get(
                    clone["test_data"].get("bench_first_domain") or "", {}
                )
            else:
                assert "theme" not in variants, spec.stem
