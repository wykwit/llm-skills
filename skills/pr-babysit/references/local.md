# Variant: local

Scheduler: a systemd **user** timer on this machine runs a headless agent CLI once per cycle. Nothing runs while the machine sleeps; use [remote](remote.md) if that matters.

## Files

`<REPORT_DIR>/<NAME>_brief.md` holds the brief. A wrapper adds the lock and a hard deadline:

```sh
# ~/.local/bin/<NAME>.sh
#!/usr/bin/env bash
set -euo pipefail
cd <WORKDIR>
exec flock -n <REPORT_DIR>/<NAME>.lock \
  timeout 25m <AGENT_CMD> "$(cat <REPORT_DIR>/<NAME>_brief.md)"
```

`<AGENT_CMD>` per harness (pick the one the user uses; default to omp; pin a model only if asked):

| Harness | Command |
|---|---|
| omp | `omp -p --auto-approve` |
| claude | `claude -p --permission-mode acceptEdits --allowedTools "Bash Read Edit Write"` |
| opencode | `opencode run --auto` |

REVIEW-ONLY: drop edit permissions where the CLI allows it.

```ini
# ~/.config/systemd/user/<NAME>.service
[Unit]
Description=<NAME>
[Service]
Type=oneshot
ExecStart=%h/.local/bin/<NAME>.sh
```

```ini
# ~/.config/systemd/user/<NAME>.timer
[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true
[Install]
WantedBy=timers.target
```

## Setup

```sh
chmod +x ~/.local/bin/<NAME>.sh
systemctl --user daemon-reload
systemctl --user enable --now <NAME>.timer
systemctl --user start <NAME>.service      # forced first cycle
journalctl --user -u <NAME>.service -n 50  # then check the log line
```

Job ID = `<NAME>.timer`. The service runs without your interactive shell env: confirm `gh`/`glab` auth works there (forced cycle proves it).

## Disable command for the brief

```sh
systemctl --user disable --now <NAME>.timer
systemctl --user is-enabled <NAME>.timer   # expect: disabled
```

Leave the unit files; the final report lists them so the user can delete them.
