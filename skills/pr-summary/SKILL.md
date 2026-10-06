---
name: pr-summary
description: "Summarise the current branch as a pull request description with risks, reviewer guidance, and a confidence score. Use when the user asks for a PR summary or description of a branch."
---

1. Pin the range: `git log --oneline <base>..HEAD` and `git diff --stat <base>...HEAD`. Use `origin/<default>` as the base when the local default branch is stale.
2. Read the diff itself, not just the commit messages; messages drift from what the code does.
3. Write the summary:
   1. **Overview**: what the PR does, in 1–2 sentences.
   2. **Key changes**: the main files and modifications, as a list.
   3. **Potential risks**: breaking changes, migrations, security concerns. Omit the section if there are none.
   4. **Review recommendations**: where the reviewer should look hardest, and why.
   5. **Confidence**: 1 (early work in progress) to 5 (production-ready), with one line justifying the score from what was tested.

Output the summary as Markdown ready to paste into the PR. Change nothing in the repo.
