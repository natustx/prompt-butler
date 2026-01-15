# Prompt Butler Design

Rename Prompt Manager → Prompt Butler. Add CLI (`pb`) + TUI + terminal-styled web app.

## Core Decisions

| Decision | Choice |
|----------|--------|
| File format | Markdown w/ YAML frontmatter |
| Folder structure | Single-level groups: `~/.prompts/{group}/name.md` |
| CLI framework | Typer |
| TUI framework | Textual |
| Search | In-memory fuzzy (rapidfuzz) |
| Tag autocomplete | Scan existing tags on demand |
| Web styling | Terminal aesthetic on existing shadcn |
| CLI binary | `pb` |
| Migration | One-time `pb migrate`, then drop YAML |
| Config | `~/.config/prompt-butler/config.yaml` |
| Editor | Respect `$EDITOR` |
| Web hosting | Static files served by FastAPI |

## File Format

```markdown
---
name: code-review
description: Reviews code for best practices
tags: [coding, review]
---

System prompt content here...

---user---

User prompt content here (optional section)
```

- Group derived from parent folder
- Filename is slugified name
- `---user---` separator for user prompt section

## Directory Structure

```
~/.prompts/
├── coding/
│   ├── code-review.md
│   └── unit-test.md
├── writing/
│   └── blog-post.md
└── quick-summary.md      # ungrouped
```

## CLI Commands

```bash
# Prompt CRUD
pb add                          # Interactive creation
pb add --name=x --group=coding --edit
pb list                         # All prompts
pb list "query"                 # Fuzzy search
pb list --tag=coding --group=x  # Filter
pb show <name>
pb edit <name>                  # Opens $EDITOR
pb delete <name>                # With confirmation
pb copy <name>                  # Copy to clipboard
pb clone <name> <newname>       # Duplicate

# Tags & Groups
pb tag list
pb tag rename <old> <new>
pb group list
pb group create <name>
pb group rename <old> <new>

# Utility
pb migrate                      # YAML → markdown
pb index                        # Rebuild index
pb config
pb tui                          # Launch TUI
```

Output: pretty tables (default), `--json` for scripting.

## TUI Design

Launch: `pb tui`

**Screens:**
1. **List View** - table, keyboard nav (j/k/Enter), `/` search, sidebar filter
2. **Detail View** - full content, `c` copy, `Esc` back
3. **Add/Edit Modal** - form w/ tag/group autocomplete, markdown textarea

**Styling:** Monospace, green/amber on dark, box-drawing borders

**Editing:** Plain textarea w/ markdown syntax highlighting. Delete requires confirmation.

## Web App Styling

Terminal aesthetic on existing shadcn:
- Font: JetBrains Mono / Fira Code
- Colors: near-black bg, green/amber accents
- Effects: scanline overlay, CRT glow, no rounded corners
- Components: bordered buttons, green outlines

## Architecture

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│   API   │  │   CLI   │  │   TUI   │
└────┬────┘  └────┬────┘  └────┬────┘
     └────────────┴────────────┘
                  │
         ┌───────┴────────┐
         │ PromptStorage  │  ← ALL logic here
         └───────┬────────┘
                 │
         ┌───────┴────────┐
         │   Filesystem   │
         └────────────────┘
```

API, CLI, TUI are thin presentation layers. PromptStorage handles all business logic.

## Backend Model

```python
class Prompt(BaseModel):
    name: str
    description: str = ""
    system_prompt: str
    user_prompt: str = ""
    tags: list[str] = []
    group: str = ""
```

New endpoints: `GET /api/tags`, `GET /api/groups`, `POST /api/tags/rename`, `POST /api/groups/rename`

## Project Structure

```
prompt-butler/
├── backend/
│   ├── prompt_butler/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── cli.py              # Typer CLI
│   │   ├── tui/
│   │   │   ├── app.py
│   │   │   └── screens/
│   │   ├── routers/
│   │   └── services/
│   │       └── storage.py      # PromptStorage
│   └── pyproject.toml
├── frontend/
├── Taskfile.yml
└── docs/
```

## Taskfile

```yaml
version: "3"
tasks:
  dev:
    deps: [backend:dev, frontend:dev]
  backend:dev:
    dir: backend
    cmd: uvicorn prompt_butler.main:app --reload --port 8000
  frontend:dev:
    dir: frontend
    cmd: npm run dev
  setup:
    deps: [backend:setup, frontend:setup]
  backend:setup:
    dir: backend
    cmd: uv sync
  frontend:setup:
    dir: frontend
    cmd: npm install
  cli:install:
    cmd: pipx install ./backend --force
  cli:dev:
    dir: backend
    cmd: uv pip install -e .
  tui:dev:
    dir: backend
    cmd: textual run --dev prompt_butler.tui.app:app
  frontend:build:
    dir: frontend
    cmd: npm run build
  lint:
    deps: [backend:lint, frontend:lint]
  backend:lint:
    dir: backend
    cmd: ruff check .
  frontend:lint:
    dir: frontend
    cmd: npm run lint
  test:
    dir: backend
    cmd: pytest
```

## Implementation Order

1. Rename + restructure (Prompt Manager → Prompt Butler)
2. Storage service (markdown w/ frontmatter, groups)
3. Migration command (`pb migrate`), delete YAML code
4. CLI core (`pb add/list/show/edit/delete/copy/clone`)
5. CLI extras (`pb tag/group`, search)
6. TUI (list, detail, add/edit)
7. Web restyling (terminal aesthetic)
8. Web updates (groups, tag autocomplete)

## Key Libraries

| Purpose | Library |
|---------|---------|
| CLI | typer, rich |
| TUI | textual |
| Fuzzy search | rapidfuzz |
| Clipboard | pyperclip |
| Frontmatter | python-frontmatter |
| YAML | pyyaml |
