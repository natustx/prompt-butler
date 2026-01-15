# AGENTS.md

## General Rules

<!-- agent-config:rules:start -->
<!-- BEGIN /Users/me/prj/agent-config/rules/optional/beads.md -->

# Beads Issue Tracking

Use `bd` for issue tracking instead of markdown TODOs.

## Essential workflow
Only engage the Beads workflow after the user explicitly asks to use Beads for the current work. Once the user requests Beads, the very first step is to confirm your agent identity by asking: "What name should I use as my agent identity for beads?" Do NOT proceed (or use generic names like "Claude") until they answer.

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

## Session end checklist
Before stopping a session:
1. File issues for any remaining/discovered work
2. Update issue statuses to reflect current state
3. Run `bd sync` to sync beads changes

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
<important>IF any skills are YES: Use Skill(<skill-name>) tool for EACH relevant skill NOW</important>

Step 3 - IMPLEMENT:
Only after Step 2 is complete, proceed with implementation.


Example of correct sequence:
- systematic-debugging: YES - matches current task
- writing-tests: NO - not relevant
- frontend-design: NO - not relevant

[Then IMMEDIATELY use Skill() tool:]
> Skill(systematic-debugging)
> Skill(writing-tests)  // if also relevant

[THEN and ONLY THEN start implementation]
</INSTRUCTION>
<!-- DYNAMIC_SKILLS_END -->

<!-- END /Users/me/prj/agent-config/rules/optional/mandatory-skill-activation.md -->

<!-- agent-config:rules:end -->
