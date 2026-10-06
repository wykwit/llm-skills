#!/usr/bin/env bash
# A2 wiring: symlink every first-party skill in ./skills into the shared hub
# (~/.agents/skills by default). Third-party skills installed in the hub by
# other tools (npx skills) are left untouched.
#
# Usage: tools/link.sh [--prune]
#   --prune  also remove hub symlinks that point into this repo but no longer
#            match a skill directory here
#
# Run after `git pull` on any machine; re-running is idempotent.
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
hub="${SKILLS_HUB:-$HOME/.agents/skills}"
prune=false
[ "${1:-}" = "--prune" ] && prune=true

mkdir -p "$hub"
for dir in "$repo"/skills/*/; do
  name="$(basename "$dir")"
  if [ ! -f "$dir/SKILL.md" ]; then
    echo "skip $name: no SKILL.md" >&2
    continue
  fi
  dest="$hub/$name"
  if [ -L "$dest" ] || [ ! -e "$dest" ]; then
    ln -sfn "${dir%/}" "$dest"
    echo "linked $name"
  else
    echo "SKIP $name: hub entry exists and is not a symlink" >&2
  fi
done

if $prune; then
  for dest in "$hub"/*; do
    [ -L "$dest" ] || continue
    case "$(readlink "$dest")" in "$repo"/skills/*) ;; *) continue ;; esac
    name="$(basename "$dest")"
    if [ ! -d "$repo/skills/$name" ]; then
      rm "$dest"
      echo "pruned $name"
    fi
  done
fi
