---
name: pr-comments
description: "Triage review comments on a GitHub pull request or GitLab merge request: judge each one, plan fixes for the valid ones, report the rest. Use when the user asks to address, handle, or respond to PR/MR comments or review feedback."
---

Every comment gets a verdict before any fix is planned. Reviewers are sometimes wrong; a suggestion applied blindly can break working code.

1. Identify the platform from `git remote get-url origin`: `github.com` is GitHub; `gitlab.com`, or any other host listed by `glab auth status`, is GitLab. For another unknown host, ask the user which platform it is.
2. Fetch the open review threads for the current branch. Skip resolved and outdated threads.
   - **GitHub**: use the GitHub MCP if available, otherwise the `gh` CLI:
     - `gh pr view --json number,url,reviews,comments`
     - inline review comments: `gh api repos/{owner}/{repo}/pulls/<number>/comments`
   - **GitLab** with `glab`:
     - `glab mr view --unresolved` lists the merge request's unresolved discussions
     - structured threads: take `iid` from `glab mr view --output json`, then `glab api "projects/:fullpath/merge_requests/<iid>/discussions" --paginate`. Keep discussions with a note where `resolvable` is true and `resolved` is false; inline notes carry `position.new_path` and `position.new_line`.
   - **GitLab** without `glab`: call the REST API with a token from `$GITLAB_TOKEN`, sending it as the `PRIVATE-TOKEN` header. `<project>` is the URL-encoded `group/repo` path (`/` becomes `%2F`):
     - find the MR: `GET https://<host>/api/v4/projects/<project>/merge_requests?source_branch=<branch>&state=opened`
     - threads: `GET https://<host>/api/v4/projects/<project>/merge_requests/<iid>/discussions?per_page=100`, following the `page` parameter until the result is empty
   If the API answers `401` (glab unauthenticated and no `$GITLAB_TOKEN`), stop and ask the user to run `glab auth login` or export `GITLAB_TOKEN`. Discussions require authentication even on public projects.
3. For each comment, read the code it points at and decide:
   - **valid**: the issue is real in the current code
   - **invalid**: the suggestion is wrong, already handled, or conflicts with the task. Note the reason, with file:line evidence.
   - **unclear**: a question for the author or reviewer
4. For each valid comment, plan the fix: which file, what change, and how to verify it.

Done when every unresolved comment has a verdict.

Report in three groups (valid with planned fix, invalid with reason, unclear with the question to ask), each item linking its comment.
Leave the code unchanged; the user applies the plan, e.g. with `/fix` or through another agent skill.
