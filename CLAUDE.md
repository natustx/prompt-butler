# Claude Code Instructions

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md


## Coding Instructions

### IMPORTANT Instructions
- IMPORTANT: Do not run any servers directly, rather tell the user to run servers for testing.

### General Instructions
- Your most important job is to manage your own context. Always read any relevant files BEFORE planning changes.
- When updating documentation, keep updates concise and on point to prevent bloat.
- Write code following KISS, YAGNI, and DRY principles.
- When in doubt follow proven best practices for implementation.
- Do not commit to git without user approval.
- Always consider industry standard libraries/frameworks first over custom implementations.
- Never mock anything (other than tests). Never use placeholders. Never omit code.
- Apply SOLID principles where relevant. Use modern framework features rather than reinventing solutions.
- Be brutally honest about whether an idea is good or bad.
- Make side effects explicit and minimal.
- Design database schema to be evolution-friendly (avoid breaking changes).
- Always check quality before completing a task. Linting errors must be fixed and tests must pass before proceeding.
- Always ask the user for confirmation before considering a task complete.
- Always use TodoRead and TodoWrite to track progress on complex multi-step tasks.
- Never add comments to code explaining the change you made, or leave behind comments when you delete code. Comments should only be used to explain the code, not the change you made.

### File Organization & Modularity
- Default to creating multiple small, focused files rather than large monolithic ones
- Each file should have a single responsibility and clear purpose
- Keep files under 350 lines when possible - split larger files by extracting utilities, constants, types, or logical components into separate modules
- Separate concerns: utilities, constants, types, components, and business logic into different files
- Prefer composition over inheritance - use inheritance only for true 'is-a' relationships, favor composition for 'has-a' or behavior mixing
- Follow existing project structure and conventions - place files in appropriate directories. Create new directories and move files if deemed appropriate.
- Use well defined sub-directories to keep things organized and scalable
- Structure projects with clear folder hierarchies and consistent naming conventions
- Import/export properly - design for reusability and maintainability

### Python Code Style
**IMPORTANT: All Python code in this monorepo must follow these formatting standards:**
- Use `ruff` for both linting and formatting (NOT black)
- 120 characters maximum line length
- Single quotes for strings (not double quotes)
- Use ruff's import sorting (isort-compatible)
- Keep trailing commas in multi-line structures

### Security First
- Never trust external inputs - validate everything at the boundaries
- IMPORTANT: NEVER PUT SECRETS IN CODE!!!! Keep secrets in environment variables.
- Log security events (login attempts, auth failures, rate limits, permission denials) but never log sensitive data (video content, transcripts, tokens, personal info)
- Authenticate users at the API gateway level - never trust client-side tokens
- Use Row Level Security (RLS) to enforce data isolation between users
- Design auth to work across all client types consistently
- Use secure authentication patterns for your platform
- Validate all authentication tokens server-side before creating sessions
- Sanitize all user inputs before storing or processing

### Error Handling
- Use specific exceptions over generic ones
- Always log errors with context
- Provide helpful error messages
- Fail securely - errors shouldn't reveal system internals

### Observable Systems & Logging Standards
- Every request needs a correlation ID for debugging
- Structure logs for machines, not humans - use JSON format with consistent fields (timestamp, level, correlation_id, event, context) for automated analysis
- Make debugging possible across service boundaries

### State Management
- Have one source of truth for each piece of state
- Make state changes explicit and traceable
- Design for scalable video processing - use job IDs for task coordination, avoid storing large video data in server memory
- Keep processing history lightweight (metadata and summaries, not full video content)

### API Design Principles
- RESTful design with consistent URL patterns
- Use HTTP status codes correctly
- Version APIs from day one (/v1/, /v2/)
- Support pagination for list endpoints
- Use consistent JSON response format:
  - Success: `{ "data": {...}, "error": null }`
  - Error: `{ "data": null, "error": {"message": "...", "code": "..."} }`


### Workflows

The general workflow for coding is:

1. Read the task details in taskmaster and any relevant files
2. Mark the task as "in progress" in taskmaster
3. Plan the changes
4. Write the code
5. Run the quality checks
6. Fix any linting or test errors immediately
7. Mark the task as "review" in taskmaster
8. Ask the user for feedback on the changes, and to confirm when done
9.  Mark the task as done in taskmaster
10. Update documentation