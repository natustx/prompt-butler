import json

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app
from prompt_butler.models import Prompt


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def storage_with_groups(tmp_path, monkeypatch):
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


class TestGroupList:
    def test_group_list_shows_all_groups(self, runner, storage_with_groups):
        result = runner.invoke(app, ['group', 'list'])

        assert result.exit_code == 0
        assert 'coding' in result.output
        assert 'writing' in result.output

    def test_group_list_shows_counts(self, runner, storage_with_groups):
        result = runner.invoke(app, ['--json', 'group', 'list'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['coding'] == 2
        assert data['writing'] == 1

    def test_group_list_shows_root(self, runner, storage_with_groups):
        result = runner.invoke(app, ['group', 'list'])

        assert result.exit_code == 0
        assert '(root)' in result.output

    def test_group_list_empty(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        empty_storage = PromptStorage(prompts_dir=tmp_path)

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: empty_storage)

        result = runner.invoke(app, ['group', 'list'])

        assert result.exit_code == 0
        assert 'No groups found' in result.output

    def test_group_list_json_output(self, runner, storage_with_groups):
        result = runner.invoke(app, ['--json', 'group', 'list'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['coding'] == 2
        assert data['writing'] == 1
        assert data[''] == 1  # Root group


class TestGroupCreate:
    def test_group_create_makes_folder(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        test_storage = PromptStorage(prompts_dir=tmp_path)

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

        result = runner.invoke(app, ['group', 'create', 'new-group'])

        assert result.exit_code == 0
        assert 'Created group' in result.output
        assert 'new-group' in result.output
        assert (tmp_path / 'new-group').exists()

    def test_group_create_already_exists(self, runner, storage_with_groups, tmp_path):
        result = runner.invoke(app, ['group', 'create', 'coding'])

        assert result.exit_code == 1
        assert 'already exists' in result.output

    def test_group_create_invalid_name(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        test_storage = PromptStorage(prompts_dir=tmp_path)

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

        result = runner.invoke(app, ['group', 'create', 'invalid name!'])

        assert result.exit_code == 1
        assert 'alphanumeric' in result.output

    def test_group_create_json_output(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        test_storage = PromptStorage(prompts_dir=tmp_path)

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

        result = runner.invoke(app, ['--json', 'group', 'create', 'new-group'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['created'] is True
        assert data['name'] == 'new-group'


class TestGroupRename:
    def test_group_rename_moves_folder(self, runner, storage_with_groups, tmp_path):
        result = runner.invoke(app, ['group', 'rename', 'coding', 'programming'])

        assert result.exit_code == 0
        assert 'Renamed group' in result.output
        assert 'coding' in result.output
        assert 'programming' in result.output
        assert '2 prompt(s) moved' in result.output

        # Verify folder was renamed
        assert not (tmp_path / 'coding').exists()
        assert (tmp_path / 'programming').exists()

    def test_group_rename_not_found(self, runner, storage_with_groups):
        result = runner.invoke(app, ['group', 'rename', 'nonexistent', 'new-name'])

        assert result.exit_code == 1
        assert 'does not exist' in result.output

    def test_group_rename_target_exists(self, runner, storage_with_groups):
        result = runner.invoke(app, ['group', 'rename', 'coding', 'writing'])

        assert result.exit_code == 1
        assert 'already exists' in result.output

    def test_group_rename_invalid_new_name(self, runner, storage_with_groups):
        result = runner.invoke(app, ['group', 'rename', 'coding', 'invalid name!'])

        assert result.exit_code == 1
        assert 'alphanumeric' in result.output

    def test_group_rename_json_output(self, runner, storage_with_groups, tmp_path):
        result = runner.invoke(app, ['--json', 'group', 'rename', 'coding', 'programming'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['renamed'] is True
        assert data['old_name'] == 'coding'
        assert data['new_name'] == 'programming'
        assert data['prompts_moved'] == 2


class TestLegacyGroupsCommand:
    def test_legacy_groups_command_still_works(self, runner, storage_with_groups):
        result = runner.invoke(app, ['groups'])

        assert result.exit_code == 0
        assert 'coding' in result.output
        assert 'writing' in result.output
