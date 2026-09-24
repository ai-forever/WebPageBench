"""Tests for eval dataset track_id isolation."""

from bench_eval.dataset import _track_id, configs_to_goldens


def test_track_id_without_suffix():
    assert _track_id("Ecommerce Basket") == "ecommerce_basket"


def test_track_id_with_suffix():
    assert _track_id("ecommerce_basket_any_product", suffix="a1b2c3d4") == (
        "ecommerce_basket_any_product__a1b2c3d4"
    )


def test_configs_to_goldens_applies_track_suffix(tmp_path, monkeypatch):
    tests_dir = tmp_path / "bench"
    tasks_dir = tests_dir / "tasks"
    build_dir = tests_dir / "build"
    tasks_dir.mkdir(parents=True)
    build_dir.mkdir(parents=True)
    (tests_dir / "config.json").write_text(
        '{"test_data": {}}',
        encoding="utf-8",
    )
    (tasks_dir / "demo_task.json").write_text(
        '{"test_data": {"task": "Open %HOST%", "conditions": []}}',
        encoding="utf-8",
    )

    goldens = configs_to_goldens(
        str(tests_dir),
        frontend_host="127.0.0.1:5173",
        track_suffix="deadbeef",
    )

    assert len(goldens) == 1
    meta = goldens[0].additional_metadata
    assert meta["track_id"] == "demo_task__deadbeef"
    assert meta["task_url"] == "http://127.0.0.1:5173/demo_task__deadbeef"
