# GUI-модели в WebPageBench: qwen3-vl, uitars, opencua, evocua, fara

Пять оценённых на лидерборде семейств, которые управляют интерфейсом **по скриншотам**: на вход — картинка вьюпорта, на выход — координата клика. В отличие от browser/DOM-harness'ов из [EVAL_README.md](./EVAL_README.md), DOM модели не видят. В раннере также есть `jedi` (не в публичных 24 парах).

Код: [`bench_eval/agents/`](../bench_eval/agents/README.md). Reference-реализации, с которых снята семантика action space, — `OSWorld/mm_agents`.

---

## Что это меняет в пайплайне

Ничего, кроме исполнителя действий. Треки, `conditions`, DeepEval, `results.json` и лидерборд — те же:

```text
create_track → GUI-агент (скриншот ↔ vLLM) → Playwright-исполнитель → check() → DeepEval
```

| Слой | DOM-harness (`browser-use`) | GUI-модель |
|------|------------------------------|------------|
| Наблюдение | DOM + индексы элементов | PNG вьюпорта 1280×720 |
| Действие | `click_element(index=12)` | `pyautogui.click(640, 360)` / tool call |
| Исполнитель | browser-use | `bench_eval/agents/core/executor.py` (Playwright) |
| Модель | облачный LLM-провайдер | self-hosted vLLM или платформа (GigaHF) |

Успех по-прежнему определяет телеметрия бэкенда, а не отчёт агента.

---

## Быстрый старт

```bash
# 1. Поднять стенд
./scripts/start_dab.sh

# 2. Поднять модель (на GPU-хосте)
python -m bench_eval.agents.cli.serve qwen3-vl-8b --port 8000

# 3. Прогнать бенчмарк
export GUI_AGENT_BASE_URL=http://127.0.0.1:8000/v1
./scripts/run_eval.sh qwen3-vl/qwen3-vl-8b
```

