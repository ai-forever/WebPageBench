import json
import os
import sys
from pathlib import Path

root = Path(os.environ["ROOT"])
sys.path.insert(0, str(root))

from bench_eval.bench_verify import BENCH_TESTS_DIR, merge
from bench_eval.task_dates import apply_booking_dates
from lib.src.agent_bench import client

track_id = os.environ["TRACK_ID"]
task_stem = os.environ["TASK_STEM"]
task_file = Path(os.environ["TASK_FILE"])
api = os.environ["API_ADDRESS"]

base = json.loads((BENCH_TESTS_DIR / "config.json").read_text(encoding="utf-8"))
task = json.loads(task_file.read_text(encoding="utf-8"))
cfg = merge(base, task)
apply_booking_dates(cfg)
cfg["test_data"]["test_name"] = task_stem
build = BENCH_TESTS_DIR / "build" / f"{track_id}.json"
build.parent.mkdir(exist_ok=True)
build.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
client.create_track(
    name=track_id,
    id=track_id,
    filepath=str(build),
    address=api,
    delete_existing=True,
)
