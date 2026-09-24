# UI-TARS

Нативный GUI-агент: мысль + одно действие компактного DSL за шаг.

| | |
|---|---|
| Формат | `Thought: …` / `Action: click(start_box='<\|box_start\|>(x,y)<\|box_end\|>')` |
| Действия | click, left_double, right_single, drag, hotkey, type, scroll, wait, finished, call_user |
| Координаты | `uitars-1.5-7b` — `resized`; `uitars-7b-dpo`, `uitars-72b-dpo` — сетка 0..1000 |

```bash
python -m bench_eval.agents.cli.serve uitars-1.5-7b       # или ../serve/serve_uitars.sh
MODEL=uitars-72b-dpo TP=4 ../serve/serve_uitars.sh
./scripts/run_eval.sh uitars/uitars-1.5-7b
```

Опции: `UITARS_LANGUAGE` (язык блока Thought), `UITARS_USE_THOUGHT`, `UITARS_ALLOW_CALL_USER`.

`type(content='…\n')` означает «ввести и отправить» — исполнитель нажимает Enter на каждом переводе строки.
