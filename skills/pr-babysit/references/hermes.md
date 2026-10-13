# Variant: hermes

Scheduler: `hermes cron`. Run all commands via the terminal tool; re-check `hermes cron create --help` before setup, flags drift.

## Create (paused first, so the ID lands in the brief before any run)

```sh
hermes cron create 30m "<placeholder brief>" \
  --name <NAME> --paused --workdir <WORKDIR> \
  --deliver local --failure-deliver local \
  [--model <MODEL> --provider <PROVIDER>]   # only if the user asked for a route
hermes cron list --all                      # find the returned job ID
hermes cron edit <JOB_ID> --prompt "$(cat <REPORT_DIR>/<NAME>_brief.md)"
hermes cron resume <JOB_ID>
hermes cron run <JOB_ID>                    # queued for the next tick, not synchronous
```

- `--deliver local` keeps cycles silent; routine output never reaches chat. For an authorized notification channel, the brief sends the notice itself; delivery stays `local`.
- `hermes cron list` has no JSON output. For a readback of the stored prompt/workdir, read the profile's `cron/jobs.json` and select the exact ID. Never hand-edit it.
- Same-name jobs may exist (paused/completed). Never attach to one by name.
- `--model` alone does not disable the CLI fallback chain; if an exact route matters, verify it from the first cycle's run record, not from flags.

## Disable command for the brief

Cron management tools are disabled inside cron runs; the cycle uses the terminal:

```sh
hermes cron pause <JOB_ID>     # default terminal outcome; verify with: hermes cron list --all
hermes cron remove <JOB_ID>    # only if the user authorized removal
```

Never use fleet-wide `hermes pause`, and never touch another ID.

## Long fixes

A cron agent run is bounded by the scheduler. If IMPLEMENT fixes need more time, do not background a process from the cron agent: it dies with the run and leaves state stuck at `running`. Instead make the job `--script <wrapper> --no-agent` (wrapper in `~/.hermes/scripts/`) that runs the cycle in the foreground with `flock -n` and a hard `timeout`, e.g. `hermes chat --oneshot --query-file <brief> --in <WORKDIR> --run-budget <s>`. Keep `cron.script_timeout_seconds` above that timeout.
