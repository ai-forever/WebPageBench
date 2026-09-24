# EvoCUA

Два стиля промпта в одном семействе — переключаются `EVOCUA_PROMPT_STYLE`.

| Стиль | Формат | Координаты |
|-------|--------|------------|
| `S2` (по умолчанию) | `computer_use` tool calls, как у Qwen3-VL, плюс `triple_click`, `key_down`, `key_up` | `resized` |
| `S1` | markdown-секции + pyautogui-код, как у OpenCUA | `relative` (0..1) |

```bash
python -m bench_eval.agents.cli.serve evocua-s2        # или ../serve/serve_evocua.sh
EVOCUA_PROMPT_STYLE=S1 ./scripts/run_eval.sh evocua/evocua-s2
```

`key_down` исполняется как полное нажатие, парный `key_up` — как no-op: иначе одна комбинация нажалась бы дважды.

> `hf_repo` для `evocua-*` — заглушка. Сверьте id чекпоинта и передайте `--model-path /путь/к/весам` либо `MODEL_PATH=…` в скрипт запуска.
