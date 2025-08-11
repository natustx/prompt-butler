# 🔧 Command Templates

Orchestration templates that enable Claude Code to coordinate multi-agent workflows for different development tasks.

## Overview

After reading the [main kit documentation](../README.md), you'll understand how these commands fit into the integrated system. Each command:

- **Auto-loads** the appropriate documentation tier for its task
- **Spawns specialized agents** based on complexity
- **Integrates MCP servers** when external expertise helps
- **Maintains documentation** to keep AI context current

### 🚀 Automatic Context Injection

All commands benefit from automatic context injection via the `subagent-context-injector.sh` hook:

- **Core documentation auto-loaded**: Every command and sub-agent automatically receives `@/docs/CLAUDE.md`, `@/docs/ai-context/project-structure.md`, and `@/docs/ai-context/docs-overview.md`
- **No manual context loading**: Sub-agents spawned by commands automatically have access to essential project documentation
- **Consistent knowledge**: All agents start with the same foundational understanding

## Available Commands

### 📊 `/full-context`
**Purpose**: Comprehensive context gathering and analysis when you need deep understanding or plan to execute code changes.

**When to use**:
- Starting work on a new feature or bug
- Need to understand how systems interconnect
- Planning architectural changes
- Any task requiring thorough analysis before implementation

**How it works**: Adaptively scales from direct analysis to multi-agent orchestration based on request complexity. Agents read documentation, analyze code, map dependencies, and consult MCP servers as needed.

### 🔍 `/dev/code-review`
**Purpose**: Get multiple expert perspectives on code quality, focusing on high-impact findings rather than nitpicks.

**When to use**:
- After implementing new features
- Before merging important changes
- When you want security, performance, and architecture insights
- Need confidence in code quality

**How it works**: Spawns specialized agents (security, performance, architecture) that analyze in parallel. Each agent focuses on critical issues that matter for production code.

### 🔍 `/dev/code-review-major`
**Purpose**: Perform thorough code review for major changes or releases, with extra attention to architecture and breaking changes.

**When to use**:
- Before major releases
- When reviewing large PRs
- Architectural changes
- API changes that affect consumers

**How it works**: Enhanced version of code-review with additional focus on backward compatibility, API contracts, migration paths, and architectural consistency.

### 🐛 `/dev/linear-fix`
**Purpose**: Fix Linear ticket issues with comprehensive understanding and implementation.

**When to use**:
- Working on a Linear ticket
- Need to understand and fix a reported bug
- Implementing a feature from Linear
- Need context from Linear issue tracking

**How it works**: Fetches Linear ticket details, analyzes the issue comprehensively, implements the fix, and updates documentation as needed.

### 🔀 `/dev/resolve-merge-conflicts`
**Purpose**: Intelligently resolve git merge conflicts by understanding both sides of the changes.

**When to use**:
- After a failed merge or rebase
- When git reports conflicts
- Need to combine divergent branches
- Complex conflicts requiring semantic understanding

**How it works**: Analyzes both sides of conflicts, understands the intent of changes, resolves conflicts semantically (not just textually), and ensures the merged result maintains functionality.

### 📝 `/context/docs-update`
**Purpose**: Keep documentation synchronized with code changes, ensuring AI context remains current.

**When to use**:
- After modifying code
- After adding new features
- When project structure changes
- Following any significant implementation

**How it works**: Analyzes what changed and updates the appropriate CLAUDE.md files across all tiers. Maintains the context that future AI sessions will rely on.

### 📄 `/context/docs-create`
**Purpose**: Generate initial documentation structure for existing projects that lack AI-optimized documentation.

**When to use**:
- Adopting the framework in an existing project
- Starting documentation from scratch
- Need to document legacy code
- Setting up the 3-tier structure

**How it works**: Analyzes your project structure and creates appropriate CLAUDE.md files at each tier, establishing the foundation for AI-assisted development.

### ♻️ `/dev/refactor`
**Purpose**: Intelligently restructure code while maintaining functionality and updating all dependencies.

**When to use**:
- Breaking up large files
- Improving code organization
- Extracting reusable components
- Cleaning up technical debt

**How it works**: Analyzes file structure, maps dependencies, identifies logical split points, and handles all import/export updates across the codebase.

### 🤝 `/context/save-context`
**Purpose**: Preserve context when ending a session or when the conversation becomes too long.

**When to use**:
- Ending a work session
- Context limit approaching
- Switching between major tasks
- Supplementing `/compact` with permanent storage

**How it works**: Updates the handoff documentation with session achievements, current state, and next steps. Ensures smooth continuation in future sessions.

### 📥 `/context/restore-context`
**Purpose**: Resume work by restoring context from a previous session.

