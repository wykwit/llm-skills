#!/usr/bin/env bash
# Remove this repo's skills from the shared hub. Only symlinks that point into
# this checkout are removed; third-party skills in the hub are untouched.
#
# hermes' skills.external_dirs entry is left in place: the hub still serves
# third-party skills. Remove it from ~/.hermes/config.yaml by hand if unwanted.
set -euo pipefail

repo="$(cd "$(dirname "$0")" && pwd)"
hub="${SKILLS_HUB:-$HOME/.agents/skills}"

removed=0
for dest in "$hub"/*; do
  [ -L "$dest" ] || continue
  case "$(readlink "$dest")" in
    "$repo"/skills/*) rm "$dest"; echo "unlinked $(basename "$dest")"; removed=$((removed + 1)) ;;
  esac
done
echo "removed $removed repo skill link(s) from $hub"
