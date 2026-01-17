# Prompt Manager Backend

FastAPI backend for managing AI prompts with YAML file storage.

## Features

- RESTful API for CRUD operations on prompts
- YAML file-based storage (default: ~/.prompts)
- Pydantic models for data validation
- CORS support for frontend integration
- Comprehensive error handling

## Setup

### Using Task (Recommended)

From the project root directory:

```bash
# Setup backend environment and install dependencies
task backend:setup

# Start development server
task backend:dev
```

### Manual Setup

From the backend directory:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"  # For development dependencies

# Start development server
uvicorn prompt_butler.main:app --reload --host 0.0.0.0 --port 8000
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
├── main.py              # FastAPI application and configuration
├── models.py            # Pydantic models for data validation
├── services/
│   └── storage.py       # YAML storage service
├── routers/
│   └── prompts.py       # API endpoints (to be implemented)
├── pyproject.toml       # Project dependencies and configuration
└── .env.example         # Environment variables template
```

## Prompt YAML Format

Prompts are stored as YAML files with the following structure:

```yaml
name: example_prompt
description: An example prompt for demonstration
system_prompt: You are a helpful assistant.
user_prompt: Please help me with the following task...
```

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
