import json

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app
from prompt_butler.models import Prompt


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def storage_with_prompts(tmp_path, monkeypatch):
    """Create storage with prompts in different groups."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    # Create prompts in different groups
    test_storage.create(Prompt(
        name='prompt1',
        system_prompt='System 1',
        group='coding',
    ))
    test_storage.create(Prompt(
        name='prompt2',
        system_prompt='System 2',
        group='coding',
    ))
    test_storage.create(Prompt(
        name='prompt3',
        system_prompt='System 3',
        group='writing',
    ))
    test_storage.create(Prompt(
        name='prompt4',
        system_prompt='System 4',
        group='',
    ))

    import prompt_butler.cli as cli
    monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

    return test_storage


class TestIndexCommand:
    def test_index_shows_count(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['index'])

        assert result.exit_code == 0
        assert '4' in result.output
        assert 'Indexed' in result.output

    def test_index_shows_group_breakdown(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['index'])

        assert result.exit_code == 0
        assert 'coding' in result.output
        assert 'writing' in result.output
        assert '(root)' in result.output

    def test_index_empty_directory(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        empty_storage = PromptStorage(prompts_dir=tmp_path)

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: empty_storage)

        result = runner.invoke(app, ['index'])

        assert result.exit_code == 0
        assert '0' in result.output

    def test_index_json_output(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['--json', 'index'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['indexed'] is True
        assert data['count'] == 4
        assert 'coding' in data['groups']
        assert data['groups']['coding'] == 2
        assert 'writing' in data['groups']
        assert data['groups']['writing'] == 1
        assert '(root)' in data['groups']
        assert data['groups']['(root)'] == 1

    def test_index_json_shows_prompts_dir(self, runner, storage_with_prompts, tmp_path):
        result = runner.invoke(app, ['--json', 'index'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'prompts_dir' in data

    def test_index_json_empty_directory(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        empty_storage = PromptStorage(prompts_dir=tmp_path)

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: empty_storage)

        result = runner.invoke(app, ['--json', 'index'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['indexed'] is True
        assert data['count'] == 0
        assert data['groups'] == {}

    def test_index_shows_directory_path(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['index'])

        assert result.exit_code == 0
        assert 'Directory:' in result.output
