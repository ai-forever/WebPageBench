# Публикация на Hugging Face

Скопируйте **всё содержимое** `liderboard/` в репозиторий Space [ai-forever/WebPageBench](https://huggingface.co/spaces/ai-forever/WebPageBench).

## Перед публикацией

Из корня репозитория:

```bash
python liderboard/src/export_results.py
```

Это обновит `liderboard/results/` из последних прогонов в `tests/eval/` (та же логика discovery, что у `scripts/render_eval_aggregate.py`). Старые файлы в `results/` удаляются перед экспортом.

## Push

Локальный клон Space (не субмодуль, в `.gitignore`). Клонируйте один раз рядом с репозиторием или укажите свой путь:

```bash
# один раз (если ещё нет)
git clone https://huggingface.co/spaces/ai-forever/WebPageBench ../WebPageBench-space
```

Синхронизировать в локальный клон Space только файлы из последнего коммита:

```bash
./scripts/sync_liderboard_to_webpagebench.sh /path/to/WebPageBench-space
```

Затем в каталоге Space:

```bash
cd /path/to/WebPageBench-space
git add -A
git commit -m "Update WebPageBench leaderboard"
git push -u origin main
```

Используйте [HF write token](https://huggingface.co/settings/tokens) вместо пароля.

## SSR / Python 3.13 на Hugging Face

Если в логах Space видно `with SSR ⚡` и `ValueError: Invalid file descriptor: -1`, отключите SSR:

```bash
hf spaces variables add ai-forever/WebPageBench --env GRADIO_SSR_MODE=false
```

На HF `launch(ssr_mode=False)` **игнорируется** — нужна переменная окружения. В `app.py` она также выставляется до импорта Gradio; в `README.md` зафиксирован `python_version: "3.12"`.
