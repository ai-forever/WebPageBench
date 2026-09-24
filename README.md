# WebPageBench

Open environment for evaluating web agents: every task is verified from the interface’s own event log. Six instrumented mock sites with brand identifiers removed (marketplace, bookstore, grocery delivery, rail ticketing, hotel search, and a document cabinet) emit typed events with parameters as a user or an agent acts. A task declares the events it requires; success is the **Event-Match Score (EMS)** — no judge model and no scraping of rendered pages.

The same instrumentation supports controlled UI variation: one configuration switch re-renders a task through a different implementation of a single control while the prompt and the success conditions stay identical, so sensitivity to interface form can be measured under a fixed task specification.

Interfaces, prompts and catalog data are Russian. The verification contract reads typed events and never the interface text, so it does not depend on the language.

## Release

| | |
|---|---|
| Tasks | **152** — 65 canonical scenarios and 87 control variants (light/dark UI modes) |
| Sites | 6 de-branded mock tabs under one hub |
| Events | 19 semantic event types; 521 conditions (3.4 per task on average) |
| UI configuration | 9 keys (8 controls + colour theme), 33 implementations |
| Variants | 87 tasks from 25 donors through 20 profiles; 82 change exactly one control |
| Evaluated harnesses | 6 browser/DOM configurations + 5 screenshot-only GUI-agent families |
| Public leaderboard | 24 model–harness pairs |
| Primary metric | Event-Match Score (EMS); Completion is recorded separately |

Public leaderboard: [huggingface.co/spaces/ai-forever/WebPageBench](https://huggingface.co/spaces/ai-forever/WebPageBench).  
Code: [github.com/ai-forever/WebPageBench](https://github.com/ai-forever/WebPageBench).

On the public 152-task leaderboard the gap between what agents declare finished (Completion) and what the log confirms (EMS) reaches 41 points.

## Clone

The repository uses Git LFS for raw leaderboard traces and binary assets. For a
faster checkout without the full Git history:

```bash
git lfs install
git clone --depth=1 https://github.com/ai-forever/WebPageBench.git
```

For a code-only checkout, set `GIT_LFS_SKIP_SMUDGE=1` before `git clone`.
Run `git lfs pull` later to download the assets required by the local UI.

## Repository layout

- `lib/` — Python client (`create_track`, `get_track`, `check`)
- `site/backend/` — API and event store (SQLite); catalogs in `static/kv/{shop,books,grocery,rail,hotels}/`
- `site/frontend/` — Vue + Vuetify SPA; six hub tabs in `src/views/bench/`
- `bench_eval/` — eval runner, harnesses, tokens, cost
- `tests/bench/` — task suite (**152** JSON files)
- `tests/evals/` — DeepEval pytest suite
- `liderboard/` — Gradio Space source
- `envs/` — ready harness × model run configs
- `example.py` — UI-pattern catalog for manual checks (needs `./scripts/start_dab.sh`); `tests.py` — create all tracks from `tests/bench`

## Run

### Docker

```bash
cd site
docker compose -f docker-compose.local.yml build --no-cache
docker compose -f docker-compose.local.yml up
```

### Development

```bash
cd site/backend
python main.py
```

```bash
cd site/frontend
npm run dev
```

Or both: `./scripts/start_dab.sh`.

## Documentation

See the [documentation index](./docs/README.md).

## Evaluation

See [docs/EVAL_README.md](./docs/EVAL_README.md) for installation, supported
harnesses, run configs, metrics and artifacts.

Export a finished run: `./scripts/export_leaderboard.sh`.

## Submit a leaderboard result

After a full evaluation run finishes, list the completed runs and select its
`results.json`:

```bash
./scripts/export_leaderboard.sh --list --require-finished
```

Export that run in submission mode. This adds its summary and raw trace without
removing existing leaderboard entries:

```bash
./scripts/export_leaderboard.sh \
  --results-json tests/eval/<model>/<harness>/<timestamp>/results.json \
  --require-finished
```

The command creates two files:

```text
liderboard/results/<model>__<harness>.json
liderboard/results/raw/<model>__<harness>/results.json
```

Check that the run contains all 152 tasks, then create a branch and commit only
those generated files:

```bash
git switch -c leaderboard/<model>-<harness>
git add \
  liderboard/results/<model>__<harness>.json \
  liderboard/results/raw/<model>__<harness>/results.json
git commit -m "Submit <model> with <harness>"
git push -u origin leaderboard/<model>-<harness>
```

Open a pull request to the `release` branch of this repository. Do not edit the
generated JSON manually. After the submission is reviewed and merged, the
maintainers publish `liderboard/` to the
[WebPageBench Space](https://huggingface.co/spaces/ai-forever/WebPageBench), and
the result appears on the public leaderboard. Contributors do not need Hugging
Face credentials.

## Tasks

`tests/bench/` — one de-branded hub and **152** tasks (65 canonical + 87 variants) across six tabs. See [docs/TAXONOMY.md](./docs/TAXONOMY.md).

Create tracks: `tests.py` or `scripts/run_bench_mock.sh`. Static validation: `pytest tests/bench/test_verify_bench.py`.

## License

WebPageBench is licensed under the [Apache License 2.0](./LICENSE).
