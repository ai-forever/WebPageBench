# Qwen3-VL

Одностадийная computer-use модель: планирование и grounding в одном вызове.

| | |
|---|---|
| Формат | `Action: <одно предложение>` + `<tool_call>{"name":"computer_use","arguments":{…}}</tool_call>` |
| Действия | key, type, mouse_move, left_click, left_click_drag, right_click, middle_click, double_click, scroll, wait, terminate |
| Координаты | абсолютные пиксели resized-изображения (`resized`); `GUI_AGENT_COORDINATE_SPACE=relative999` — сетка 0..999 |
| Патч-сетка | `factor=32` (не 28, как у qwen2.5-VL) |

```bash
python -m bench_eval.agents.cli.serve qwen3-vl-8b     # или ../serve/serve_qwen3_vl.sh
./scripts/run_eval.sh qwen3-vl/qwen3-vl-8b
```

Чекпоинты: `qwen3-vl-4b`, `qwen3-vl-8b`, `qwen3-vl-32b`, `qwen3-vl-30b-a3b`, `qwen3-vl-235b-a22b`.

Схема инструмента совпадает с обучающей — менять её не стоит, это заметно портит grounding. Адаптировано только описание среды: браузерный вьюпорт вместо Ubuntu-десктопа.
