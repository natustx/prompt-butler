import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app
from prompt_butler.models import Prompt


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def storage_with_prompt(tmp_path, monkeypatch):
    """Create storage with test prompts."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    # Create test prompt with both system and user prompts
    test_storage.create(Prompt(
        name='full-prompt',
        description='A prompt with both parts',
        system_prompt='You are a helpful assistant.',
        user_prompt='Please help me with this task.',
        group='testing',
        tags=['test'],
    ))

    # Create prompt without user prompt
    test_storage.create(Prompt(
        name='system-only',
        description='System prompt only',
        system_prompt='You are a system assistant.',
        user_prompt='',
        group='',
        tags=[],
    ))

    import prompt_butler.cli as cli
    monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

    return test_storage


class TestCopyCommand:
    @patch('pyperclip.copy')
    def test_copy_system_prompt_default(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['copy', 'full-prompt'])

        assert result.exit_code == 0
        assert 'Copied system prompt' in result.output
        assert 'full-prompt' in result.output
        mock_copy.assert_called_once_with('You are a helpful assistant.')

    @patch('pyperclip.copy')
    def test_copy_user_prompt(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['copy', 'full-prompt', '--user'])

        assert result.exit_code == 0
        assert 'Copied user prompt' in result.output
        mock_copy.assert_called_once_with('Please help me with this task.')

    @patch('pyperclip.copy')
    def test_copy_all_prompts(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['copy', 'full-prompt', '--all'])

        assert result.exit_code == 0
        assert 'Copied system and user prompts' in result.output
        expected = 'You are a helpful assistant.\n\n---\n\nPlease help me with this task.'
        mock_copy.assert_called_once_with(expected)

    @patch('pyperclip.copy')
    def test_copy_all_without_user_prompt(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['copy', 'system-only', '--all'])

        assert result.exit_code == 0
        # Should just copy system prompt without separator
        mock_copy.assert_called_once_with('You are a system assistant.')

    def test_copy_user_prompt_when_none_exists(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['copy', 'system-only', '--user'])

        assert result.exit_code == 1
        assert 'no user prompt' in result.output

    def test_copy_prompt_not_found(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['copy', 'nonexistent'])

        assert result.exit_code == 1
        assert 'not found' in result.output

    @patch('pyperclip.copy')
    def test_copy_with_group_filter(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['copy', 'full-prompt', '--group', 'testing'])

        assert result.exit_code == 0
        mock_copy.assert_called_once()

    @patch('pyperclip.copy')
    def test_copy_json_output(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['--json', 'copy', 'full-prompt'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['copied'] is True
        assert data['name'] == 'full-prompt'
        assert data['type'] == 'system'
        assert data['length'] == len('You are a helpful assistant.')

    @patch('pyperclip.copy')
    def test_copy_json_user_type(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['--json', 'copy', 'full-prompt', '--user'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['type'] == 'user'

    @patch('pyperclip.copy')
    def test_copy_json_all_type(self, mock_copy, runner, storage_with_prompt):
        result = runner.invoke(app, ['--json', 'copy', 'full-prompt', '--all'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['type'] == 'all'

    @patch('pyperclip.copy')
    def test_copy_short_flags(self, mock_copy, runner, storage_with_prompt):
        # Test short flags -u and -a
        result = runner.invoke(app, ['copy', 'full-prompt', '-u'])
        assert result.exit_code == 0

        result = runner.invoke(app, ['copy', 'full-prompt', '-a'])
        assert result.exit_code == 0
