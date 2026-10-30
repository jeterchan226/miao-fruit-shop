---
name: work-on-ticket
description: "Take one GitHub ticket from start to an open PR, inside a worktree the user created. Usage: /work-on-ticket #NN"
---

# Work on a ticket

One session handles only the ticket given as the argument (#NN below). GitHub issues are the single source for the feature list; the repo is `jeterchan226/miao-fruit-shop` and the base branch is `dev` (production deploys come from `master`, which `dev` is merged into later). All GitHub operations go through the GitHub MCP server (`mcp__github-jeterchan226__*`, `owner: "jeterchan226"`, `repo: "miao-fruit-shop"`), never the `gh` CLI; see `docs/agents/issue-tracker.md`. Load the MCP tools you need in one `ToolSearch` call before the first use.

Commands that write git config (`git push -u`, `--set-upstream`, `git config`) run as a standalone command, not chained after `cd ... &&`.

## 1. Start

Move on only when each step passes. If any step fails, stop and report the cause to the user; write no feature code.

1. **Check location**: `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` (you are in a worktree), the current branch is neither `master` nor `dev`, and the working tree is clean. The user creates the worktree; if any check fails, ask the user to fix it.
2. **Sync**: `git fetch origin`, then bring the branch up to the latest `origin/dev` (if the desktop app created this worktree, use its sync with base branch tool with `base: "dev"`; otherwise `git rebase origin/dev`).
3. **Read context**:
   - `git log --oneline -15`
   - `issue_read` `method: "get"` and `method: "get_comments"` on #NN: the full ticket and its acceptance criteria
   - `GLOSSARY.md` and `docs/adr/` for domain terms and past decisions
   - `docs/progress/STATUS.md` for where the project stands and open 「留待之後」 items; if `docs/progress/tickets/NN-*.md` exists, an earlier session stopped partway: resume from its 「下一步」 section
4. **Confirm the ticket can start**: the ticket is open, and every issue in its `Blocked by:` line (if any) is closed.
5. **Load the OpenSpec change**: the ticket's `## OpenSpec` section names `<change-id>` and branch `spec/<change-id>` (written by `/to-spec`, see `docs/agents/to-spec.md`).
   - If `openspec/changes/<change-id>/` is missing, bring in the spec commit: `git fetch origin spec/<change-id>`, then `git cherry-pick origin/dev..origin/spec/<change-id>`.
   - Read `proposal.md`, `design.md`, every `specs/**/spec.md` and `tasks.md`; `openspec validate <change-id> --strict` passes.
   - The ticket's acceptance criteria match the spec scenarios one to one; on a mismatch, ask the user which is right.
   - A ticket with no `## OpenSpec` section stops here: report it, so its spec can be written first.
6. **Database**: tests need Postgres. If it is not running, `docker compose up db -d` in `backend/`.
7. **Baseline**: `uv run pytest -q` in `backend/` passes in full (and `npm run test` in `frontend/` when the ticket touches the frontend). This proves existing features worked before you started. If it fails, report the failing tests and change nothing.

Done when: all seven steps pass and you have reported a summary to the user: the ticket's goal, its acceptance criteria, the OpenSpec change and its task groups, and the baseline results.

## 2. Work

- **Only #NN.** Anything outside the acceptance criteria (bugs, refactoring opportunities, other tickets' work) gets noted, and at the end goes into the report's 「留待之後」 section, for a later ticket.
- **Respect the backend layering** in `CLAUDE.md`: routes → services → repositories → models; never skip or reach across a layer.
- **Confirm the entry point before writing tests**: follow `/tdd`. The agreed entry points are the HTTP API, pure domain functions (e.g. `compute_amounts`), services against the test DB, and database constraints (exercised with raw SQL). Ask the user before using any other entry point.
- **Follow `tasks.md`**: work the task groups in order, and change each task to `- [x]` as soon as it is done. Use `design.md` for how and the spec scenarios for what counts as done.
- **TDD**: one slice at a time; see red before implementing. Run single test files and `uv run mypy app` often along the way.
- Ask the user about anything that needs their decision (the spec is silent, or you want to deviate from it); once answered, update the OpenSpec change (spec scenario, `design.md`, `tasks.md`), the ticket, `GLOSSARY.md` or an ADR to match, and rerun `openspec validate <change-id> --strict`.
- **Stopping early**: if the session ends before section 3 (blocked, waiting on the user, out of time), write `docs/progress/tickets/NN-<change-id>.md` in the format of `docs/progress/README.md` with status `進行中` or `阻塞` and a concrete 「下一步」, commit it as `docs: progress for #NN`, and push the branch, so the next `/work-on-ticket #NN` can resume.

## 3. Finish

Done when: the PR is open, CI is green, and you have reported the PR link to the user. The user merges the PR; the agent leaves merging to them.

1. **Full checks** all pass in `backend/`: `uv run ruff check .`, `uv run mypy app`, `uv run pytest -q`. When the frontend changed, also `npm run test` and `npm run build` in `frontend/`.
2. **Check every acceptance criterion**: each one has a matching automated test, or a manual verification with a record of what you did and what you saw.
3. **Code review**: run `/code-review` with `origin/dev` as the fixed point. Fix what should be fixed; write what you leave unfixed into the report's 「留待之後」 section. After fixing, rerun step 1.
4. **Migrations**: if models changed, the branch includes an Alembic migration, and `uv run alembic upgrade head` runs cleanly against the local DB.
5. **Archive the OpenSpec change**: every task in `tasks.md` is `- [x]` (or explained in the report), `openspec validate <change-id> --strict` passes, then `openspec archive <change-id> -y`. This moves the change to `openspec/changes/archive/` and merges its requirements into `openspec/specs/`; check the resulting `openspec/specs/` diff reads right.
6. **Record progress**: write `docs/progress/tickets/NN-<change-id>.md` in the format of `docs/progress/README.md` with status `完成`, including 「留待之後」 (a line tracked by an issue ends in `：#NN`), 「系統現況」 and 「部署待辦」 when they have content. If this ticket resolved an untracked 「留待之後」 line in another ticket's record, delete that line. Do not edit `docs/progress/STATUS.md`: it is generated after the merge into `dev`.
7. **Commit**: one clear commit (on top of the spec commit from `/to-spec`), titled like `feat: <what was done> (#NN)` or `fix: ... (#NN)`, holding the code, the archived change and the progress files, with a body listing user-visible changes and containing `Closes #NN`.
8. **Align with dev**: `git fetch origin`, then rebase onto `origin/dev`. After the rebase, rerun `uv run pytest -q`.
9. **Push and open the PR**: `git push -u origin <branch>` as a standalone command, then open the PR yourself with `create_pull_request` (`base: "dev"`, `head: <branch>`; write the body with `/pr`). The body starts with `Closes #NN` on its own line, so the reader sees which ticket the PR closes, lists every acceptance criterion and how it was verified, and ends with the attribution line from the session's system reminder.
10. **Wait for CI**: poll `pull_request_read` `method: "get_check_runs"` every few minutes until every check run completes. On failure, read the failing job, fix, push, and poll again until green.
11. **Tick checkboxes**: once CI is green, change each verified acceptance criterion in the #NN body to `- [x]` (read the body with `issue_read` `method: "get"`, edit it, write it back with `issue_write` `method: "update"`, `body`). Leave unverified ones unticked and explain them in the report.
12. **Report**: the PR link, the result for each acceptance criterion, the 「留待之後」 items, and that branch `spec/<change-id>` can be deleted once the PR merges.
