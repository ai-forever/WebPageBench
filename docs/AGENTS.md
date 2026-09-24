# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

WebPageBench — an open environment for evaluating web agents from the interface’s own event log. The suite is `tests/bench` (**152** tasks: 65 canonical scenarios + 87 control variants across light/dark UI modes; six hub tabs: marketplace, books, grocery, rail, hotels, files). Primary metric: Event-Match Score (EMS). See [README.md](../README.md).

### Services

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| Flask Backend | `cd site/backend && python3 main.py` | 9000 | `DAB_API_PORT` (default 9000, no sudo). |
| Vue Frontend (Vite) | `cd site/frontend && npm run dev` | 5173 | Set `VITE_API_URL=http://127.0.0.1:9000/` if API is not on port 80. |

Quick start both: `./scripts/start_dab.sh`

SQLite DB auto-created in `site/backend/data/`.

### Dependencies

Backend (once):

```bash
pip install --user --ignore-installed blinker -r site/backend/requirements.txt
```

Frontend (once):

```bash
cd site/frontend && npm install
```

### Bench mock

| Script | Purpose |
|--------|---------|
| `./scripts/start_dab.sh` | Backend + frontend |
| `./scripts/start_dab_preview.sh` | Backend + vite preview (для headless eval) |
| `./scripts/run_bench_mock.sh` | Same + demo track from `tests/bench` |
| `./scripts/run_ui_variants_demo.sh` | UI variant demo tracks (`tests/bench/configs/`; backend + frontend must be up) |
| `./scripts/run_bench_tests.sh` | Same + `pytest tests/bench/test_verify_bench.py` |
| `./scripts/run_eval.sh` | LLM eval (backend + frontend must be up; see `docs/EVAL_README.md`) |
| `./scripts/export_leaderboard.sh` | Экспорт `tests/eval/` → `liderboard/results/` |

Config: `tests/bench/config.json`, tasks: `tests/bench/tasks/`. Browse: `http://127.0.0.1:5173/<track_id>/state_hub/bench_hub`

### Eval harnesses (`AGENT_HARNESS`)

Public leaderboard (6 browser/DOM + 5 screenshot-only): `browser-use`, `ouroboros-cut`, `ouroboros-full-isolated`, `ouroboros-full-evolving`, `openmanus`, `openhands`; GUI: `qwen3-vl`, `uitars`, `opencua`, `evocua`, `fara`.

Also wired in the runner: `hermes-ouroboros`, `deepagents`, `jedi`. See [gui-agents.md](./gui-agents.md) and [`bench_eval/agents/`](../bench_eval/agents/README.md).

Готовые конфиги: `envs/runs/<harness>/<model>.env`. Установка submodules: `./scripts/install_harnesses.sh` (после `pip install -r requirements-eval.txt`). OpenHands требует Python ≥3.12.

### Creating test tracks

Use `tests.py` or `scripts/run_bench_mock.sh` as reference. Merge `tests/bench/config.json` + task JSON, then `client.create_track(...)` with `address=localhost:9000`.

### Tests and lint

No ESLint/Prettier on frontend. Pytest covers `tests/bench/`, `tests/evals/`, `tests/agents/`. Bench verification: `pytest tests/bench/test_verify_bench.py`.

### Frontend build

`cd site/frontend && npm run build` → `site/frontend/dist/`.

### Agency agents (Cursor rules)

Специалисты из [agency-agents](https://github.com/msitarzewski/agency-agents) стоят как `.mdc` в [`.cursor/rules/`](../.cursor/rules/) с `alwaysApply: false`. Вызывать точечно через `@slug`, не держать always-on.

**Eval:** единственный skill — [`.agents/skills/deepeval/`](../.agents/skills/deepeval/). Не копировать Model QA (и другие agency-agents) в `.agents/skills/`. `@model-qa-specialist` — persona для разбора прогонов, не второй DeepEval.

Ядро: `@frontend-developer` `@backend-architect` `@software-architect` `@multi-agent-systems-architect` `@autonomous-optimization-architect` `@prompt-engineer` `@developer-tooling-engineer` `@technical-writer` `@agentic-search-optimizer` `@test-results-analyzer` `@api-tester` `@model-qa-specialist`

Второй эшелон: `@ui-designer` `@ux-architect` `@persona-walkthrough-specialist` `@workflow-architect` `@test-automation-engineer` `@evidence-collector` `@code-reviewer` `@minimal-change-engineer` `@data-visualization-engineer` `@devops-automator` `@secrets-credential-hygiene-engineer` `@statistician`
