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

    # Create test prompts
    test_storage.create(Prompt(
        name='test-prompt',
        description='A test prompt',
        system_prompt='You are helpful.',
        group='testing',
        tags=['test'],
    ))
    test_storage.create(Prompt(
        name='ungrouped-prompt',
        description='An ungrouped prompt',
        system_prompt='Basic assistant.',
        group='',
        tags=[],
    ))

    import prompt_butler.cli as cli
    monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

    return test_storage


class TestDeleteCommand:
    def test_delete_with_force(self, runner, storage_with_prompt, tmp_path):
        # Verify prompt exists
        assert storage_with_prompt.read('test-prompt') is not None

        result = runner.invoke(app, ['delete', 'test-prompt', '--force'])

        assert result.exit_code == 0
        assert 'Deleted' in result.output
        assert 'test-prompt' in result.output

        # Verify prompt was deleted
        assert storage_with_prompt.read('test-prompt') is None

    def test_delete_with_confirmation_yes(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['delete', 'test-prompt'], input='y\n')

        assert result.exit_code == 0
        assert 'Deleted' in result.output
        assert storage_with_prompt.read('test-prompt') is None

    def test_delete_with_confirmation_no(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['delete', 'test-prompt'], input='n\n')

        assert result.exit_code == 0
        assert 'Cancelled' in result.output
        # Prompt should still exist
        assert storage_with_prompt.read('test-prompt') is not None

    def test_delete_prompt_not_found(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['delete', 'nonexistent', '--force'])

        assert result.exit_code == 1
        assert 'not found' in result.output

    def test_delete_with_group_filter(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['delete', 'test-prompt', '--group', 'testing', '--force'])

        assert result.exit_code == 0
        assert 'Deleted' in result.output
        assert storage_with_prompt.read('test-prompt', group='testing') is None

    def test_delete_ungrouped_prompt(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['delete', 'ungrouped-prompt', '--force'])

        assert result.exit_code == 0
        assert 'Deleted' in result.output
        assert storage_with_prompt.read('ungrouped-prompt') is None

    def test_delete_json_output(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['--json', 'delete', 'test-prompt', '--force'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['deleted'] is True
        assert data['name'] == 'test-prompt'
        assert data['group'] == 'testing'

    def test_delete_json_not_found(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['--json', 'delete', 'nonexistent', '--force'])

        assert result.exit_code == 1

    def test_delete_shows_group_in_confirmation(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['delete', 'test-prompt'], input='n\n')

        assert 'testing' in result.output  # Group should be shown in confirmation
        assert 'Cancelled' in result.output

    def test_delete_force_flag_short(self, runner, storage_with_prompt):
        result = runner.invoke(app, ['delete', 'test-prompt', '-f'])

        assert result.exit_code == 0
        assert 'Deleted' in result.output
