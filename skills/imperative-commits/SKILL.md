---
name: imperative-commits
description: Create logically grouped git commits with imperative-style messages. Use when the user asks to commit changes, split work into commits, or write commit messages.
---

# Imperative Commits

## Workflow

1. Inspect state: `git status`, `git diff`, `git diff --staged`.
2. Group changes by logical intent. Unrelated changes go in separate commits; prefer narrow, granular groups. Small changes MAY be a single commit.
3. For each group: stage only its files/hunks (`git add <paths>` or `git add -p`), then commit.
4. Verify with `git log --oneline` and `git status` that nothing was left out unintentionally.

If the user supplies extra instructions (scope, message hints, files to exclude), follow them.

## Message format

`<Action> <what> [to/in/for/from/...] <context>`

- Start with a capitalized verb: Add, Fix, Update, Remove, Refactor, Implement, Improve, ...
- Present tense, imperative mood, as if giving a command.
- First line under 50 characters when possible; no trailing period.

## Examples

- `Add user authentication to login service`
- `Fix null pointer exception in OrderProcessor`
- `Update README with installation instructions`
- `Refactor database connection handling`
