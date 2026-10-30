---
name: review-and-fix
description: Review an open PR, commit fixes for the clear-cut problems, and list the ones needing a decision in the PR body. Usage: /review-and-fix <PR number>
disable-model-invocation: true
---

# Review and fix a PR

One session handles only the PR given as the argument (PR N below; the ticket it closes is #NN). The repo is `jeterchan226/miao-fruit-shop`. All GitHub operations go through the GitHub MCP server (`mcp__github-jeterchan226__*`, `owner: "jeterchan226"`, `repo: "miao-fruit-shop"`), never the `gh` CLI; see `docs/agents/issue-tracker.md`. Load the MCP tools you need in one `ToolSearch` call before the first use.

Commands that write git config (`git push -u`, `--set-upstream`, `git config`) run as a standalone command, not chained after `cd ... &&`.

The user looks at only two things: the final diff, and the "Automated review" section of the PR body. So every finding must land in a commit or in that section.

## 1. Start

Move on only when each step passes; on failure, stop and report.

1. **Read the PR**: `pull_request_read` `method: "get"` on N. The PR must be open. Note its head branch, base branch and body. When the body holds exactly one `Closes #NN` (or `Fixes #NN` / `Resolves #NN`), that issue is #NN. With zero or several, stop: ask the user to put exactly one `Closes #NN` in the PR body. A PR with no ticket gets a plain `/code-review` instead.
2. **Check location**: you are in a worktree, the current branch equals the PR's head branch, and the working tree is clean. If not, ask the user to fix it.
3. **Sync**: `git fetch origin`; the local branch must match `origin/<head>` (`git status -sb` shows no ahead / behind). If it is behind the base branch, use the desktop app's sync with base branch tool, or `git merge origin/<base>`; on any conflict, `git merge --abort`, then stop and report the conflicting files. The PR is public, so history only grows by new commits: no rebase, no force push.
4. **Read the spec**: `issue_read` `method: "get"` and `method: "get_comments"` on #NN.
5. **Database**: if Postgres is not running, `docker compose up db -d` in `backend/`.

## 2. Collect findings

1. **Automated review**: run `/code-review` with `origin/<base>` as the fixed point and #NN as the spec.
2. **Human comments**: `pull_request_read` `method: "get_review_comments"` and `method: "get_comments"` on N; take the comments not yet addressed. Treat them exactly like the automated findings: findings to verify, judged right or wrong against the code.
3. Merge both sources into one numbered list. For each item record its source (Standards, Spec, or the comment's author), location (file:line), and content.

Done when: the list covers every item from both sources.

## 3. Triage

First read the relevant code and tests to confirm the finding is real, then put each item into exactly one category. The fix decides the category, whatever label the reviewer gave. The test: would two careful engineers, given the finding, both fix it and write the same fix?

- **auto-fix**: yes to both, so you commit the fix yourself in this run. For example: a broken acceptance criterion from the spec, a bug, a breach of a documented repo standard (`CLAUDE.md` layering, ruff, mypy strict), a test the acceptance criteria require but the PR lacks, an unclear name or reference with one obvious replacement.
- **needs-decision**: the finding is real, but leaving it is defensible or there are several reasonable fixes, so the user decides. For example: a smell whose fix reshapes code (moving a function across layers, extracting a type), a gap or ambiguity in the spec, a change to a public API or the domain model, a problem inside #NN whose fix reaches code outside it.
- **rejected**: verification shows the finding is wrong, or it conflicts with a documented decision (`docs/adr/`, `GLOSSARY.md`, the spec). Record the evidence.
- **deferred**: real, but the problem itself lies outside #NN's scope.

When unsure between auto-fix and needs-decision, choose needs-decision.

Done when: every item in the list has a category and a one-sentence reason.

## 4. Fix

Handle the auto-fix items one at a time, one commit per item (or per group of items sharing a root cause):

1. For behavior problems, follow `/tdd`: first write a test that goes red, then fix until green. Change standards and naming problems directly.
2. Run the affected test files and `uv run mypy app`; commit only when both pass.
3. Commit with a title like `fix: <what was fixed> (#NN)` or `refactor: ... (#NN)`; the body gives the list number and the finding.

If a fix turns out to involve a trade-off partway through, revert that item's changes and move it to needs-decision.

After all fixes, run the full checks from `/work-on-ticket` section 3 step 1.

Done when: every auto-fix item has a matching commit and the full checks all pass.

## 5. Re-review

After fixing, run `/code-review` again (same fixed point), look only at new findings, and handle them per sections 3 and 4. Re-review at most twice; any new auto-fix item from the second re-review moves to needs-decision, noted "still appearing after two re-reviews".

Done when: the last re-review produced no new auto-fix items, or two re-reviews have run.

## 6. Deliver

1. **Deferred items**: open a GitHub issue for each with `issue_write` `method: "create"` (label `needs-triage`, body linking PR N and the finding). Put the new issue number in the Deferred section.
2. **Record progress**: append this run's result (commit range, count per category, needs-decision items) to the 「Review」 section of `docs/progress/tickets/NN-*.md` (format in `docs/progress/README.md`; create the file if the ticket predates it), move any deferred items into `docs/progress/STATUS.md` 「留待之後」 with their new issue numbers, and commit as `docs: review progress for #NN`.
3. **Push**: `git push` as a standalone command.
4. **Update the PR body**: fetch the current body with `pull_request_read` `method: "get"` right before writing, append the format below (or replace only the existing `## Automated review` section, keeping everything else byte for byte), and write it back with `update_pull_request` `body`. Write the section's prose in the same language as the rest of the PR body. The agent edits only the body; replying to and resolving GitHub comments is left to the user.
5. **Wait for CI**: poll `pull_request_read` `method: "get_check_runs"` every few minutes until every check run completes. On failure, fix, push, and poll again until green.
6. **Report**: the PR link, the count in each category, and the full needs-decision list. The user merges the PR.

Done when: every list item appears under its category in the PR body, and CI is green.

## PR body format

```markdown
## Automated review

`/review-and-fix` reviewed <commit range>, X items: auto-fix A, needs-decision B, rejected C, deferred D.

### Auto-fixed
| # | Finding | Source | Commit |
|---|---|---|---|
| 1 | <one sentence> | Spec | <short SHA> |

### Needs decision
- **#2 <one sentence>** (`path:line`, source): <what the trade-off is>. Recommendation: <option and reason>.

### Rejected
- **#3 <one sentence>**: <evidence, citing ADR / spec / code>.

### Deferred
- **#4 <one sentence>**: tracked in #MM.
```

Write "None" under any empty category.
