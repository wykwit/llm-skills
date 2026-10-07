#!/usr/bin/env bash
# Install llm-skills on this machine. Idempotent: re-run after every `git pull`.
#
#   1. lint every skill (aborts on problems)
#   2. symlink skills/<name> into the shared hub (~/.agents/skills), pruning
#      links for skills removed from the repo
#   3. wire harnesses that do not read the hub natively (hermes)
#
# omp, opencode and openclaw read ~/.agents/skills on their own.
# Override the hub with SKILLS_HUB=/path ./install.sh
set -euo pipefail

repo="$(cd "$(dirname "$0")/../" && pwd)"
hub="${SKILLS_HUB:-$HOME/.agents/skills}"

echo "== lint"
"$repo/tools/lint.py"

echo "== link into $hub"
SKILLS_HUB="$hub" "$repo/tools/link.sh" --prune

echo "== harnesses"
status=0
hermes_home="${HERMES_HOME:-$HOME/.hermes}"
if [ -d "$hermes_home" ]; then
  python3 "$repo/tools/wire-hermes.py" "$hermes_home/config.yaml" "$hub" || status=1
else
  echo "hermes: not installed ($hermes_home missing), skipped"
fi

if [ -n "${OPENCLAW_STATE_DIR:-}" ] && [ "$OPENCLAW_STATE_DIR" != "$HOME/.openclaw" ]; then
  echo "openclaw: WARNING non-default OPENCLAW_STATE_DIR; openclaw skips ~/.agents/skills." >&2
  echo "          add \"$hub\" to skills.load.extraDirs in its config." >&2
fi
if [ "$hub" != "$HOME/.agents/skills" ]; then
  echo "NOTE: custom hub; omp/opencode/openclaw only read ~/.agents/skills by default." >&2
  echo "      point omp skills.customDirectories, opencode skills.paths and" >&2
  echo "      openclaw skills.load.extraDirs at $hub" >&2
fi

echo "== done: $(find "$hub" -maxdepth 1 -type l -lname "$repo/skills/*" | wc -l) repo skills linked"
echo "restart running harness sessions to pick up changes"
[ "$status" -eq 0 ] || echo "finished with manual steps pending (see above)" >&2
exit "$status"
