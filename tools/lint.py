#!/usr/bin/env python3
"""Lint skills/ against the portable Agent-Skills intersection.

Checks per skills/<name>/:
- SKILL.md exists with frontmatter that strict YAML parsers accept
- name matches the directory name, kebab-case, <=64 chars
- description present, <=1024 chars
- only spec top-level keys plus disable-model-invocation (honoured by omp
  and openclaw); other harness extras nest under metadata:
- SKILL.md body <= 500 lines (spec guidance; push detail into sibling files)
- relative Markdown links in the skill's .md files resolve inside the skill
- bundled scripts parse: *.py compiles, *.sh passes `bash -n`
"""
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("lint.sh needs PyYAML (python3-yaml / pip install pyyaml)")

SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools",
             "disable-model-invocation"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

MAX_BODY_LINES = 500
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

root = Path(__file__).resolve().parent.parent / "skills"
skills = sorted(p for p in root.iterdir() if p.is_dir())
if not skills:
    sys.exit("no skills found under skills/")

fail = 0
for d in skills:
    def err(msg):
        global fail
        fail += 1
        print(f"FAIL {d.name}: {msg}", file=sys.stderr)

    f = d / "SKILL.md"
    if not f.is_file():
        err("missing SKILL.md")
        continue
    text = f.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        err("no YAML frontmatter")
        continue
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        err(f"invalid YAML frontmatter: {e}".replace("\n", " "))
        continue
    if not isinstance(fm, dict):
        err("frontmatter is not a mapping")
        continue

    name = fm.get("name", d.name)
    if name != d.name:
        err(f"name {name!r} != dir {d.name!r}")
    if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
        err(f"bad name {name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        err("missing description")
    elif len(desc) > 1024:
        err(f"description {len(desc)} chars > 1024")
    extra = sorted(set(fm) - SPEC_KEYS)
    if extra:
        err(f"non-portable top-level keys: {extra}")
    if "metadata" in fm and not isinstance(fm["metadata"], dict):
        err("metadata must be a mapping")

    body_lines = text[m.end():].count("\n")
    if body_lines > MAX_BODY_LINES:
        err(f"SKILL.md body {body_lines} lines > {MAX_BODY_LINES}")

    for md in sorted(d.rglob("*.md")):
        for target in LINK_RE.findall(md.read_text(encoding="utf-8")):
            path = target.split("#", 1)[0]
            if not path or re.match(r"^[a-z][a-z0-9+.-]*:", path):
                continue  # in-page anchor or URL
            dest = (md.parent / path).resolve()
            if not dest.is_relative_to(d.resolve()) or not dest.exists():
                err(f"{md.relative_to(d)}: broken link {target!r}")

    for py in sorted(d.rglob("*.py")):
        try:
            compile(py.read_text(encoding="utf-8"), str(py), "exec")
        except SyntaxError as e:
            err(f"{py.relative_to(d)}: {e.msg} (line {e.lineno})")
    for sh in sorted(d.rglob("*.sh")):
        r = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
        if r.returncode:
            err(f"{sh.relative_to(d)}: {r.stderr.strip()}")

print(f"{len(skills)} skills checked, {fail} problem(s)")
sys.exit(1 if fail else 0)
