---
name: work-on-ticket
description: "Take one GitHub ticket from start to an open PR, inside a worktree the user created. Usage: /work-on-ticket #NN"
disable-model-invocation: true
---

# Work on a ticket

One session handles only the ticket given as the argument (#NN below). GitHub issues are the single source for the feature list; the repo is `jeterchan226/miao-fruit-shop` and the base branch is `master`. All GitHub operations go through the GitHub MCP server (`mcp__github-jeterchan226__*`, `owner: "jeterchan226"`, `repo: "miao-fruit-shop"`), never the `gh` CLI; see `docs/agents/issue-tracker.md`. Load the MCP tools you need in one `ToolSearch` call before the first use.

Commands that write git config (`git push -u`, `--set-upstream`, `git config`) run as a standalone command, not chained after `cd ... &&`.

## 1. Start

Move on only when each step passes. If any step fails, stop and report the cause to the user; write no feature code.

1. **Check location**: `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` (you are in a worktree), the current branch is not `master`, and the working tree is clean. The user creates the worktree; if any check fails, ask the user to fix it.
2. **Sync**: `git fetch origin`, then bring the branch up to the latest `origin/master` (if the desktop app created this worktree, use its sync with base branch tool; otherwise `git rebase origin/master`).
3. **Read context**:
   - `git log --oneline -15`
   - `issue_read` `method: "get"` and `method: "get_comments"` on #NN: the full ticket and its acceptance criteria
   - `GLOSSARY.md` and `docs/adr/` for domain terms and past decisions
4. **Confirm the ticket can start**: the ticket is open, and every issue in its `Blocked by:` line (if any) is closed.
5. **Database**: tests need Postgres. If it is not running, `docker compose up db -d` in `backend/`.
6. **Baseline**: `uv run pytest -q` in `backend/` passes in full (and `npm run test` in `frontend/` when the ticket touches the frontend). This proves existing features worked before you started. If it fails, report the failing tests and change nothing.

Done when: all six steps pass and you have reported a summary to the user: the ticket's goal, its acceptance criteria, and the baseline results.

## 2. Work

- **Only #NN.** Anything outside the acceptance criteria (bugs, refactoring opportunities, other tickets' work) gets noted, and at the end goes into the report's 「留待之後」 section, for a later ticket.
- **Respect the backend layering** in `CLAUDE.md`: routes → services → repositories → models; never skip or reach across a layer.
- **Confirm the entry point before writing tests**: follow `/tdd`. The agreed entry points are the HTTP API, pure domain functions (e.g. `compute_amounts`), services against the test DB, and database constraints (exercised with raw SQL). Ask the user before using any other entry point.
- **TDD**: one slice at a time; see red before implementing. Run single test files and `uv run mypy app` often along the way.
- Ask the user about anything that needs their decision (the spec is silent, or you want to deviate from it); once answered, update the ticket, `GLOSSARY.md` or an ADR to match.

## 3. Finish

Done when: the PR is open, CI is green, and you have reported the PR link to the user. The user merges the PR; the agent leaves merging to them.

1. **Full checks** all pass in `backend/`: `uv run ruff check .`, `uv run mypy app`, `uv run pytest -q`. When the frontend changed, also `npm run test` and `npm run build` in `frontend/`.
2. **Check every acceptance criterion**: each one has a matching automated test, or a manual verification with a record of what you did and what you saw.
3. **Code review**: run `/code-review` with `origin/master` as the fixed point. Fix what should be fixed; write what you leave unfixed into the report's 「留待之後」 section. After fixing, rerun step 1.
4. **Migrations**: if models changed, the branch includes an Alembic migration, and `uv run alembic upgrade head` runs cleanly against the local DB.
5. **Commit**: one clear commit, titled like `feat: <what was done> (#NN)` or `fix: ... (#NN)`, with a body listing user-visible changes and containing `Closes #NN`.
6. **Align with master**: `git fetch origin`, then rebase onto `origin/master`. After the rebase, rerun `uv run pytest -q`.
7. **Push and open the PR**: `git push -u origin <branch>` as a standalone command, then open the PR yourself with `create_pull_request` (`base: "master"`, `head: <branch>`; write the body with `/pr`). The body starts with `Closes #NN` on its own line, so the reader sees which ticket the PR closes, lists every acceptance criterion and how it was verified, and ends with the attribution line from the session's system reminder.
8. **Wait for CI**: poll `pull_request_read` `method: "get_check_runs"` every few minutes until every check run completes. On failure, read the failing job, fix, push, and poll again until green.
9. **Tick checkboxes**: once CI is green, change each verified acceptance criterion in the #NN body to `- [x]` (read the body with `issue_read` `method: "get"`, edit it, write it back with `issue_write` `method: "update"`, `body`). Leave unverified ones unticked and explain them in the report.
10. **Report**: the PR link, the result for each acceptance criterion, and the 「留待之後」 items.
