# OpenCUA

Markdown-секции с настраиваемой глубиной рассуждения + pyautogui-код.

| | |
|---|---|
| Формат | `## Observation` / `## Thought` / `## Action` / `## Code` + ```` ```python ```` |
| Действия | pyautogui + `computer.wait`, `computer.triple_click`, `computer.terminate` |
| Координаты | нормированные 0..1 (`relative`); у `opencua-72b` — сетка qwen2.5-VL (`qwen25`) |

```bash
python -m bench_eval.agents.cli.serve opencua-7b       # или ../serve/serve_opencua.sh
OPENCUA_COT_LEVEL=l3 ./scripts/run_eval.sh opencua/opencua-7b
```

| Опция | Значения |
|-------|----------|
| `OPENCUA_COT_LEVEL` | `l1` (только действие), `l2` (мысль + действие, по умолчанию), `l3` (+ наблюдение) |
| `OPENCUA_HISTORY_TYPE` | `action_history`, `thought_history`, `observation_history` |

Чекпоинты требуют `--trust-remote-code` — он уже прописан в `VLLMSpec`.
