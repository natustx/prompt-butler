import json

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app
from prompt_butler.models import Prompt


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def storage_with_prompt(tmp_path, monkeypatch):
    """Create storage with a test prompt."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    # Create test prompt with all fields
    test_storage.create(Prompt(
        name='test-prompt',
        description='A test prompt for testing',
        system_prompt='You are a helpful assistant.',
        user_prompt='Hello, how can you help me today?',
        group='testing',
        tags=['test', 'example'],
    ))

    # Create prompt without user_prompt
    test_storage.create(Prompt(
        name='minimal-prompt',
        description='Minimal prompt',
        system_prompt='Basic system prompt.',
        group='',
        tags=[],
    ))

    import prompt_butler.cli as cli
    monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

    return test_storage


class TestShowCommand:
    def test_show_existing_prompt(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'test-prompt'])

        assert result.exit_code == 0
        assert 'test-prompt' in result.output
        assert 'testing' in result.output
        assert 'A test prompt for testing' in result.output
        assert '#test' in result.output
        assert '#example' in result.output

    def test_show_displays_system_prompt(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'test-prompt'])

        assert result.exit_code == 0
        assert 'System Prompt' in result.output
        assert 'You are a helpful assistant.' in result.output

    def test_show_displays_user_prompt(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'test-prompt'])

        assert result.exit_code == 0
        assert 'User Prompt' in result.output
        assert 'Hello, how can you help me today?' in result.output

    def test_show_without_user_prompt(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'minimal-prompt'])

        assert result.exit_code == 0
        assert 'minimal-prompt' in result.output
        assert 'Basic system prompt.' in result.output
        # User Prompt section should not appear
        assert 'User Prompt' not in result.output

    def test_show_prompt_not_found(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'nonexistent'])

        assert result.exit_code == 1
        assert 'not found' in result.output

    def test_show_with_group_filter(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'test-prompt', '--group', 'testing'])

        assert result.exit_code == 0
        assert 'test-prompt' in result.output
        assert 'testing' in result.output

    def test_show_json_output(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['--json', 'show', 'test-prompt'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['name'] == 'test-prompt'
        assert data['description'] == 'A test prompt for testing'
        assert data['system_prompt'] == 'You are a helpful assistant.'
        assert data['user_prompt'] == 'Hello, how can you help me today?'
        assert data['group'] == 'testing'
        assert data['tags'] == ['test', 'example']

    def test_show_json_not_found(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['--json', 'show', 'nonexistent'])

        assert result.exit_code == 1
        # Error should be in stderr as JSON

    def test_show_displays_tags(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'test-prompt'])

        assert result.exit_code == 0
        assert 'Tags' in result.output
        assert 'test' in result.output
        assert 'example' in result.output

    def test_show_displays_group_in_header(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['show', 'test-prompt'])

        assert result.exit_code == 0
        # Group should appear near the name
        assert 'testing' in result.output
