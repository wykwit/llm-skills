#!/usr/bin/env python3
"""Ensure hermes' config lists the skills hub in skills.external_dirs.

Usage: wire-hermes.py <config.yaml> <hub-dir>

Edits text, never round-trips YAML, so comments and layout survive:
- hub already listed (after ~ / $VAR expansion): nothing to do
- no top-level `skills:` key: append a `skills:` block
- `skills:` exists without the hub: print the line to add and exit 1, rather
  than guess at merging into hand-edited config
"""
import os
import sys
from pathlib import Path

import yaml

cfg_path, hub = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
home = Path.home()
hub_entry = "~/" + str(hub.relative_to(home)) if hub.is_relative_to(home) else str(hub)

text = cfg_path.read_text(encoding="utf-8") if cfg_path.exists() else ""
cfg = yaml.safe_load(text) or {}
if not isinstance(cfg, dict):
    sys.exit(f"hermes: {cfg_path} is not a YAML mapping; add skills.external_dirs by hand")

skills = cfg.get("skills")
dirs = (skills.get("external_dirs") or []) if isinstance(skills, dict) else []
for entry in dirs:
    if Path(os.path.expandvars(os.path.expanduser(str(entry)))).resolve() == hub:
        print(f"hermes: {cfg_path} already lists {hub_entry}")
        sys.exit(0)

if "skills" in cfg:
    print(f"hermes: {cfg_path} has a skills: section without the hub. Add by hand:\n"
          f"  skills:\n    external_dirs:\n      - \"{hub_entry}\"", file=sys.stderr)
    sys.exit(1)

block = (
    "\n# llm-skills: shared cross-harness skill hub (added by llm-skills install.sh)\n"
    "skills:\n"
    "  external_dirs:\n"
    f"    - \"{hub_entry}\"\n"
)
sep = "" if not text or text.endswith("\n") else "\n"
cfg_path.parent.mkdir(parents=True, exist_ok=True)
with cfg_path.open("a", encoding="utf-8") as fh:
    fh.write(sep + block)
yaml.safe_load(cfg_path.read_text(encoding="utf-8"))  # fail loudly if we broke it
print(f"hermes: added {hub_entry} to skills.external_dirs in {cfg_path}")
