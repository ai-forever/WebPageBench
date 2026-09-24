# Конфигурация hermes-ouroboros в WebPageBench

В WebPageBench используются **два независимых слоя конфигурации**. Их не следует смешивать с JSON из других проектов, где ouroboros — это MCP-агент с `max_turns` и отдельными `agent` / `user` моделями.

## Два слоя

| Слой | Файл | Кто читает | Назначение |
|------|------|------------|------------|
| **HERMES API server** | `hermes-ouroboros/config.yaml` + `hermes-ouroboros/.env` | `python main.py --api` | LLM council (Advocate, Skeptic, Oracle, Contrarian, Arbiter), web search, обучение |
| **Eval harness client** | `configs/hermes_ouroboros.default.json` | `bench_eval` при `AGENT_HARNESS=hermes-ouroboros` | HTTP-клиент council'а, промпт планирования, обогащение задачи для browser-use |

Bench **не запускает** HERMES API и **не** передаёт в него поля вроде `mcp`, `tool.max_inner_turns` или `user.model` — это другая архитектура.

## Схема потока

```text
configs/hermes_ouroboros.default.json  +  HERMES_* env
              │
              ▼
    bench_eval.harnesses.hermes_ouroboros
              │  POST /api/query  (analysis_mode)
              ▼
    hermes-ouroboros API  ← config.yaml + .env (council LLM)
              │  verdict
              ▼
    browser-use  ← LLM_PROVIDER / LLM_MODEL / OPENROUTER_API_KEY
              │
              ▼
         WebPageBench mock site
```

## Файл по умолчанию

`configs/hermes_ouroboros.default.json`

Переопределение пути:

```bash
export HERMES_CONFIG_PATH=configs/my_hermes.json
```

## Спецификация JSON (eval harness)

### Корень

| Поле | Тип | По умолчанию | Описание |
|------|-----|--------------|----------|
| `harness` | string | `"hermes-ouroboros"` | Идентификатор harness (информативно) |
| `_comment` | string | — | Комментарий, не используется кодом |

### `api` — HTTP-клиент к локальному или публичному HERMES API

| Поле | Тип | По умолчанию | Env override |
|------|-----|--------------|--------------|
| `base_url` | string | `http://127.0.0.1:8000` | `HERMES_BASE_URL` |
| `api_key` | string \| null | `null` | `HERMES_API_KEY`, `HERMES_OUROBOROS_API_KEY` |
| `timeout_seconds` | number | `300` | `HERMES_TIMEOUT` |

### `council` — один запрос планирования на задачу

| Поле | Тип | По умолчанию | Env override |
|------|-----|--------------|--------------|
| `analysis_mode` | `"verify"` \| `"red_team"` \| `"research"` | `"research"` | `HERMES_MODE` |
| `planning_prompt_prefix` | string | см. default JSON | — |
| `planning_prompt_suffix` | string | см. default JSON | — |
| `on_api_error` | `"continue_with_original_task"` \| `"fail"` | `"continue_with_original_task"` | `HERMES_ON_API_ERROR` |

Режимы council (как в [HERMES API](https://github.com/Ridwannurudeen/hermes-ouroboros)):

- `research` — стратегия и риски (рекомендуется для web-задач WebPageBench)
- `verify` — проверка утверждений
- `red_team` — поиск слабых мест плана

Число раундов council (Round 1 + rebuttal) задаётся **внутри** `hermes-ouroboros` и **не** настраивается из bench JSON.

### `browser` — делегирование в browser-use

| Поле | Тип | По умолчанию | Env override |
|------|-----|--------------|--------------|
| `inherit_from_eval_config` | boolean | `true` | — |
| `max_steps` | number \| null | `null` | `HERMES_BROWSER_MAX_STEPS`, иначе `AGENT_MAX_STEPS` |

LLM браузера (`LLM_PROVIDER`, `LLM_MODEL`, `OPENROUTER_API_KEY`) **не** входят в этот JSON — они общие для eval.

### `task_enhancement` — как verdict council встраивается в prompt browser-use

| Поле | Тип | По умолчанию |
|------|-----|--------------|
| `enabled` | boolean | `true` |
| `include_summary` | boolean | `true` |
| `include_full_verdict` | boolean | `true` |
| `include_fatal_flaws` | boolean | `true` |
| `instruction` | string | Текст для агента после блока council |

## Переменные окружения (приоритет над JSON)

| Переменная | Назначение |
|------------|------------|
| `HERMES_CONFIG_PATH` | Путь к JSON harness |
| `HERMES_BASE_URL` | URL HERMES API |
| `HERMES_API_KEY` | Ключ API (опционально) |
| `HERMES_MODE` | `verify` / `red_team` / `research` |
| `HERMES_TIMEOUT` | Таймаут HTTP-клиента (сек) |
| `HERMES_ON_API_ERROR` | `continue_with_original_task` или `fail` |
| `HERMES_BROWSER_MAX_STEPS` | Лимит шагов browser-use для harness |

## Сравнение с примером из другого проекта

Пример с `global_task_config.max_turns`, `mcp`, `agent.model`, `user.model` относится к **decoupled ouroboros agent** с MCP-tools и multi-turn loop. В WebPageBench это **не применимо**:

| Поле из другого проекта | В WebPageBench |
|-------------------------|-------|
| `global_task_config.max_turns` | → `AGENT_MAX_STEPS` / `browser.max_steps` (лимит **browser-use**, не council) |
| `agent.model` | → `LLM_MODEL` + `LLM_PROVIDER` (browser LLM) |
| `user.model` | Не используется (нет user-simulator) |
| `mcp.server_config_path` | Нет MCP в harness |
| `agent.tool.max_inner_turns` | Нет tool-loop ouroboros; есть шаги browser-use |

Council LLM в другом проекте мог бы соответствовать `hermes-ouroboros/config.yaml` → `provider.model`, а не bench JSON.

## Минимальный запуск с конфигом по умолчанию

```bash
# 1. API council (терминал A) — см. hermes-ouroboros/config.yaml
cd hermes-ouroboros && python main.py --api --host 127.0.0.1 --port 8000

# 2. Стенд (терминал B)
./scripts/start_dab.sh

# 3. Eval (терминал C) — configs/hermes_ouroboros.default.json подхватится сам
export AGENT_HARNESS=hermes-ouroboros
export OPENROUTER_API_KEY=sk-or-v1-...
./scripts/run_gemini_openrouter.sh
```

Кастомный JSON:

```bash
cp configs/hermes_ouroboros.default.json configs/hermes_ouroboros.local.json
# отредактируйте api.base_url, council.analysis_mode, ...
export HERMES_CONFIG_PATH=configs/hermes_ouroboros.local.json
```
