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
    """Create storage with test prompts."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    # Create test prompts
    test_storage.create(Prompt(
        name='coding-assistant',
        description='Help with coding tasks',
        system_prompt='You are a coding assistant.',
        group='coding',
        tags=['python', 'development'],
    ))
    test_storage.create(Prompt(
        name='writing-helper',
        description='Help with writing tasks',
        system_prompt='You are a writing helper.',
        group='writing',
        tags=['creative', 'editing'],
    ))
    test_storage.create(Prompt(
        name='python-expert',
        description='Expert Python programmer',
        system_prompt='You are a Python expert.',
        group='coding',
        tags=['python', 'expert'],
    ))
    test_storage.create(Prompt(
        name='general-chat',
        description='General conversation',
        system_prompt='You are a helpful assistant.',
        group='',
        tags=['general'],
    ))

    import prompt_butler.cli as cli
    monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

    return test_storage


class TestListCommand:
    def test_list_all_prompts(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list'])

        assert result.exit_code == 0
        assert 'coding-assistant' in result.output
        assert 'writing-helper' in result.output
        assert 'python-expert' in result.output
        assert 'general-chat' in result.output
        assert '4 prompt(s) found' in result.output

    def test_list_empty(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        empty_storage = PromptStorage(prompts_dir=tmp_path)

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: empty_storage)

        result = runner.invoke(app, ['list'])

        assert result.exit_code == 0
        assert 'No prompts found' in result.output

    def test_list_with_tag_filter(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list', '--tag', 'python'])

        assert result.exit_code == 0
        assert 'coding-assistant' in result.output
        assert 'python-expert' in result.output
        assert 'writing-helper' not in result.output
        assert '2 prompt(s) found' in result.output

    def test_list_with_group_filter(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list', '--group', 'coding'])

        assert result.exit_code == 0
        assert 'coding-assistant' in result.output
        assert 'python-expert' in result.output
        assert 'writing-helper' not in result.output
        assert '2 prompt(s) found' in result.output

    def test_list_with_fuzzy_search(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list', 'python'])

        assert result.exit_code == 0
        assert 'python-expert' in result.output
        assert 'Search Results: "python"' in result.output

    def test_list_fuzzy_search_with_tag_filter(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list', 'coding', '--tag', 'python'])

        assert result.exit_code == 0
        assert 'coding-assistant' in result.output
        # python-expert doesn't match the search 'coding' as well
        assert 'writing-helper' not in result.output

    def test_list_fuzzy_search_with_group_filter(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list', 'expert', '--group', 'coding'])

        assert result.exit_code == 0
        assert 'python-expert' in result.output

    def test_list_fuzzy_search_no_results(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list', 'zzzzxyzzy'])

        assert result.exit_code == 0
        assert 'No prompts matching "zzzzxyzzy"' in result.output

    def test_list_combined_filters(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list', '--tag', 'python', '--group', 'coding'])

        assert result.exit_code == 0
        assert 'coding-assistant' in result.output
        assert 'python-expert' in result.output
        assert '2 prompt(s) found' in result.output

    def test_list_json_output(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['--json', 'list'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 4

        names = [p['name'] for p in data]
        assert 'coding-assistant' in names
        assert 'writing-helper' in names

    def test_list_json_output_with_filter(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['--json', 'list', '--tag', 'python'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

        for prompt in data:
            assert 'python' in prompt['tags']

    def test_list_json_output_with_query(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['--json', 'list', 'writing'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        # Should find writing-helper via fuzzy search

    def test_list_shows_table_columns(self, runner, storage_with_prompts):
        result = runner.invoke(app, ['list'])

        assert result.exit_code == 0
        # Check table has expected columns
        assert 'Name' in result.output
        assert 'Group' in result.output
        assert 'Description' in result.output
        assert 'Tags' in result.output

    def test_list_truncates_long_description(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        storage = PromptStorage(prompts_dir=tmp_path)
        long_desc = 'A' * 100
        storage.create(Prompt(
            name='long-desc',
            description=long_desc,
            system_prompt='Test',
        ))

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: storage)

        result = runner.invoke(app, ['list'])

        assert result.exit_code == 0
        # Description should be truncated (Rich uses unicode ellipsis)
        assert 'long-desc' in result.output
        # Full 100 A's should NOT appear in output
        assert 'A' * 100 not in result.output
