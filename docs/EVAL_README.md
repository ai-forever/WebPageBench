# Оценка агентов на WebPageBench

WebPageBench запускает выбранный agent harness на задачах из
`tests/bench/tasks/`, записывает типизированные события интерфейса и проверяет
их через DeepEval. Основная метрика — **Event-Match Score (EMS)**: задача
успешна, только если события удовлетворяют всем `conditions`. **Completion**
показывает, что агент объявил задачу завершённой, но не заменяет EMS.

```text
task JSON → create_track → harness + LLM → UI events → check() → EMS
```

Judge-модель и анализ отрендеренного текста для проверки не используются.
Состав 152 задач описан в [bench-tasks.md](./bench-tasks.md), классификация —
в [TAXONOMY.md](./TAXONOMY.md) и [UI_TAXONOMY.md](./UI_TAXONOMY.md).

## Быстрый старт

### Требования

- Python 3.11+; для `openhands` — Python 3.12+;
- Node.js и npm для frontend;
- Chromium для Playwright;
- API-ключ LLM или OpenAI-compatible локальный endpoint.

### Установка

```bash
git submodule update --init deepeval browser-use hermes-ouroboros ouroboros \
  deepagents openhands openmanus

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-eval.txt
pip install -e ./deepeval -e ./browser-use -e ./hermes-ouroboros/sdk
./scripts/install_harnesses.sh
python -m playwright install chromium

pip install --user --ignore-installed blinker -r site/backend/requirements.txt
cd site/frontend && npm install && cd ../..
```

`install_harnesses.sh` устанавливает `openmanus`, `openhands` и `deepagents`.
Ouroboros full-режимы дополнительно требуют:

```bash
./scripts/install_ouroboros.sh
```

Проверить отдельный harness:

```bash
python scripts/check_harness_compat.py --harness browser-use
```

### Ключи провайдеров

Готовые run-конфиги находятся в `envs/runs/<harness>/<model>.env`.
Секреты храните только в gitignored-файлах:

```bash
cp envs/_openrouter.env.example envs/_openrouter.env
cp envs/_gigachat.env.example envs/_gigachat.env
```

После изменения фрагментов `envs/models/` или `envs/harnesses/` пересоберите
run-конфиги:

```bash
./scripts/gen_eval_envs.sh
```

### Локальные сервисы

Для headless eval используйте production preview:

```bash
./scripts/start_dab_preview.sh
```

Скрипт поднимает backend на `127.0.0.1:9000` и frontend на
`127.0.0.1:5173`. Для ручной UI-разработки используйте `./scripts/start_dab.sh`.

Перед LLM-прогоном можно проверить браузер и DOM:

```bash
python3 scripts/diagnose_browser_dom.py \
  --track-id ecommerce_basket_any_product
```

Ожидаются `backend_probe.ok: true`, `browser_api_probe.has_track: true` и
`warmup.ready: true`.

### Smoke и полный прогон

Во втором терминале:

```bash
source .venv/bin/activate

EVAL_MAX_TASKS=1 \
EVAL_TASK_FILTER=ecommerce_basket_any_product \
./scripts/run_eval.sh browser-use/gemini-2.5-flash
```

Полный прогон всех 152 задач:

```bash
unset EVAL_MAX_TASKS EVAL_TASK_FILTER
./scripts/run_eval.sh browser-use/gemini-2.5-flash
```

`run_eval.sh` проверяет сервисы, создаёт каталог прогона, собирает
`dataset.json` и запускает DeepEval.

## Harness

| `AGENT_HARNESS` | Исполнитель | Дополнительный сервис |
|-----------------|-------------|------------------------|
| `browser-use` | browser-use | нет |
| `ouroboros-cut` | browser-use + Ouroboros prompts | нет |
| `ouroboros-full-isolated` | Ouroboros, отдельный drive на задачу | Ouroboros `:9123` |
| `ouroboros-full-evolving` | Ouroboros, общий evolving drive | Ouroboros `:9123`, один worker |
| `hermes-ouroboros` | HERMES council → browser-use | HERMES API |
| `openmanus` | OpenManus prompts → browser-use | нет |
| `openhands` | OpenHands BrowserToolSet | нет, Python 3.12+ |
| `deepagents` | LangGraph + Playwright MCP | Node.js / `npx` |
| `qwen3-vl`, `uitars`, `jedi`, `opencua`, `evocua`, `fara` | screenshot-only executor | vLLM или GigaHF |

Подробности, которые не дублируются здесь:

- [ouroboros-config.md](./ouroboros-config.md) — cut/full-режимы, identity и
  evolution;
- [hermes-ouroboros-config.md](./hermes-ouroboros-config.md) — HERMES API и
  JSON-конфиг;
- [gui-agents.md](./gui-agents.md) — screenshot-only модели и action space;
- [agent-harnesses.md](./agent-harnesses.md) — обзор внешних фреймворков.

Примеры:

```bash
./scripts/run_eval.sh openmanus/deepseek-v4-flash
./scripts/run_eval.sh openhands/gemini-2.5-flash
./scripts/run_eval.sh deepagents/gemini-2.5-flash
./scripts/run_eval.sh qwen3-vl/gigahf-qwen3.8-27b
```

Full Ouroboros запускается в двух терминалах:

```bash
# Терминал 1
./scripts/start_dab_ouroboros_preview.sh

# Терминал 2
./scripts/run_eval.sh ouroboros-full-isolated/openrouter-ouroboros
```

## Провайдеры LLM

Run-конфиги обычно задают провайдера и модель автоматически. Для ручной
настройки:

```bash
# OpenAI-compatible API
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4.1-mini
export OPENAI_API_KEY=sk-...

# локальный vLLM
export LLM_PROVIDER=vllm
export LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
export LLM_BASE_URL=http://127.0.0.1:8000/v1
export OPENAI_API_KEY=EMPTY
```

## Управление прогоном

Основные переменные:

| Переменная | Назначение |
|------------|------------|
| `EVAL_TASK_FILTER` | Подстрока в имени задачи |
| `EVAL_MAX_TASKS` | Максимальное число задач |
| `EVAL_REBUILD_DATASET` | Пересобрать `dataset.json` |
| `EVAL_OUTPUT_DIR` | Явный каталог артефактов |
| `EVAL_DRY_RUN` | Создать треки без запуска агента |
| `EVAL_FRONTEND_HOST` | Frontend, по умолчанию `127.0.0.1:5173` |
| `EVAL_API_ADDRESS` | Backend, по умолчанию `localhost:9000` |
| `EVAL_TRACK_SUFFIX` | Суффикс track ID для изоляции прогонов |
| `AGENT_HEADLESS` | Headless-режим браузера |
| `AGENT_MAX_STEPS` | Лимит шагов агента |
| `AGENT_WARMUP_TIMEOUT` | Ожидание интерактивного DOM |
| `DEEPEVAL_EXTRA_ARGS` | Аргументы `deepeval test run` |

Полный набор defaults находится в `.env.eval.example`, `envs/_common.env` и
`bench_eval/config.py`.

### Параллельность

По умолчанию run-конфиги используют pytest-xdist. Число workers можно
переопределить:

```bash
DEEPEVAL_EXTRA_ARGS="--num-processes 4" \
./scripts/run_eval.sh browser-use/gemini-2.5-flash
```

Каждый worker запускает отдельный Chromium, поэтому начинайте с двух.
`ouroboros-full-evolving` всегда запускайте с одним worker:

```bash
DEEPEVAL_EXTRA_ARGS="--num-processes 1" \
./scripts/run_eval.sh ouroboros-full-evolving/openrouter-ouroboros
```

Разные модели можно запускать одновременно: `run_eval.sh` создаёт отдельные
каталоги и уникальные `EVAL_TRACK_SUFFIX`. Не задавайте одинаковый
`EVAL_OUTPUT_DIR` двум процессам.

## Датасет и артефакты

Собрать датасет отдельно:

```bash
python3 scripts/build_eval_dataset.py --mock bench
python3 scripts/build_eval_dataset.py --mock bench \
  --task-filter ecommerce_basket --max-tasks 3
```

Артефакты одного прогона:

```text
tests/eval/<model>/<harness>/<YYYY-MM-DD_HH-MM-SS>/
├── dataset.json
├── results.json
└── results.worker-gw*.json  # при параллельном запуске
```

`results.json` содержит:

| Поле | Содержание |
|------|------------|
| `run` | модель, provider, harness, длительность и агрегированные метрики |
| `tests[]` | EMS, Completion, ошибки, `dab_check` и траектория каждой задачи |
| `ui_taxonomy_stats` | агрегаты по UI-классам и вариантам контролов |

Внутри `tests[]`:

- `success` и `dab_check.all_passed` — итог EMS;
- `agent.is_done` — Completion;
- `trajectory.agent` — шаги и ответы harness;
- `trajectory.dab_events` — события backend;
- `ui_taxonomy` — проверенные и фактически использованные UI-классы.

Формат можно сверять с опубликованными файлами в
`liderboard/results/raw/*/results.json`.

Сгенерировать отчёт:

```bash
python3 scripts/render_eval_report.py --latest
python3 scripts/render_eval_report.py --latest \
  --model gpt-4.1-mini --harness browser-use
```

## Интерпретация результата

| EMS | Completion | Значение |
|----:|-----------:|----------|
| 1 | 1 | Агент выполнил условия и завершился |
| 1 | 0 | Условия выполнены, но harness не объявил завершение |
| 0 | 1 | Агент переоценил успех; проверяйте `failed_conditions` |
| 0 | 0 | Задача не выполнена или прогон завершился ошибкой |

EMS вычисляется по событиям и всегда является основной метрикой. Completion —
диагностический сигнал.

## Проверки и устранение проблем

Статическая проверка задач:

```bash
python3 scripts/build_bench_config.py
python3 scripts/build_bench_tasks.py
pytest tests/bench/test_verify_bench.py -m "not integration"
```

Сервисы и UI-тесты:

```bash
./scripts/run_bench_tests.sh
```

| Симптом | Что проверить |
|---------|---------------|
| `No module named 'deepeval'` | `pip install -e ./deepeval` |
| Harness не готов | `python scripts/check_harness_compat.py --harness <harness>` |
| Не найден Chromium | `python -m playwright install chromium` |
| Пустой DOM | preview вместо dev и `diagnose_browser_dom.py` |
| Не найден API-ключ | `envs/_openrouter.env` / `envs/_gigachat.env` |
| `full_*` не подключается | Ouroboros `:9123` и `OUROBOROS_URL` |
| Старый run-конфиг | `./scripts/gen_eval_envs.sh` |

Если frontend собран с неправильным API URL, перезапустите
`./scripts/start_dab_preview.sh`. При медленном рендеринге увеличьте
`AGENT_WARMUP_TIMEOUT`.

## Расширение

- Новая задача: измените `scripts/build_bench_tasks.py`, пересоберите задачи и
  запустите `pytest tests/bench/`.
- Новый harness: добавьте его в `bench_eval/harness_factory.py` и
  `bench_eval/harness_compat.py`.
- Новая метрика DeepEval: добавьте её в `tests/evals/metrics.py`.
- UI-варианты и классы взаимодействий описаны в
  [UI_TAXONOMY.md](./UI_TAXONOMY.md).
