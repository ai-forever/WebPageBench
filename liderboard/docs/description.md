# WebPageBench — лидерборд

Открытая среда оценки веб-агентов: успех задачи читается из лога типизированных событий интерфейса (**Event-Match Score**), без judge-модели и без скрейпинга страницы. Сюит — **152** задачи: 65 канонических сценариев и 87 вариантов контролов (светлая/тёмная тема) на **шести** обезличенных моках (маркет, книги, продукты, поезда, отели, файлы). «Главная» хаба — навигация, не отдельный набор задач. Интерфейсы, промпты и данные на русском; контракт верификации читает события, а не текст UI. Подробности: [EVAL_README.md](../../docs/EVAL_README.md).

Прогоны в `liderboard/results/` — канон **152** задачи (EMS = `passed_tasks` / 152; непрогнанные считаются 0). Публичный лидерборд: 24 пары модель–harness.

## Бенчмарк

Канонические сценарии (варианты наследуют раздел донора):

| Раздел | Ключ | Канон. | Вар. | Всего |
|--------|------|-------:|-----:|------:|
| Маркет | `shop` | 18 | 14 | 32 |
| Книги | `books` | 11 | 10 | 21 |
| Продукты | `grocery` | 8 | 2 | 10 |
| Поезда | `rail` | 9 | 17 | 26 |
| Отели | `hotels` | 8 | 37 | 45 |
| Файлы | `files` | 11 | 7 | 18 |
| **Итого** | | **65** | **87** | **152** |

Агент работает через harness с выбранной LLM на моках. **Оценённые** DOM-значения `AGENT_HARNESS` (6 конфигураций):

`browser-use`, `ouroboros-cut`, `ouroboros-full-isolated`, `ouroboros-full-evolving`, `openmanus`, `openhands`

Screenshot-only GUI (5 семейств): `qwen3-vl`, `uitars`, `opencua`, `evocua`, `fara`.

В раннере также есть `hermes-ouroboros`, `deepagents`, `jedi` — не входят в 24 пары лидерборда.

Вход, который harness кладёт в модель в этом прогоне:

| Вход | Когда |
|------|--------|
| `text` | `openhands`; text-only модели на Ouroboros (скриншот в LLM не инжектится); DeepSeek на `browser-use`/`openmanus` (только DOM) |
| `text+image` | `browser-use`, `openmanus`, `ouroboros-cut`, `ouroboros-full-*` (если модель видит скриншот) |
| `image` | GUI-harness: `qwen3-vl`, `uitars`, `opencua`, `evocua`, `fara` |

## Метрики лидерборда

### Основная: Event-Match Score (EMS)

| Поле | Источник | Описание |
|------|----------|----------|
| `success_rate` | `run.success_rate` | `passed_tasks / total_tasks` — среднее EMS по задачам |
| Успех задачи | `tests[].success` | Все `conditions` прошли (`dab_check.all_passed`) |

Не путать с **Completion** — агент мог вызвать `done`, но условия лога не выполнены. Разница Completion − EMS — *completion–verification gap* (на публичном лидерборде до 41 пункта).

### Скорость и эффективность

| Поле | Описание |
|------|----------|
| `avg_duration_seconds` | Среднее время задачи (create_track + agent + check) |
| `avg_agent_steps` | Среднее число шагов агента |
| `avg_tokens_per_task` | Средние токены на задачу |
| `total_cost_usd` | Оценка стоимости LLM (`bench_eval.llm_cost`); `---` если в submission нет цены |

### Надёжность

| Поле | Описание |
|------|----------|----------|
| `pass_at_k` | Pass@k по историческим прогонам (extended_metrics) |
| `agent_completion_rate` | Completion: доля задач с `agent_is_done` |
| `agent_dab_agreement_rate` | Согласие Completion и EMS |

Публичный submission хранит EMS, Completion, шаги, длительность и стоимость. Over-claim, under-claim и harness-error в файл не пишутся. Разбивка донор/вариант в submission нет, поэтому Δ по ключам UI не публикуется.

### UI-таксономия

Агрегаты `ui_taxonomy_stats` в `results.json`. В публичном submission — девять primary-классов (`ui_classes`): BASKET, COUNTER, FILES, FAV, CARD, DATE, PAY, SELECT_AC, SELECT_LIST. Классы с четырьмя и меньше задачами — диагностика, не рейтинг.

- `by_checked_class` — классы из `conditions`
- `by_primary` — главный класс задачи
- `by_ui_pattern` — реализации контролов (`date:popup_grid`, …)

## Виды лидерборда

1. **Success Rate** — EMS, основной рейтинг
2. **Speed** — `avg_duration_seconds` (меньше — лучше)
3. **Cost** — стоимость и value (EMS / $)

Фильтры **Input** (`text` / `text+image` / `image`) и **Harness** пересобирают основную таблицу, разделы, UI-таксономию и Metrics.

## Экспорт результатов

```bash
python liderboard/src/export_results.py
```

Берёт последний прогон с **более чем 5 задачами** (не smoke) для каждой пары model × harness из `tests/eval/`. Полный бенч — **152** задачи; порог экспорта по умолчанию отсекает smoke, см. `--min-tasks-for-aggregate` в `export_results.py` и `full_bench_min_tasks` в `bench_config.json`.

## Ссылки

- [Space](https://huggingface.co/spaces/ai-forever/WebPageBench)
- [Репозиторий](https://github.com/ai-forever/WebPageBench)
- [Задачи](https://github.com/ai-forever/WebPageBench/tree/main/tests/bench)
- [Таксономия](https://github.com/ai-forever/WebPageBench/blob/main/docs/TAXONOMY.md)
