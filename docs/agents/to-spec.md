# /to-spec in this repo: OpenSpec change + GitHub ticket

In this repo `/to-spec` produces two things, and this file replaces the generic spec template and the "publish to the issue tracker" step of the global `/to-spec` skill:

1. An **OpenSpec change** at `openspec/changes/<change-id>/` (proposal, specs, design, tasks), committed on its own branch `spec/<change-id>` and pushed.
2. A **GitHub issue** (the ticket) that states the goal and the acceptance criteria and points at that change.

`/work-on-ticket #NN` later reads both and implements them. Keep the global skill's rules: no interview, synthesize what the conversation already established, and check the test seams with the user before writing.

GitHub operations follow `docs/agents/issue-tracker.md` (GitHub MCP, not `gh`). Commands that write git config or push run as standalone commands, not chained after `cd ... &&`.

## Steps

1. **Context**: read `GLOSSARY.md`, the ADRs in the area, `docs/progress/STATUS.md`, and the current requirements (`openspec list --specs`, then `openspec show <capability> --type spec` for the capabilities you touch). Decide which capabilities are new and which existing ones change.
2. **Seams**: sketch the test entry points (HTTP API, pure domain function, service against the test DB, DB constraint); prefer existing seams and the highest one. Confirm them with the user.
3. **Name the change**: a kebab-case verb phrase, e.g. `add-order-cancel`. Check `openspec list` for a clash.
4. **Isolated branch**: write the change in a temporary worktree so the user's checkout is untouched:
   ```bash
   git fetch origin
   git worktree add "$TMPDIR/spec-<change-id>" -b spec/<change-id> origin/master
   ```
   Run every `openspec` command below from inside that worktree (`cd "$TMPDIR/spec-<change-id>" && openspec ...`).
5. **Write the artifacts** in dependency order: `openspec new change <change-id>`, then for each artifact from `openspec status --change <change-id> --json`, run `openspec instructions <artifact> --change <change-id> --json` and write the file from its `template` to `resolvedOutputPath`. The `context` and `rules` it returns come from `openspec/config.yaml`; obey them, never copy them into the file. Map the conversation onto the artifacts:

   | Conversation content | Artifact |
   |---|---|
   | Problem, solution, user stories | `proposal.md` (Why, What Changes, User Stories, Capabilities, Impact) |
   | Observable behaviour, acceptance criteria | `specs/<capability>/spec.md`: `## ADDED` / `## MODIFIED` / `## REMOVED Requirements`, each `### Requirement:` with `#### Scenario:` using WHEN / THEN |
   | Implementation decisions, test seams, prior-art tests, out of scope | `design.md` (Context, Goals / Non-Goals, Decisions, Testing Decisions, Risks / Trade-offs) |
   | Implementation steps | `tasks.md`: vertical-slice groups, each starting with a failing test, ending with a verification group |

   A `## MODIFIED Requirements` block copies the whole existing requirement from `openspec/specs/` and edits it; a partial copy loses text on archive. No file paths or code snippets in proposal or specs (a prototype snippet that encodes a decision may go in design.md).
6. **Validate**: `openspec validate <change-id> --strict` passes.
7. **Create the ticket** with `issue_write` `method: "create"`, label `ready-for-agent`, title in zh-TW, body:

   ```markdown
   Blocked by: #<n>          (omit the line when nothing blocks it)

   ## 目標
   <proposal 的 Why + What Changes，2–5 句>

   ## 驗收條件
   - [ ] <Requirement 名稱> — <Scenario 名稱>
   - [ ] ...

   ## OpenSpec
   - Change：`openspec/changes/<change-id>/`
   - Branch：`spec/<change-id>`（https://github.com/jeterchan226/miao-fruit-shop/tree/spec/<change-id>/openspec/changes/<change-id>）
   ```

   The acceptance criteria are one checkbox per spec scenario, same names, same order. The issue carries only the goal and criteria; details stay in the change.
8. **Link back**: put `Ticket: #NN` as the first line of `proposal.md`, rerun `openspec validate <change-id> --strict`.
9. **Commit and push** from the temporary worktree: one commit `docs(openspec): propose <change-id> (#NN)` containing only `openspec/changes/<change-id>/`, then `git push -u origin spec/<change-id>` as a standalone command. Remove the worktree with `git worktree remove "$TMPDIR/spec-<change-id>"`. No PR: the spec reaches master inside the ticket's PR.
10. **Report**: the issue link, the change id and branch, the requirement and scenario count, and the next command: `/work-on-ticket #NN`.

When the conversation splits into several independent tickets, repeat steps 3–9 per ticket (one change, one issue, one branch each) and fill in `Blocked by:` between them.
