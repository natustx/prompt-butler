# Prompt Butler Backend

FastAPI backend and CLI for managing AI prompts with markdown/YAML file storage.

## Features

- **CLI (`pb`)**: Command-line interface for managing prompts
- **REST API**: FastAPI backend for CRUD operations on prompts
- **Markdown Storage**: Prompts stored as markdown with YAML frontmatter (default: ~/.prompts)
- **Rich Output**: Beautiful terminal output with tables and syntax highlighting
- **JSON Mode**: Machine-readable output for scripting and automation
- Pydantic models for data validation
- CORS support for frontend integration
- Fuzzy search for finding prompts

## Setup

### Using Task (Recommended)

From the project root directory:

```bash
# Setup everything (backend + frontend)
task setup

# Or setup just the backend
task backend:setup

# Start development server
task backend:dev
```

### CLI Installation

```bash
# Install CLI in development mode (uses .venv)
task cli:dev

# Then activate the virtual environment to use pb command
source .venv/bin/activate

# Or install globally via pipx
task cli:install
```

### Manual Setup

From the backend directory:

```bash
# Create virtual environment with uv
uv venv ../.venv

# Install dependencies
uv pip install -e .
uv pip install -e ".[dev]"  # For development dependencies

# Activate virtual environment
source ../.venv/bin/activate

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## CLI Usage

The `pb` command provides a terminal interface for managing prompts.

### Basic Commands

```bash
# Show help
pb --help

# Show version
pb --version

# List all prompts
pb list

# List prompts filtered by tag or group
pb list --tag coding
pb list --group development

# Show a specific prompt
pb show my-prompt

# Search prompts (fuzzy matching)
pb search "code review"

# List all tags with counts
pb tags

# List all groups with counts
pb groups
```

### Creating Prompts

```bash
# Interactive mode - prompts for all fields
pb add

# Non-interactive with flags
pb add --name my-prompt --group development --description "My new prompt"

# With tags
pb add --name code-review --tags "coding,review,development"

# Open in editor after creation
pb add --name my-prompt --edit
```

### Editing Prompts

```bash
# Edit a prompt in $EDITOR
pb edit my-prompt

# Edit a prompt in a specific group
pb edit my-prompt --group development
```

The file is validated after editing. If the syntax is invalid, you'll see an error message.

### Cloning Prompts

```bash
# Clone a prompt with a new name
pb clone my-prompt my-new-prompt

# Clone to a different group
pb clone my-prompt my-new-prompt --group different-group

# Clone from a specific source group
pb clone my-prompt my-new-prompt --source-group development --group production
```

### JSON Output

Use `--json` for machine-readable output (great for scripting):

```bash
# Get prompts as JSON
pb --json list

# Get a specific prompt as JSON
pb --json show my-prompt

# Search with JSON output
pb --json search "test"
```

## Configuration

Environment variables can be set in a `.env` file (see `.env.example`):

- `PROMPTS_DIR`: Directory for storing YAML files (default: `~/.prompts`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)

## API Documentation

Once the server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Project Structure

```
backend/
├── cli.py               # Typer CLI application (pb command)
├── main.py              # FastAPI application and configuration
├── models.py            # Pydantic models for data validation
├── services/
│   └── storage.py       # Markdown/YAML storage service
├── routers/
│   └── prompts.py       # API endpoints
├── tests/               # Test suite
├── pyproject.toml       # Project dependencies and configuration
└── .env.example         # Environment variables template
```

## Prompt File Format

Prompts are stored as markdown files with YAML frontmatter:

```markdown
---
name: code-review
description: Reviews code for best practices
tags: [coding, review]
---

You are an expert code reviewer. Analyze the provided code for:
- Bugs and potential issues
- Best practices violations
- Performance concerns
- Security vulnerabilities

---user---

Please review the following code:

{code}
```

- **Group**: Derived from parent folder name (e.g., `~/.prompts/development/code-review.md` has group "development")
- **User Prompt**: Optional section after `---user---` separator

## Task Commands Reference

All available task commands (run from project root):

| Command | Description |
|---------|-------------|
| `task setup` | Install all dependencies (backend + frontend) |
| `task dev` | Start all development servers in parallel |
| `task lint` | Run all linters |
| `task test` | Run all tests |
| `task backend:setup` | Setup backend virtual environment |
| `task backend:dev` | Start backend development server |
| `task backend:test` | Run backend tests |
| `task backend:lint` | Run backend linter (ruff) |
| `task backend:lint:fix` | Auto-fix backend lint issues |
| `task cli:dev` | Install CLI in development mode |
| `task cli:install` | Install CLI globally via pipx |
| `task frontend:setup` | Setup frontend dependencies |
| `task frontend:dev` | Start frontend development server |
| `task frontend:lint` | Run frontend linter |

## Development

### Running Tests

```bash
# From backend directory with venv activated
pytest
```

### Code Formatting

```bash
# Format code with black
black .

# Check linting with ruff
ruff check .
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint returning service status
- `GET /health` - Health check endpoint

### Prompts API (To be implemented in Task 2)
- `GET /api/prompts` - List all prompts
- `GET /api/prompts/{name}` - Get a specific prompt
- `POST /api/prompts` - Create a new prompt
- `PUT /api/prompts/{name}` - Update an existing prompt
- `DELETE /api/prompts/{name}` - Delete a prompt
