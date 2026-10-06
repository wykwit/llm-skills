# Report spec

The JSON that `scripts/build_report.py` reads. String fields marked _HTML_ are inserted as-is, so use `<code>`, `<b>`, and escape `<`/`&` in code you quote.

```json
{
  "slug": "FS-1101",
  "title": "Short legs when a wall has an adapter",
  "base": "origin/master",
  "head": "HEAD",
  "out": "/tmp/fs-1101-walkthrough.html",
  "pills": ["T13 / V13 BAMBI+", "T14 PTERO+"],
  "summary": "Follow the data from drawer preprocessing to the final foot choice. …",
  "verification": "Focused tests not run: Docker could not read <code>shared/postgresql/pgdata</code>.",
  "steps": [
    {
      "title": "Pipeline order",
      "subtitle": "Why the adapter can be seen",
      "badge": "Core change",
      "tone": "neutral",
      "explain": "Wall feet used to be decided before drawer preprocessing. …",
      "bullets": ["T03 keyhole correction now sees post-preprocessing state."],
      "files": [
        "server/apps/geometry/docs/drawers.md",
        {"path": "server/apps/geometry/shelf_gallery/gallery_watty.py",
         "focus": ["_assign_wall_feet_info"], "note": "ordering"}
      ],
      "comment": "This dependency is necessary. An end-to-end test would protect the ordering."
    }
  ],
  "skip": [{"glob": "server/apps/manual/templates/assets/**", "reason": "SVG drawings, no logic"}],
  "checklist": {
    "blockers": [],
    "confirm": ["Ask: <b>should one-sided drawers without adapters get long feet too?</b> It changes output beyond FS-1101."],
    "not_blocking": ["Mixed-face test (adapter left, drawer right) would pin the precedence."]
  }
}
```

| Field | Required | Meaning |
|---|---|---|
| `base` | yes | Left side of `git diff base...head`. |
| `head` | no | Default `HEAD`. |
| `slug`, `title` | `title` yes | Ticket id and plain-language PR title; the page title and nav show them. |
| `out` | no | Default `/tmp/<slug>-walkthrough.html`; `--out` overrides it. |
| `summary`, `verification` | no | _HTML_. The box under the header. `verification` states what ran and what could not. |
| `pills` | no | Short scope tags: product lines, versions, affected subsystems. |
| `steps[].title` | yes | Step name; the nav shows it too. Steps are numbered in order. |
| `steps[].subtitle`, `badge` | no | One-line subtitle shown under the title; status label such as `Core change`, `Boundary`, `Confirm intent`, `Actionable`, `Verified`. |
| `steps[].tone` | no | `neutral` (default), `attention` (bug, confirm intent, mismatch), or `ok`. Colours the number, badge, and review comment. |
| `steps[].explain`, `bullets[]`, `comment` | no | _HTML_. The explanation, watch-out points, and CR remark. |
| `steps[].files[]` | no | A path string, or `{path, focus?, note?}`. Each path must appear in the diff range. `focus` keeps only the hunks containing any of the needle strings; the build fails if none match. |
| `skip[]` | no | `{glob, reason}` for changed files deliberately left out. `fnmatch` globs: `*` crosses `/`. |
| `checklist` | no | `blockers`, `confirm`, `not_blocking`: lists of _HTML_ strings; empty lists are omitted. |
