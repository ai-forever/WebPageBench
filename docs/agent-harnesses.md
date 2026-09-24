# Агентные harness-фреймворки: обзор и применимость к WebPageBench

Сводка по публичным agent harness — runtime-оболочкам вокруг LLM (планирование, инструменты, память, субагенты, песочница, human-in-the-loop). Отдельно — пригодность для mock-сайтов **WebPageBench**.

---

## Терминология

| Понятие | Смысл |
|---|---|
| **Framework** (LangChain, LangGraph) | Библиотека для сборки пайплайнов |
| **Harness** (DeepAgents, Hermes, OpenClaw) | Готовый runtime: как агент живёт, вызывает tools, хранит память |
| **Browser use** | Управление реальным браузером: навигация, клики, формы, DOM/скриншоты |

---

## Запрошенные системы

| Система | Краткое описание | Browser use | Лицензия | Ссылка |
|---|---|---|---|---|
| **Hermes Ouroboros** | Self-improving multi-agent council (Advocate, Skeptic, Oracle, Contrarian, Arbiter); SDK для планирования перед browser-use | ⚠️ Нет нативного браузера — используется как planning harness поверх browser-use | MIT | [github.com/Ridwannurudeen/hermes-ouroboros](https://github.com/Ridwannurudeen/hermes-ouroboros) |
| **Hermes Agent** | Автономный self-hosted harness от Nous Research: persistent memory, автогенерация skills, cron, субагенты, 5 sandbox-бэкендов, gateway в Telegram/Discord/Slack/WhatsApp/CLI | ✅ Встроенный — Browser Harness (CDP/Chromium), интеграция с Browser Use Cloud | MIT | [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| **OpenClaw** | Personal AI assistant (бывш. ClawdBot/Moltbot): gateway-centric архитектура, мессенджеры, heartbeat/cron, skills, memory в Markdown | ✅ Встроенный — изолированный Chromium, CDP, Chrome extension relay | Custom | [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw) |
| **DeepAgents** | Agent harness от LangChain: планирование, файловая система, субагенты, long-term memory, HITL; на LangGraph | ⚠️ Нет нативного браузера — через tools/MCP (Browserbase, Stagehand, Playwright MCP) | MIT | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |
| **OpenManus** | Open-source альтернатива Manus: planner–executor, multi-agent, MCP; от MetaGPT/FoundationAgents | ✅ Встроенный — `BrowserUseTool` на Playwright (+ vision) | MIT | [github.com/FoundationAgents/OpenManus](https://github.com/FoundationAgents/OpenManus) |

---

## Дополненный список

### Универсальные agent harness

| Система | Краткое описание | Browser use | Лицензия | Ссылка |
|---|---|---|---|---|
| **Claude Agent SDK** | Программируемый harness Anthropic (тот же loop, что Claude Code) | ✅ Через MCP — Playwright MCP, Browser Harness | Proprietary SDK | [code.claude.com/docs](https://code.claude.com/docs/en/agent-sdk/overview) |
| **OpenAI Codex** | Agentic harness OpenAI: multimodal, computer use, web search, CLI/TUI/IDE | ✅ Встроенный — browser/computer use | Proprietary | [openai.com/codex](https://openai.com/codex) |
| **OpenAI Agents SDK** | Python/TS SDK: tools, handoffs, tracing; Computer Use | ✅ Через Computer Use — Playwright, Browserbase, Daytona | MIT | [github.com/openai/openai-agents-python](https://github.com/openai/openai-agents-python) |
| **Open SWE** | Async coding agent на Deep Agents/LangGraph: sandboxes, Slack/Linear, auto-PR | ❌ Код/репозитории | Apache-2.0 | [github.com/langchain-ai/open-swe](https://github.com/langchain-ai/open-swe) |
| **SWE-agent** | Автономное решение GitHub issues / CTF | ❌ Shell + git | MIT | [github.com/SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) |
| **MetaGPT** | Multi-agent «software company»: SOP, роли PM/architect/engineer | ⚠️ Опционально через toolkits | MIT | [github.com/FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) |
| **OWL** (CAMEL-AI) | Multi-agent automation на CAMEL, 30+ toolkits | ✅ `BrowserToolkit` (Playwright) | Apache-2.0 | [github.com/camel-ai/owl](https://github.com/camel-ai/owl) |
| **smolagents** | Минималистичный harness от Hugging Face: CodeAgent / ToolCallingAgent | ✅ CLI `webagent` (Helium/Selenium) | Apache-2.0 | [github.com/huggingface/smolagents](https://github.com/huggingface/smolagents) |
| **Magentic-UI** | Human-in-the-loop web agent от Microsoft (AutoGen + WebSurfer) | ✅ WebSurfer (Playwright в sandbox) | MIT | [github.com/microsoft/magentic-ui](https://github.com/microsoft/magentic-ui) |

### Browser-first harness / browser automation для агентов

| Система | Краткое описание | Browser use | Лицензия | Ссылка |
|---|---|---|---|---|
| **Browser Use** | Python agent framework: observe–plan–act, Playwright, vision+DOM, cloud | ✅ Core product | MIT | [github.com/browser-use/browser-use](https://github.com/browser-use/browser-use) |
| **Browser Harness** | Тонкий self-healing CDP-harness от Browser Use | ✅ Core product | MIT | [github.com/browser-use/browser-harness](https://github.com/browser-use/browser-harness) |
| **Skyvern** | Vision+LLM browser automation: CAPTCHA/2FA, proxy, workflow builder, MCP | ✅ Core product | AGPL-3.0 | [github.com/Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) |
| **Stagehand** | Hybrid framework (Browserbase): `act` / `extract` / `observe`, CDP-native | ✅ Core product | MIT | [github.com/browserbase/stagehand](https://github.com/browserbase/stagehand) |
| **Playwright MCP** | MCP-сервер Microsoft: browser tools для MCP-агентов | ✅ Browser layer (tool surface) | Apache-2.0 | [github.com/microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) |
| **agent-browser** (Vercel) | Rust CLI: snapshot + refs (`@e1`), компактный вывод | ✅ Browser CLI | Apache-2.0 | [github.com/vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) |
| **Browserbase** | Managed cloud browsers + Stagehand MCP | ✅ Infrastructure + MCP | Commercial | [browserbase.com](https://www.browserbase.com) |

---

## Применимость к mock'ам WebPageBench

В WebPageBench агент **не сам себя оценивает**. Успех — Event-Match Score по логу типизированных событий. Схема:

1. `client.create_track(...)` — поднять среду с конфигом
2. Агент открывает `http://localhost:5173/<track_id>`
3. Действия пишутся в телеметрию бэкенда
4. `client.check(track_id, ...)` — проверка событий (`basket_add`, `bench_files_download`, …)

### Критерии пригодности

| Критерий | Зачем в WebPageBench |
|---|---|
| Локальный браузер (`localhost:5173`) | Mock'и не в публичном интернете |
| Playwright / CDP | SPA на Vue с динамическим JS |
| Программируемый runner (Python) | Batch-прогон как в `tests.py` |
| Multi-step planning | «найти товар → корзина → оплата» |
| Headless | Сотни задач в `tests/*/tasks/` |
| Без обязательного HITL | Автоматическая проверка через API |

### Рекомендуемые

| Harness | Почему подходит | Оговорки |
|---|---|---|
| **Browser Use** | Python, Playwright, agent loop; типичный выбор для web-agent бенчмарков | Нужен LLM API; для batch — свой wrapper |
| **Browser Harness** | Тонкий CDP, локальный Chrome | Скорее browser-layer, чем полный orchestrator |
| **OpenManus** | `BrowserUseTool` на Playwright, planner–executor | Тяжелее Browser Use |
| **OWL** | `BrowserToolkit`, multi-tool | Research-framework |
| **Playwright MCP** + Claude SDK / DeepAgents | MCP + Python-runner, встраивается в `tests.py` | Браузер через MCP |
| **agent-browser** + coding harness | Локальный CLI, низкий расход контекста | Нужен внешний agent loop |
| **Stagehand** (local) | Self-healing, гибрид code + NL | Часто тянет Browserbase |
| **smolagents** (`webagent`) | Минимальный Python | Слабее на сложных SPA |

**Практичные стеки:**

```text
tests.py (create_track + check)
    → Browser Use / OpenManus / OWL
    → Playwright → http://localhost:5173/<track_id>
```

```text
tests.py → DeepAgents / Claude Agent SDK + Playwright MCP
```

### Условно подходят

| Harness | Почему «условно» |
|---|---|
| **DeepAgents** | Браузера нет из коробки; нужны Playwright MCP / Browserbase |
| **Claude Agent SDK** | Proprietary; удобен как eval-runner |
| **OpenAI Codex / Agents SDK** | Сильный, но закрытый и дороже в batch |
| **Hermes Agent** | Browser Harness есть, но фокус на gateway/Telegram |
| **OpenClaw** | Personal assistant; неудобно гонять сотни track'ов |
| **Skyvern** | Заточен под реальные сайты; для локальных mock'ов избыточен |

### Не подходят

| Harness | Причина |
|---|---|
| **SWE-agent**, **Open SWE** | Код/git, не браузер |
| **MetaGPT** | Multi-agent «software company», не web UI |
| **Magentic-UI** | Human-in-the-loop — ломает автоматический batch |
| **Browserbase** (как harness) | Cloud; `localhost:5173` с удалённого браузера — отдельная настройка |

### Запрошенные четверо — итог для WebPageBench

| Система | Для mock-сайтов WebPageBench |
|---|---|
| **Hermes Agent** | ⚠️ Можно, но overkill |
| **OpenClaw** | ⚠️ Можно, но неудобно для batch eval |
| **DeepAgents** | ✅ С Playwright MCP / browser-tools |
| **OpenManus** | ✅ Один из лучших open-source вариантов |

### Особенности mock'ов WebPageBench

По задачам в `tests/bench` (Маркет, Книги, Продукты, Поезда, Отели, Файлы):

- **Поиск по тексту** — опечатки, фильтры (`*Typo*` tasks)
- **Формы** — логин, телефон, SMS, оплата (`login_data` в конфиге)
- **Многошаговые SPA** — `state_changed`, корзина, скачивание PDF
- **localStorage** — нужен реальный браузер, не HTTP-fetch

**Приоритет:** Browser Use → OpenManus → OWL → Playwright MCP + DeepAgents/Claude SDK.

### Минимальная интеграция

```python
# 1. Поднять track
client.create_track(name=..., id=track_id, filepath=..., address="localhost:9000")

# 2. Задача + credentials из config
task = test["test_data"]["task"].replace("%HOST%", f"http://127.0.0.1:5173/{track_id}")
login = test["test_data"].get("login_data", {})

# 3. Запустить harness (псевдокод)
# agent.run(f"{task}\nЛогин: {login}")

# 4. Проверить результат через API, не self-report агента
client.check(track_id, "localhost:9000")
```

---

## Выбор по сценарию

| Сценарий | Что смотреть |
|---|---|
| Personal assistant + мессенджеры + браузер | OpenClaw, Hermes Agent |
| Open-source «как Manus» | OpenManus, OWL |
| Свой harness на Python | DeepAgents, smolagents |
| Только веб-автоматизация | Browser Use, Skyvern, Stagehand |
| Браузер в существующего агента | Playwright MCP, agent-browser, Browser Harness |
| Coding agent | Claude Agent SDK, Codex, Open SWE, SWE-agent |
| Human-in-the-loop в браузере | Magentic-UI |
| **Batch-eval на mock'ах WebPageBench** | Browser Use, OpenManus, OWL, Playwright MCP + DeepAgents |

---

## Заметки

1. В 2026 заметен сдвиг **framework → harness** (Browser Use → Browser Harness как «anti-framework» с прямым CDP).
2. Успех в WebPageBench определяет **Event-Match Score** по событиям бэкенда, не Completion агента.
3. В WebPageBench eval запускается через DeepEval и `AGENT_HARNESS` — см. [EVAL_README.md](./EVAL_README.md).

---

## Реализация в WebPageBench

Актуальная матрица `AGENT_HARNESS`, требования и команды запуска находятся в
[EVAL_README.md](./EVAL_README.md#harness). Screenshot-only модели и их action
space описаны в [gui-agents.md](./gui-agents.md).

Остальные системы в таблицах выше — обзор экосистемы; их интеграция в
WebPageBench не предполагается автоматически.
