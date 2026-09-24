# Jedi

Двухстадийная схема: планировщик пишет действие словами, grounder находит пиксель.

| Стадия | Что делает |
|--------|------------|
| Planner | `Observation:` / `Thought:` / одна строка pyautogui с `# описанием цели`; координаты в коде — заглушки |
| Grounder | Jedi-VL получает скриншот + описание и отвечает `computer_use` tool call с координатой |

```bash
python -m bench_eval.agents.cli.serve jedi-7b          # или ../serve/serve_jedi.sh
./scripts/run_eval.sh jedi/jedi-7b
```

По умолчанию планировщиком работает сама Jedi. Сильный внешний планировщик обычно даёт заметно лучший результат:

```bash
export JEDI_PLANNER_MODEL=gpt-5.5
export JEDI_PLANNER_BASE_URL=https://api.openai.com/v1
export JEDI_PLANNER_API_KEY=sk-...
```

Токены планировщика и grounder'а считаются в один ledger и попадают в `token_usage_by_model` отчёта раздельно.

Если grounder не вернул координату, действие **пропускается** — кликать по заглушке `(0, 0)` хуже, чем не кликать.
