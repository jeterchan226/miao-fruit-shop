---
name: orchestrator
description: "Run tickets in parallel: map open tickets, rank them, and keep starting spec, dev and review sessions until only blocked work remains. Usage: /orchestrator"
disable-model-invocation: true
---

# Orchestrator

The orchestrator runs a **loop**: read the board, rank the tickets, fill every free slot, wait for a session to end, repeat. It stops when the stop condition in section 5 holds. It writes no code, merges nothing, and keeps no state of its own: GitHub issues, PRs and the session list are the whole board.

All GitHub operations follow `docs/agents/issue-tracker.md`. Label meanings are in `docs/agents/triage-labels.md`.

## 1. Read the board

1. **Issues**: `list_issues` with `state: "OPEN"`, including `body` and `labels`.
2. **PRs**: `list_pull_requests` with `base: "dev"`, once with `state: "open"` and once with `state: "closed"`. Match each PR to its ticket by the `Closes #NN` line in its body.
3. **Sessions**: `mcp__ccd_session_mgmt__list_sessions`, keeping only sessions whose `cwd` is inside this repo. Find sessions titled `spec #NN`, `ticket #NN` or `review PR N`, with their state and worktree.
4. **Baseline**: whether `openspec/specs/` on `origin/dev` holds any capability.

Done when: every open ticket has its labels, its open PR (if any), and its session (if any).

## 2. Map the links

For every open ticket, record each link, whether written or inferred:

- **Blocker**: an open issue in its `Blocked by` section. A "suggested order" blocker counts as a blocker. A struck-through one is cleared.
- **Decision**: a blocker that is a choice only the user can make (`需決策`, `待決定`, a named option A / B).
- **Collision**: tickets that must not run together: a written `不要同時進行`, two tickets that both add an Alembic migration, two that change the same file, or two that change the same OpenSpec requirement. Infer the last three from each ticket's locations and scope, then cite what they share.

Done when: every open ticket is accounted for, and every inferred collision names what is shared.

## 3. Classify and rank

Put each ticket in exactly one bucket, first match wins:

1. **Stale**: a merged PR closes it, or its body says it only awaits confirmation and `dev` already meets its acceptance criteria. Cite the PR or the code; the user closes it. A stale ticket counts as closed for every blocker below.
2. **In flight**: it has a running session or an open PR.
3. **Stalled**: its session ended with no PR, or its spec session ended with no `## OpenSpec` section on the ticket. Read `docs/progress/tickets/NN-*.md` and name what it needs. A stalled ticket gets no new session until the user answers.
4. **Needs the user**: it has an open decision, or carries `needs-info`, `ready-for-human` or `wontfix`. Name what the user must decide.
5. **Blocked**: it has an open blocker. Name the blocker.
6. **Needs spec**: its body has no `## OpenSpec` section.
7. **Ready**: everything else.

Rank each bucket by these keys in order:

1. Production bugs first.
2. Most tickets unblocked, counting indirect ones (#49 → #29 → #30 counts two).
3. Bugs before refactors, refactors before chores.
4. Lowest ticket number.

## 4. Fill the slots

**Capacity is four running sessions.** Each worktree has its own test database, so sessions run in parallel. Count running sessions, then fill the free slots in this order:

1. **Review**: every open PR with green CI, no `## Automated review` section in its body, and no running session on its worktree.
2. **Spec**: every Needs spec ticket, once the baseline exists. With no baseline, report it and start no spec sessions.
3. **Develop**: Ready tickets in rank order, skipping any that collide with an in-flight ticket or one started this pass.

An open PR that already has `## Automated review` waits on the user's merge and starts nothing.

Load `mcp__ccd_session__start_session` first. Every session uses `initiation: "user_asked"`, `context: "fresh"`, `wake_when_done: true`, and this `background`: repo `jeterchan226/miao-fruit-shop`, base branch `dev`, the user merges PRs, and this session handles only its own ticket or PR.

- **Spec session**: `title: "spec #NN"`, `use_worktree: true`, `source_branch: "dev"`. Prompt:

  > Read `docs/agents/to-spec.md` and follow it for existing ticket #NN. The ticket exists, so skip creating one: at step 7, rewrite the #NN body in that format and keep its `Blocked by` line, then set the label `ready-for-agent`. At step 2, choose the seams yourself and record them in `design.md`. If the spec needs a choice only the user can make, stop and report it, leaving the ticket as it is. Include `github.com` in `allowed_domains` for `git fetch`.

- **Dev session**: `title: "ticket #NN"`, `use_worktree: true`, `source_branch: "dev"`. Prompt:

  > Invoke the `work-on-ticket` skill for #NN. The orchestrator created this worktree, which satisfies the skill's location check. Include `github.com` in `allowed_domains` for `git fetch`.

- **Review session**: `title: "review PR N"`, `cwd: <the ticket's dev worktree>`, `use_worktree: false`, so it works on the PR's head branch. Prompt:

  > Invoke the `review-and-fix` skill for PR N. Include `github.com` in `allowed_domains` for `git fetch`.

  When the dev worktree is gone, leave the PR unstarted and report it.

Done when: every free slot holds a session, or no work is left to start.

## 5. Loop or stop

**Stop** when no session is running and sections 3 and 4 leave nothing to start: every remaining ticket is Stale, Stalled, Needs the user, Blocked, or waiting on the user's merge.

Otherwise end the turn. The app continues the orchestrator when its sessions end; go back to section 1. A note from a session is its report: confirm its result on the board.

## 6. Report

On stopping, reply in Traditional Chinese with:

- **本次完成**: sessions started and where each ended, with links.
- **等你處理**: PRs ready to merge, stale tickets to close, stalled tickets, then decisions, each with the tickets it unblocks.
- **被擋**: Blocked tickets in rank order, each with its blocker.
- **衝突**: every collision, citing what is shared.

Merges unblock tickets, so the user sends `/orchestrator` again after merging.
