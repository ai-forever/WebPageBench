# WORLD — WebPageBench environment

## Runtime context

| Field | Value |
|-------|-------|
| Harness | WebPageBench |
| Task surface | De-branded mock browser sites (marketplace, books, grocery, rail, hotels, files) |
| Data root | Per-task or shared `ouroboros_drive/<EVAL_TRACK_SUFFIX>/` under eval output |
| Identity seed | Bundled `configs/ouroboros/seed/memory/` (auto) unless overridden |

## What exists here

- **Browser tasks** on synthetic e-commerce / booking / checkout / document-cabinet flows.
- **Isolated benchmark drive** under `OUROBOROS_DATA_DIR` — not a production machine.
- **Optional evolution** between tasks when `full_evolving` mode is enabled.

## What does not exist here

- Real customer PII, payment rails, or production credentials.
- Long-lived operator chat history from a desktop Ouroboros install (unless copied in).
- Guaranteed network access beyond what the eval operator configured.

## Interaction model

1. Read the task prompt (golden).
2. Plan briefly, then act in the browser.
3. Verify page state matches the goal.
4. Return a concise final result for scoring.

Success is decided by Event-Match Score on typed backend events, not by this self-report.

## Safety defaults

- Use only credentials and test data provided by the mock site.
- Do not exfiltrate secrets from the eval environment.
- Prefer minimal, reversible UI actions over destructive experimentation.
