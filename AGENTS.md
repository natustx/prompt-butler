# AGENTS.md

## General Rules

<!-- agent-config:rules:start -->
<!-- BEGIN /Users/me/prj/agent-config/rules/optional/beads.md -->

# Beads Issue Tracking

Use `bd` for issue tracking instead of markdown TODOs.

## Essential workflow
Only engage the Beads workflow after the user explicitly asks to use Beads for the current work. For agent identity, use the `beads-work` skill which auto-generates a unique name.

**NOTE:** `bd list --status` does NOT support comma-separated values. Query each status separately.

```bash
bd ready --unassigned --json                    # Find work
bd update <id> --assignee "<AGENT_NAME>" --status in_progress  # Claim it
# ... do the work ...
bd close <id> --reason "Done"                   # Complete it
bd sync                                          # Push changes (end of session)
```

## Creating issues
```bash
bd create "Title" -d "Description" -t task -p 2 --json
```
Types (-t): bug, feature, task, epic, chore.
Priority (-p): 0 (critical) to 4 (backlog).

**Discovered work / issues:** Create beads immediately with `--discovered-from <current-id>` to link it.

## Dependencies
- Think "what does this need?" not "what comes first?"
- Use `bd dep add <task> <depends-on>`. Name by function ("Add auth"), not sequence ("Step 1").

## Planning Mode
When exiting plan mode, write the plan to Beads instead of a markdown file:
1. Create an epic: `bd create "Epic: [Plan Title]" -t epic -p 2 --json`
2. Add child tasks: `bd create "Task description" --parent <epic-id> --json`
3. Set dependencies: `bd dep add <task-id> <blocked-by-id>`
4. Verify structure: `bd dep tree <epic-id>`

## Completing a feature or session

**IMPORTANT:** Before stopping a session, after completing a feature, or after doing cleanup on beads, you MUST:
1. File issues as beads for any remaining/discovered work
2. Update issue statuses to reflect current state
3. Run `bd sync` to sync beads changes

**This last command MUST succeed in order for you to be done**. If it doesn't work, stop what you are doing and alert the users with specifics around what is wrong

<!-- END /Users/me/prj/agent-config/rules/optional/beads.md -->

<!-- BEGIN /Users/me/prj/agent-config/rules/optional/mandatory-skill-activation.md -->

### Available Skills

<INSTRUCTION>
MANDATORY SKILL ACTIVATION SEQUENCE

Step 1 - EVALUATE (do this in your response):
For each skill below, state: [skill-name] - YES/NO - [reason]

Available skills:
- frontend-design: Use when the user asks to build web components, pages, or applications.
- optimizing-performance: Measure-first performance optimization that balances gains against complexity. Use when addressing slow code, profiling issues, or evaluating optimization trade-offs.
- systematic-debugging: Four-phase debugging framework that finds root causes before proposing fixes. Use when investigating bugs, errors, unexpected behavior, failed tests, or when previous fixes haven't worked.
- writing-tests: Writes behavior-focused tests using Testing Trophy model with real dependencies. Use when writing tests, choosing test types, or avoiding anti-patterns like testing mocks.

Step 2 - ACTIVATE (do this immediately after Step 1):
<important>IF any skills are YES: invoke EACH relevant skill NOW</important>

Step 3 - IMPLEMENT:
Only after Step 2 is complete, proceed with implementation.


Example of correct sequence:
- systematic-debugging: YES - matches current task
- writing-tests: NO - not relevant
- frontend-design: NO - not relevant

[Then IMMEDIATELY invoke the skills]

[THEN and ONLY THEN start implementation]
</INSTRUCTION>
<!-- DYNAMIC_SKILLS_END -->

<!-- END /Users/me/prj/agent-config/rules/optional/mandatory-skill-activation.md -->

<!-- agent-config:rules:end -->

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
