# Memory registry — WebPageBench drive

Source-of-truth map for what this Ouroboros instance can rely on during WebPageBench runs.

## Core memory (present after seeding)

| Path | Status | Purpose |
|------|--------|---------|
| `memory/identity.md` | seeded | Who I am in this benchmark |
| `memory/WORLD.md` | seeded | Environment and constraints |
| `memory/registry.md` | seeded | This index |
| `memory/knowledge/` | seeded (partial) | Stable benchmark facts |

## Runtime paths (created by harness / Ouroboros)

| Path | Status | Purpose |
|------|--------|---------|
| `state/` | runtime | Benchmark markers, evolution logs |
| `logs/` | runtime | Task and tool traces (when Ouroboros writes them) |
| `memory/scratchpad.md` | absent until use | Working notes for the current task |
| `memory/knowledge/patterns.md` | absent until use | Error-pattern register |
| `memory/knowledge/improvement-backlog.md` | absent until use | Post-task improvement notes |

## External references (not copied into drive)

| Resource | Location |
|----------|----------|
| Mock sites | Operator-managed WebPageBench backend |
| Eval dataset | `EVAL_DATASET_PATH` in the repo |
| Ouroboros gateway | `OUROBOROS_URL` when full modes are used |

## Lookup rule

If a fact is not listed above and not visible in the current browser session, treat it as **unknown** until observed or read from an allowed path.
