# Variant: openclaw

Scheduler: openclaw automations (cron) via the agent's automations tool. Inspect the tool schema in-session before use; field names below match the current tool.

## Create

| Field | Value |
|---|---|
| name | `<NAME>` |
| schedule | `{"kind": "every", "everyMs": 1800000}` (30 min) |
| sessionTarget | `isolated` (stateless cycles) |
| delivery | none (silent; never posts into the parent conversation) |
| deleteAfterRun | `false` |
| toolsAllow | `exec, read, write, apply_patch` (REVIEW-ONLY: drop `apply_patch`) |
| payload | the filled brief |

Then:

1. List automations; record the returned job ID in state and in the brief (update the job payload if the ID was unknown at create time).
2. Force the first cycle: `run` with `runMode: force`. Read `<REPORT_DIR>/<NAME>_log.md`; no line means the job is not working.

## Auth inside cycles

Isolated cycles may not inherit your shell env. If the brief needs it, start with `source ~/.bash_profile` (or whichever file exports `GH_TOKEN` / `GITLAB_TOKEN`), and prove it in the forced cycle.

If a GitLab token starts returning 401 mid-job: an `oauth2:<token>@` remote URL in the clone may hold a working token. Verify with `GET /api/v4/user` before use; it may still lack rights to resolve threads or approve (403). Log that limit, do not loop.

## Disable command for the brief

Isolated cycles may lack the automations tool. Give the cycle a way to stop itself that you verified during setup (automations tool `update` with `enabled: false` on `<JOB_ID>`, or the gateway CLI equivalent). If none is available inside cycles, the terminal step writes the final report and every later run exits at step 1; tell the user the job must be disabled by hand.
