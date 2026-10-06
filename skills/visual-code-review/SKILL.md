---
name: visual-code-review
description: Render a PR or branch review as a step-by-step HTML walkthrough with real diffs and review comments beside each step. Use when the user asks for a visual walkthrough, or "walk me through this PR" for a branch, PR, or diff.
---

The reader wants to **review the PR without running `git diff`**. The report is a guided tour: a reading order through the change, each stop pairing a plain-language explanation with the real diff and your review comment, ending in a pre-approve checklist. Read the report as a reviewer would: every claim in it is one you checked against the code.

`scripts/build_report.py` renders the page from a JSON spec. The spec format is in [`REPORT-SPEC.md`](REPORT-SPEC.md). Put the spec and output in `/tmp`, never in the repo.

## 1. Review first

Pin the comparison range: `git diff <base>...HEAD` (three dots, merge-base). Use `origin/<default>` when local `master`/`main` is stale; a range full of upstream merges reviews other people's work. List the commits and `--stat`.

If a review already happened in this session, re-verify each finding against the current branch before reusing it. Findings go stale after pushes and rebases. Otherwise review now. Trace each changed behaviour to its callers and downstream consumers, and run the focused tests.

Done when every finding is labelled one of: **bug**, **confirm intent** (deliberate-looking behaviour change, often beyond the ticket's scope), **doc/code mismatch**, **follow-up**, **checked, fine**. Each one has a file:line and the mechanism behind it.

## 2. Choose the reading order

Order the steps along the **data flow**, from small to large: new data or fields → gates/flags/predicates → wiring (registration, chapter lists, settings) → the decision logic → downstream output → tests read as the spec → docs. The reader then meets every concept before the code that uses it. Put one concern in each step, usually one file or one group of files.

Bulk files with no logic (SVG/images, lockfiles, generated code, fixtures, migrations without data changes) go under `skip`, with a reason. Never render them; one PR had 21k SVG lines that would have buried 1,200 real lines.

Done when every changed file sits in exactly one step or one `skip` glob. The builder exits non-zero and lists any uncovered files.

## 3. Write the steps

For each step, write:

- **explain**: what changed and why it matters, in plain words. Name the before → after behaviour, not the edit ("a one-sided drawer now gets long feet; it used to keep the short foot").
- **bullets**: what to watch for in this diff. Keep them short.
- **comment**: your CR remark for this step. Attach each finding from step 1 to the step whose diff shows it. Set `tone: attention` on steps that carry a bug, a confirm-intent item, or a mismatch.
- **focus**: for large files, keep only the hunks that matter (see spec).

Then write the **checklist**. It answers "what do I need before I hit approve?" in easy language, brief points: `blockers`, `confirm` (questions for the author or product, phrased as the question to ask), `not_blocking`. Set `verification` honestly: what ran, its counts, and what could not run and why. Say "tests not run: Docker cannot read pgdata"; "looks fine" says nothing about what was checked.

Done when every finding from step 1 appears in exactly one step comment and in the checklist.

## 4. Build

```bash
python3 <skill-dir>/scripts/build_report.py /tmp/<slug>-spec.json   # run from the repo root
```

Diffs come from git at build time, so re-run after new commits. `--inline` embeds diff2html for offline viewing; the default loads it from jsDelivr.

## 5. Hand over

Give user the report path back. Then the checklist in three lines or fewer: blockers first, then the questions to confirm.
