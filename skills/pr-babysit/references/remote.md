# Variant: remote

Same mechanism as [local](local.md) (systemd user timer + wrapper + headless agent CLI), installed on an SSH host so the watch survives this machine sleeping.

## Extra setup on the host

1. `ssh <HOST>`: confirm the agent CLI, `gh`/`glab`, `flock`, `timeout` exist, and auth works **as the host user** (`gh auth status` / `glab auth status`). Never copy tokens from this machine without asking.
2. Clone or reuse a checkout on the host; `<WORKDIR>` and `<REPORT_DIR>` are host paths. Check out the head branch and the push remote there.
3. `loginctl enable-linger <user>` (or confirm `loginctl show-user <user> -p Linger` is `yes`), otherwise user timers stop at logout.
4. Write the brief, wrapper and units on the host (e.g. `scp` or heredoc over `ssh`), then run the local setup commands via `ssh <HOST> '…'`.
5. Forced cycle: `ssh <HOST> systemctl --user start <NAME>.service`, then `ssh <HOST> tail -n1 <REPORT_DIR>/<NAME>_log.md`.

Record `HOST` in state and in the brief. Job ID = `<HOST>:<NAME>.timer`.

## Checking in

```sh
ssh <HOST> tail -n 20 <REPORT_DIR>/<NAME>_log.md
ssh <HOST> cat <REPORT_DIR>/<NAME>_final.md
```

## Disable command for the brief

Runs on the host itself:

```sh
systemctl --user disable --now <NAME>.timer
systemctl --user is-enabled <NAME>.timer   # expect: disabled
```

To stop it from here: `ssh <HOST> systemctl --user disable --now <NAME>.timer`.
