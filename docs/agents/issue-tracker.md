# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the GitHub MCP server (`mcp__github-jeterchan226__*`) for all operations, with `owner: "jeterchan226"`, `repo: "miao-fruit-shop"`. Do not use the `gh` CLI: inside the Claude Code sandbox it fails TLS verification against api.github.com (`x509: OSStatus -26276`).

MCP tools are deferred: load the ones you need in one `ToolSearch` call (`select:mcp__github-jeterchan226__issue_write,mcp__github-jeterchan226__issue_read,...`) before calling them.

## Conventions

- **Create an issue**: `issue_write` with `method: "create"`, `title`, `body`, `labels`. Pass the body as a plain multi-line string.
- **Read an issue**: `issue_read` with `method: "get"` (body, labels, state, hierarchy) and `method: "get_comments"` for comments.
- **List issues**: `list_issues` with `state` (`OPEN`/`CLOSED`), `labels`, and `fields` to trim the response. Use `search_issues` for keyword queries.
- **Make an issue a sub-issue of a parent**: create it with `issue_write` `method: "create"` plus `parent_issue_number: <parent>`, or attach afterwards with `sub_issue_write` `method: "add"`, `issue_number: <parent>`, `sub_issue_id: <child database id>` (the `issue.id` returned by `issue_write`, _not_ the `#number`). Without sub-issues, put `Part of #<parent>` at the top of the child body.
- **Comment on an issue**: `add_issue_comment` with `issue_number`, `body`.
- **Apply / remove labels**: read current labels (`issue_read` `method: "get_labels"`), then `issue_write` `method: "update"` with the full new `labels` list (it replaces, not appends).
- **Close**: `add_issue_comment` with the reason, then `issue_write` `method: "update"`, `state: "closed"`, `state_reason: "completed"` (or `"not_planned"` / `"duplicate"` + `duplicate_of`).
- **Code references in bodies**: use commit permalinks (`https://github.com/jeterchan226/miao-fruit-shop/blob/<sha>/path#Lx-Ly`) so line numbers survive later edits.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the MCP PR tools:

- **Read a PR**: `pull_request_read` with `method: "get"`, `"get_comments"`, and `"get_diff"`.
- **List external PRs for triage**: `list_pull_requests` with `state: "open"`, then keep those whose author is not the owner or a collaborator (`list_repository_collaborators`).
- **Comment / label / close**: `add_issue_comment` (pass the PR number as `issue_number`), `issue_write` `method: "update"` with `labels` (PRs share the issue number space), `update_pull_request` with `state: "closed"`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `pull_request_read` `method: "get"` and fall back to `issue_read` `method: "get"`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue with `issue_write`.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `issue_write` `method: "create"` with `labels: ["wayfinder:map"]`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (see **Make an issue a sub-issue of a parent**). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: the GitHub MCP server has no tool for native issue dependencies, so record blockers as a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every listed blocker is closed. If native dependencies were already set in the GitHub UI, honour them too.
- **Frontier query**: list the map's open children (`issue_read` `method: "get_sub_issues"` on the map, or its task list), drop any with an open blocker (an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `issue_write` `method: "update"` with `assignees: ["jeterchan226"]`, the session's first write.
- **Resolve**: `add_issue_comment` with the answer, then close (see **Close**), then append a context pointer (gist + link) to the map's Decisions-so-far.
