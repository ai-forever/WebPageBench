---
title: WebPageBench
emoji: 🌐
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.9.0
app_file: app.py
python_version: "3.12"
pinned: false
license: apache-2.0
tags:
- leaderboard
short_description: WebPageBench leaderboard — Event-Match Score
---

# WebPageBench Leaderboard

Источник для Hugging Face Space: [ai-forever/WebPageBench](https://huggingface.co/spaces/ai-forever/WebPageBench).

## Генерация

```bash
# из корня репозитория — после прогона eval
./scripts/export_leaderboard.sh
cd liderboard && python app.py
```

## Метрики

Основная — **Event-Match Score (EMS)** (`run.success_rate` из `results.json`): доля задач, где все `conditions` совпали с типизированными событиями лога. Рядом публикуется **Completion** (`agent_completion_rate`) — заявление harness, что задача закончена. См. [EVAL_README.md](../docs/EVAL_README.md) и [description.md](./docs/description.md).
