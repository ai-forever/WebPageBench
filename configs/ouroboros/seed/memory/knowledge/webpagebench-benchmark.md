# WebPageBench — stable facts

## Sites

Tasks run against **mock web applications** started by the WebPageBench stack. Six de-branded tabs: marketplace, books, grocery, rail, hotels, files. URLs, credentials, and product data are synthetic unless the task prompt states otherwise.

## Task format

- Each eval item provides a natural-language goal (golden prompt).
- Success is the Event-Match Score: typed events in the backend log must satisfy the task `conditions`. There is no judge model.
- Completion (calling `done`) is recorded separately and is not the verdict.
- The agent should finish with an explicit answer string when the task asks for one.

## Modes in this harness

| Mode | Drive | Evolution |
|------|-------|-----------|
| `ouroboros-cut` | Empty per-task drive | Off |
| `ouroboros-full-isolated` | Forked drive + identity seed per task | Off |
| `ouroboros-full-evolving` | Shared drive + identity seed | On between tasks |

## Practical tips

- Re-read labels and confirmation screens before submitting forms.
- After navigation, wait for the target element or URL pattern before the next action.
- When a flow has multiple steps (cart → checkout → confirm), complete the full chain.