**When to use**:
- Starting a new session after using `/context/save-context`
- Continuing work after a break
- Picking up where another developer left off
- Need to understand recent changes and next steps

**How it works**: Loads the saved context documentation, analyzes recent work, and prepares for continuation of tasks. Provides a summary of what was accomplished and what needs to be done next.

### 🔍 `/context/get-context`
**Purpose**: Quickly gather relevant context about specific parts of the codebase without executing changes.

**When to use**:
- Need to understand a specific module or feature
- Quick analysis without implementation intent
- Gathering information for planning
- Lightweight alternative to `/full-context`

**How it works**: Performs targeted context gathering based on your query, focusing on understanding rather than implementation. More lightweight than full-context but still thorough for the specified scope.

### 📋 `/pm/create-prd`
**Purpose**: Create comprehensive Product Requirements Documents through interactive AI-powered questioning.

**When to use**:
- Starting a new product or feature
- Need structured requirements gathering
- Converting initial concepts into detailed specifications
- Ensuring no critical requirements are missed

**How it works**: Guides you through systematic questioning to gather complete requirements, validates content against the Taskmaster PRD template, and generates development-ready specifications.

### 🔧 `/pm/linear-refine`
**Purpose**: Analyze and improve existing PRDs through intelligent gap detection and targeted questioning.

**When to use**:
- Existing PRD needs improvement
- PRD has gaps or ambiguities
- Need to align PRD with current implementation
- Preparing PRD for task generation

**How it works**: Analyzes existing PRD for completeness and quality, identifies specific gaps and inconsistencies, generates targeted improvement questions, and produces an enhanced version.

### 🧪 `/test-generate`
**Purpose**: Generate comprehensive, concise UI regression tests from project documentation using MCP browser automation.

**When to use**:
- After implementing new features
- Need systematic test coverage
- Converting documentation into executable tests
- Establishing baseline test suite

**How it works**: Scans project documentation for testable features, generates minimal but comprehensive test cases with MCP browser automation steps, and creates idempotent tests when possible. Outputs to `./docs/tests/regression-tests.md`.

### 🔄 `/test-update`
**Purpose**: Update existing test cases based on new requirements or documentation changes.

**When to use**:
- Features have been modified
- New requirements added
- Tests need optimization
- Documentation has changed

**How it works**: Analyzes existing test suite and documentation changes, identifies what needs updating, preserves valid test results, and maintains test conciseness and idempotency.

### 🚀 `/test-run`
**Purpose**: Execute manual test cases using MCP browser automation with comprehensive evidence collection.

**When to use**:
- Before releases
- After major changes
- Validating bug fixes
- Systematic regression testing

**How it works**: Systematically executes test cases using MCP browser automation, captures screenshots and logs, documents results with evidence, and generates comprehensive test reports.

## Integration Patterns

### Typical Workflow
```bash
/full-context "implement user notifications"    # Understand
# ... implement the feature ...
/dev/code-review "review notification system"       # Validate
/context/docs-update "document notification feature"    # Synchronize
/context/save-context "completed notification system"        # Preserve
```

### Quick Analysis
```bash
/full-context "why is the API slow?"           # Investigate
# ... apply fixes ...
/context/docs-update "document performance fixes"       # Update context
```

### Major Refactoring
```bash
/full-context "analyze authentication module"   # Understand current state
/dev/refactor "@auth/large-auth-file.ts"          # Restructure
/dev/code-review "review refactored auth"          # Verify quality
/context/docs-update "document new auth structure"     # Keep docs current
```

### PRD Development
```bash
/pm/create-prd "mobile fitness tracking app"      # Create new PRD
# ... review and refine ...
/pm/linear-refine "@docs/prds/fitness-app-prd.md"   # Improve existing PRD
# ... generate tasks from PRD ...
```

### Test Development & Execution
```bash
/test-generate "focus on authentication flows"  # Generate test suite
# ... review tests ...
/test-update "add new dashboard tests"         # Update with new features
/test-run "high priority tests only"          # Execute critical tests
```


## Customization

Each command template can be adapted:

- **Adjust agent strategies** - Modify how many agents spawn and their specializations
- **Change context loading** - Customize which documentation tiers load
- **Tune MCP integration** - Adjust when to consult external services
- **Modify output formats** - Tailor results to your preferences

Commands are stored in `.claude/commands/` and can be edited directly.

## Key Principles

1. **Commands work together** - Each command builds on others' outputs
2. **Documentation stays current** - Commands maintain their own context
3. **Complexity scales naturally** - Simple tasks stay simple, complex tasks get sophisticated analysis
4. **Context is continuous** - Information flows between sessions through documentation

---

*For detailed implementation of each command, see the individual command files in this directory.*