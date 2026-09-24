# Режимы ouroboros в WebPageBench

Три режима измерения decoupled **Ouroboros** (как в Toolathlon) поверх базового `browser-use` (`normal`).

## Режимы

| Режим | `AGENT_HARNESS` | Что происходит |
|-------|-----------------|----------------|
| **normal** | `browser-use` | Прямой browser-use loop (baseline) |
| **cut** | `ouroboros-cut` | Ouroboros **только как оболочка цикла**: промпты и инструменты стенда (browser-use). Свой пустой drive на задачу. Без identity и evolution. |
| **full_isolated** | `ouroboros-full-isolated` | **Вся** функциональность Ouroboros (identity, полный agent loop). Каждая задача с нуля (`memory_mode=forked`). Evolution выключен. |
| **full_evolving** | `ouroboros-full-evolving` | **Вся** функциональность Ouroboros + evolution между задачами. Общий drive (`memory_mode=shared`). Запускать с `workers=1`. |

## Конфиги

| Режим | JSON |
|-------|------|
| cut | `configs/ouroboros.cut.json` |
| full_isolated | `configs/ouroboros.full_isolated.json` |
| full_evolving | `configs/ouroboros.full_evolving.json` |

## Запуск

### cut (только стенд + browser-use)

```bash
export AGENT_HARNESS=ouroboros-cut
export OPENROUTER_API_KEY=sk-or-v1-...
./scripts/run_gemini_openrouter.sh
```

Ouroboros binary **не нужен**. Используются промпты стенда и browser-use как единственный tool surface. LLM берётся из eval env (`LLM_PROVIDER`, `GIGACHAT_TOKEN` / `OPENROUTER_API_KEY` и т.д.) — тот же `ChatGigaChat`, что и для `browser-use`:

```bash
./scripts/run_eval.sh ouroboros-cut/gigachat-3-ultra
```

### full_isolated / full_evolving (нужен Ouroboros)

Установка CLI (один раз):

```bash
git submodule update --init ouroboros
./scripts/install_ouroboros.sh
```

Запуск:

```bash
# Терминал A — стенд + Ouroboros
./scripts/start_dab_ouroboros_preview.sh

# Терминал B — eval
./scripts/run_eval.sh ouroboros-full-isolated/openrouter-ouroboros
```

Порты: backend **9000**, Ouroboros **9123** (`OUROBOROS_URL` в harness env).

Для `full_evolving` не запускайте несколько параллельных eval-процессов с **одним** `EVAL_TRACK_SUFFIX` — drive общий внутри suffix. Разные прогоны с общим `EVAL_OUTPUT_DIR` изолированы через `ouroboros_drive/<suffix>/`.

### GigaChat и ouroboros

| Режим | Провайдер | Что нужно в env |
|-------|-----------|-----------------|
| `ouroboros-cut` | eval LLM (`ChatGigaChat` / OpenRouter) | ключ в `envs/models/*` |
| `ouroboros-full-isolated` | auto-sync → Ouroboros | **OpenRouter:** только `OPENROUTER_API_KEY` |
| `ouroboros-full-evolving` | auto-sync → Ouroboros | **OpenRouter:** только `OPENROUTER_API_KEY` |

**OpenRouter (рекомендуется для full_*):** eval по умолчанию синхронизирует дешёвые модели `google/gemini-2.5-flash` для main, fallback и review через OpenRouter (`POST /api/settings`):

```bash
# В envs/models/openrouter-ouroboros.env — только ключ:
# OPENROUTER_API_KEY=sk-or-v1-...

./scripts/run_eval.sh ouroboros-full-isolated/openrouter-ouroboros
./scripts/run_eval.sh ouroboros-full-evolving/openrouter-ouroboros
```

Другие OpenRouter-модели (`deepseek-v4-flash`) задают **main** слот; fallback/review/scope/websearch остаются `google/gemini-2.5-flash`, если не переопределены в env.

При установке `./scripts/install_ouroboros.sh` и перед preview-стартом применяется `scripts/patch_ouroboros_for_bench.py` — дефолты submodule `ouroboros` тоже переводятся на дешёвые модели.

**GigaChat:**

```bash
./scripts/run_eval.sh ouroboros-full-isolated/gigachat-3-ultra
```

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `AGENT_HARNESS` | `ouroboros-cut`, `ouroboros-full-isolated`, `ouroboros-full-evolving` |
| `OUROBOROS_BIN` | CLI `ouroboros` (обязателен для full-режимов) |
| `OUROBOROS_URL` | Gateway (`http://127.0.0.1:9123`) |
| `OUROBOROS_REPO_DIR` | Каталог репозитория Ouroboros (fallback seed: `data/memory/`) |
| `OUROBOROS_IDENTITY_SEED_DIR` | Опционально: data root или `memory/` с seed-файлами. По умолчанию — `configs/ouroboros/seed/memory/` |
| `OUROBOROS_CONFIG_PATH` | Путь к JSON режима |
| `OUROBOROS_EVOLUTION_ENABLED` | Переопределение evolution (`true`/`false`) |
| `OUROBOROS_RESTART_READY_TIMEOUT` | Секунды ожидания `/api/health` после evolution-restart (по умолчанию `120`) |
| `OUROBOROS_RESTART_READY_POLL` | Интервал опроса health в секундах (по умолчанию `1`) |

## Архитектура

```text
cut:
  task prompt → ouroboros-cut shell → browser-use → mock site
  drive: empty, per-task

full_isolated:
  task prompt → Ouroboros API/CLI (forked) → Ouroboros browser/tools
  drive: forked + identity, per-task, evolution off

full_evolving:
  task prompt → Ouroboros API/CLI (shared) → Ouroboros browser/tools
  drive: shared + identity, evolution on between tasks
```

## Отличие от hermes-ouroboros

| | hermes-ouroboros | ouroboros cut / full_* |
|--|------------------|------------------------|
| Runtime | HERMES council HTTP API | cut shell или razzant/ouroboros |
| Браузер | browser-use | cut: browser-use; full: Ouroboros native |
| Drive / evolution | Нет | Да |

См. [hermes-ouroboros-config.md](./hermes-ouroboros-config.md).

## Identity seed (автоматически)

Для `full_isolated` и `full_evolving` bench копирует seed из `memory/` в `drive/memory/` перед задачей:

| Файл | Назначение |
|------|------------|
| `identity.md` | Кто я в контексте WebPageBench |
| `WORLD.md` | Описание окружения и ограничений |
| `registry.md` | Карта доступной памяти на drive |
| `knowledge/dab-benchmark.md` | Стабильные факты о стенде и режимах |

**Порядок выбора seed** (первый подходящий):

1. `OUROBOROS_IDENTITY_SEED_DIR` — data root (`…/data`) или сразу `…/memory`
2. `OUROBOROS_REPO_DIR/data/memory` или `…/data`
3. `~/Ouroboros/data/memory` (desktop Ouroboros)
4. Bundled: `configs/ouroboros/seed/memory/` в WebPageBench

Ручная настройка не нужна, если устраивает bundled seed. Для своей личности Ouroboros укажите `OUROBOROS_IDENTITY_SEED_DIR=~/Ouroboros/data` или путь к `memory/`.