Готовые конфиги: `envs/runs/{qwen3-vl,uitars,jedi,opencua,evocua}/<model>.env`. Если поднимать веса негде — см. [Модели с платформы GigaHF](#модели-с-платформы-gigahf).

Проверка готовности: `python scripts/check_harness_compat.py --harness qwen3-vl`.

---

## Семейства и action space

| `AGENT_HARNESS` | Модель по умолчанию | Формат ответа | Координаты |
|-----------------|---------------------|---------------|------------|
| `qwen3-vl` | `qwen3-vl-8b` | `computer_use` tool call | пиксели resized-изображения |
| `uitars` | `uitars-1.5-7b` | DSL `click(start_box=…)` | 1.5 — пиксели, DPO — сетка 0..1000 |
| `jedi` | `jedi-7b` | планировщик pyautogui + grounder tool call | пиксели resized-изображения |
| `opencua` | `opencua-7b` | markdown-секции + pyautogui | 0..1 (у 72B — сетка qwen2.5-VL) |
| `evocua` | `evocua-s2` | S2 — tool call, S1 — pyautogui | S2 — пиксели, S1 — 0..1 |
| `gui-agent` | — | любая из зарегистрированных (`GUI_AGENT_MODEL` обязателен) | из реестра |

Полный список чекпоинтов и поддерживаемых действий:

```bash
python -m bench_eval.agents.cli.models
python -m bench_eval.agents.cli.models --family uitars --json
```

Разные action space приведены к одному IR (`bench_eval/agents/core/actions.py`), поэтому один Playwright-исполнитель отрабатывает все пять. Действия, которых у семейства нет, деградируют по правилам `ActionSpace.coerce()`, а не роняют прогон.

---

## Модели с платформы GigaHF

[`gigahf.sberdevices.ru`](https://gigahf.sberdevices.ru/api/docs) — внутренняя платформа, где модели **уже развёрнуты**: GPU и `vllm serve` не нужны, нужен только Bearer-токен. Агент, промпт и парсер берутся из того же семейства `qwen3_vl`, меняется только транспорт (`bench_eval/agents/core/gigahf.py`).

```bash
cp envs/_gigahf.env.example envs/_gigahf.env   # вписать GIGAHF_TOKEN
python -m bench_eval.agents.cli.serve --health https://gigahf.sberdevices.ru/api/v1
./scripts/run_eval.sh qwen3-vl/gigahf-qwen3.8-27b
```

Готовые конфиги: `envs/runs/qwen3-vl/gigahf-qwen3.8-27b.env`, `…/gigahf-qwen3.6-27b.env`. Список развёрнутых моделей — `GET /api/v1/models` (без токена) или `--health`; на сентябрь 2026 vision-моделей 11, включая `Qwen3.8-27B`, `Qwen3.6-27B` и `Qwen2.5-VL-72B-Instruct`.

### Почему не просто `GUI_AGENT_BASE_URL`

Формат сообщений у GigaHF OpenAI-совместимый (текстовые части + `image_url` с `data:`-URI), но три детали ломают обычный клиент:

| Что | Как решено |
|-----|------------|
| Синхронный `POST /chat/completions` — **10 запросов в минуту на IP** (429). Один таск тратит до `AGENT_MAX_STEPS` вызовов | По умолчанию `GIGAHF_MODE=async`: `POST /async/chat/completions` → поллинг `GET /async/chat/completions/{id}` до статуса `ready`. Лимит там ~150 RPS |
| Поля вне схемы `ChatCompletionRequestJSON` отклоняются с 422 | Всё лишнее уезжает в `extra_params` (`GigaHFClient.build_request`) |
| Сертификат подписан внутренним CA, которого нет в `certifi`: httpx падает с `CERTIFICATE_VERIFY_FAILED` там, где curl проходит | Транспорт ходит с `verify=False` — настраивать нечего |

Переменные транспорта: `GIGAHF_MODE` (`async` \| `sync`), `GIGAHF_POLL_INTERVAL`, `GIGAHF_POLL_TIMEOUT`, `GIGAHF_SYNC_RPM`, `GIGAHF_EXTRA_PARAMS` (JSON, например `{"model_path": "giga/..."}` для staging-моделей).

В `sync`-режиме клиент сам держится под лимитом (`GIGAHF_SYNC_RPM`, по умолчанию 10) и добирает результат через async-эндпоинт, если пришёл 504. Учтите: лимитер живёт **в одном процессе**, а DeepEval поднимает воркеров отдельными процессами — при `--num-processes N` реальный потолок в N раз выше заявленного.

### Полные дампы запросов и ответов

`results.json` хранит только разобранный ответ — действия и сырой текст. Когда нужно увидеть, **что именно ушло на вход модели и что вернулось**, включается `AGENT_DUMP_ENABLED`: на каждый вызов пишется один JSON с телом запроса дословно (base64-скриншоты включительно) и нетронутым ответом.

По умолчанию выключено — дампы весят примерно столько же, сколько сумма скриншотов (~1 МБ на шаг при `GUI_AGENT_HISTORY_N=3`), то есть сотни МБ на полный прогон.

```bash
# в env-файле прогона или в шелле
AGENT_DUMP_ENABLED=true EVAL_MAX_TASKS=1 \
  ./scripts/run_eval.sh qwen3-vl/gigahf-qwen3.8-27b
```

| Переменная | Что делает |
|---|---|
| `AGENT_DUMP_ENABLED` | включает дампы (`EvalConfig.agent_dump_enabled`) |
| `AGENT_DUMP_DIR` | куда писать; по умолчанию `<EVAL_OUTPUT_DIR>/llm-calls` |
| `AGENT_DUMP_IMAGES=trim` | заменить data-URI на `<base64 image, N chars>`, сохранив структуру |

`GUI_AGENT_DUMP_DIR` продолжает работать как синоним `AGENT_DUMP_DIR` и, если `AGENT_DUMP_ENABLED` не задан явно, сам включает дампы.

```text
<dump-dir>/
├── index.jsonl                      # по строке на вызов, без картинок — можно грепать
└── <task_key>/step-04_call-004_<pid>.json
```

| Поле дампа | Что внутри |
|---|---|
| `context` | `task_key`, номер шага, URL страницы, инструкция |
| `http` | метод, URL и **тело как оно уходит на wire** (у async-режима — с конвертом `{"request": …}`) |
| `request` | `ChatCompletionRequestJSON` после `build_request()` |
| `response` | ответ генерации целиком, как его вернула платформа |
| `gigahf` | `request_id` и история поллинга (сколько ждали, в каких статусах) |
| `summary` | дайджест без картинок: usage, `finish_reason`, текст ответа |

Механизм не привязан к GigaHF: с обычным vLLM-эндпоинтом пишется тот же дамп с `transport: openai`.

DOM-harness'ы (`browser-use` и прочие) тоже могут ходить в GigaHF: `LLM_PROVIDER=gigahf` + `LLM_BASE_URL`. Но идут они через синхронный эндпоинт со своим HTTP-клиентом, то есть под лимит 10 RPM — для полного прогона это непригодно.

---

## Ресурсы GPU

| Чекпоинт | Минимум GPU | `--tensor-parallel-size` |
|----------|-------------|--------------------------|
| `qwen3-vl-4b`, `qwen3-vl-8b`, `uitars-1.5-7b`, `jedi-3b`, `jedi-7b`, `opencua-7b`, `evocua-s2` | 1 | 1 |
| `qwen3-vl-32b`, `qwen3-vl-30b-a3b`, `opencua-32b` | 2 | 2 |
| `uitars-72b-dpo`, `opencua-72b` | 4 | 4 |
| `qwen3-vl-235b-a22b` | 8 | 8 |

Переопределяется без правки кода: `python -m bench_eval.agents.cli.serve <model> --tp N --max-model-len N`.

---

## Ограничения

- Модели обучались на десктопных скриншотах; здесь им показывают браузерный вьюпорт. Описание среды в промптах переписано под браузер, схемы инструментов и формат ответа оставлены как в обучении.
- `hf_repo` в реестре — ориентир; для `evocua-*` id чекпоинта нужно подтвердить и передать `--model-path`.
- Задачи с загрузкой файлов требуют полного Chromium (см. `AGENT_DOWNLOADS_ENABLED` в [EVAL_README.md](./EVAL_README.md)); исполнитель сохраняет скачанное в `downloads_dir` из конфига бенча.

---

## Тесты

```bash
pytest tests/agents/
```

Парсеры каждого семейства, реестр, пересчёт координат и цикл шагов — без GPU, vLLM и браузера.
