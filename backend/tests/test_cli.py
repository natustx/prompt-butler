"""Integration tests for CLI commands.

Tests use real filesystem operations with temporary directories.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app, prompt_to_dict
from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptStorage


@pytest.fixture
def storage(tmp_path):
    """Create a PromptStorage instance with a temporary directory."""
    return PromptStorage(prompts_dir=tmp_path)


@pytest.fixture
def sample_prompt():
    """Create a sample prompt for testing."""
    return Prompt(
        name='test-prompt',
        description='A test prompt',
        system_prompt='You are a helpful assistant.',
        user_prompt='Help me with {task}.',
        tags=['test', 'sample'],
        group='',
    )


@pytest.fixture
def runner(storage, monkeypatch):
    """Create a CLI runner with a patched storage instance."""
    monkeypatch.setattr('prompt_butler.cli.get_storage', lambda: storage)
    return CliRunner()


class TestPromptToDict:
    """Tests for prompt serialization."""

    def test_converts_all_fields(self, sample_prompt):
        result = prompt_to_dict(sample_prompt)

        assert result['name'] == 'test-prompt'
        assert result['description'] == 'A test prompt'
        assert result['system_prompt'] == 'You are a helpful assistant.'
        assert result['user_prompt'] == 'Help me with {task}.'
        assert result['tags'] == ['test', 'sample']
        assert result['group'] == ''


class TestListCommand:
    """Tests for pb list command."""

    def test_list_empty(self, runner):
        result = runner.invoke(app, ['list'])

        assert result.exit_code == 0
        assert 'No prompts found' in result.output

    def test_list_shows_prompts_in_table(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['list'])

        assert result.exit_code == 0
        assert 'test-prompt' in result.output
        assert 'ungrouped' in result.output

    def test_list_with_json_output(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['list', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]['name'] == 'test-prompt'

    def test_list_filters_by_group(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', group='g1'))
        storage.create(Prompt(name='p2', system_prompt='sys', group='g2'))

        result = runner.invoke(app, ['list', '--group', 'g1', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]['name'] == 'p1'

    def test_list_filters_by_tag(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', tags=['web']))
        storage.create(Prompt(name='p2', system_prompt='sys', tags=['cli']))

        result = runner.invoke(app, ['list', '--tag', 'web', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]['name'] == 'p1'

    def test_list_fuzzy_search(self, runner, storage):
        storage.create(Prompt(name='code-review', system_prompt='sys'))
        storage.create(Prompt(name='summarize', system_prompt='sys'))

        result = runner.invoke(app, ['list', 'crv', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]['name'] == 'code-review'


class TestShowCommand:
    """Tests for pb show command."""

    def test_show_displays_prompt(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['show', 'test-prompt'])

        assert result.exit_code == 0
        assert 'test-prompt' in result.output
        assert 'You are a helpful assistant.' in result.output

    def test_show_with_json_output(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['show', 'test-prompt', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['name'] == 'test-prompt'
        assert data['system_prompt'] == 'You are a helpful assistant.'

    def test_show_not_found(self, runner):
        result = runner.invoke(app, ['show', 'nonexistent'])

        assert result.exit_code == 1

    def test_show_not_found_json(self, runner):
        result = runner.invoke(app, ['show', 'nonexistent', '--json'])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data['status'] == 'error'


class TestDeleteCommand:
    """Tests for pb delete command."""

    def test_delete_with_force_removes_prompt(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['delete', 'test-prompt', '--force'])

        assert result.exit_code == 0
        assert not storage.exists('test-prompt', '')

    def test_delete_with_json_output(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['delete', 'test-prompt', '--force', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'deleted'

    def test_delete_not_found(self, runner):
        result = runner.invoke(app, ['delete', 'nonexistent', '--force'])

        assert result.exit_code == 1

    def test_delete_confirmation_cancelled(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['delete', 'test-prompt'], input='no\n')

        assert result.exit_code == 0
        assert storage.exists('test-prompt', '')
        assert 'Cancelled' in result.output

    def test_delete_confirmation_accepted(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['delete', 'test-prompt'], input='yes\n')

        assert result.exit_code == 0
        assert not storage.exists('test-prompt', '')


class TestCloneCommand:
    """Tests for pb clone command."""

    def test_clone_creates_copy(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['clone', 'test-prompt', 'test-prompt-copy'])

        assert result.exit_code == 0
        assert storage.exists('test-prompt', '')
        assert storage.exists('test-prompt-copy', '')

        cloned = storage.get('test-prompt-copy', '')
        assert cloned.system_prompt == sample_prompt.system_prompt
        assert cloned.tags == sample_prompt.tags

    def test_clone_to_different_group(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['clone', 'test-prompt', 'test-prompt-copy', '--target-group', 'other'])

        assert result.exit_code == 0
        assert storage.exists('test-prompt-copy', 'other')

    def test_clone_with_json_output(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['clone', 'test-prompt', 'test-clone', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'cloned'
        assert data['source'] == 'test-prompt'
        assert data['target'] == 'test-clone'

    def test_clone_source_not_found(self, runner):
        result = runner.invoke(app, ['clone', 'nonexistent', 'new'])

        assert result.exit_code == 1

    def test_clone_target_exists(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)
        storage.create(Prompt(name='existing', system_prompt='sys', group=''))

        result = runner.invoke(app, ['clone', 'test-prompt', 'existing'])

        assert result.exit_code == 1


class TestCopyCommand:
    """Tests for pb copy command."""

    def test_copy_system_prompt(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        mock_pyperclip = MagicMock()
        with patch.dict('sys.modules', {'pyperclip': mock_pyperclip}):
            result = runner.invoke(app, ['copy', 'test-prompt'])

        assert result.exit_code == 0
        mock_pyperclip.copy.assert_called_once_with('You are a helpful assistant.')

    def test_copy_user_prompt(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        mock_pyperclip = MagicMock()
        with patch.dict('sys.modules', {'pyperclip': mock_pyperclip}):
            result = runner.invoke(app, ['copy', 'test-prompt', '--user'])

        assert result.exit_code == 0
        mock_pyperclip.copy.assert_called_once_with('Help me with {task}.')

    def test_copy_with_json_output(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        mock_pyperclip = MagicMock()
        with patch.dict('sys.modules', {'pyperclip': mock_pyperclip}):
            result = runner.invoke(app, ['copy', 'test-prompt', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'copied'

    def test_copy_not_found(self, runner):
        result = runner.invoke(app, ['copy', 'nonexistent'])

        assert result.exit_code == 1

    def test_copy_empty_user_prompt(self, runner, storage):
        storage.create(Prompt(name='no-user', system_prompt='sys', user_prompt='', group=''))

        result = runner.invoke(app, ['copy', 'no-user', '--user'])

        assert result.exit_code == 1


class TestAddCommand:
    """Tests for pb add command."""

    def test_add_with_stdin(self, runner, storage):
        result = runner.invoke(app, ['add', '--name', 'new-prompt'], input='System prompt content')

        assert result.exit_code == 0
        assert storage.exists('new-prompt', '')

        prompt = storage.get('new-prompt', '')
        assert prompt.system_prompt == 'System prompt content'

    def test_add_with_json_output(self, runner, storage):
        result = runner.invoke(app, ['add', '--name', 'json-prompt', '--json'], input='System prompt')

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'created'
        assert data['prompt']['name'] == 'json-prompt'

    def test_add_duplicate_fails(self, runner, storage):
        storage.create(Prompt(name='existing', system_prompt='sys', group=''))

        result = runner.invoke(app, ['add', '--name', 'existing'], input='New content')

        assert result.exit_code == 1

    def test_add_empty_prompt_fails(self, runner):
        result = runner.invoke(app, ['add', '--name', 'empty'], input='')

        assert result.exit_code == 1


class TestMainEntryPoint:
    """Tests for main CLI entry point."""

    def test_no_command_shows_help(self, runner):
        result = runner.invoke(app, [])

        assert result.exit_code == 0
        assert 'Prompt Butler' in result.output or 'Usage' in result.output

    def test_list_command_routes_correctly(self, runner):
        result = runner.invoke(app, ['list', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_show_command_routes_correctly(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['show', 'test-prompt', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['name'] == 'test-prompt'


class TestIndexCommand:
    """Tests for pb index command."""

    def test_index_empty_storage(self, runner):
        result = runner.invoke(app, ['index'])

        assert result.exit_code == 0
        assert 'Indexed 0 prompt(s)' in result.output

    def test_index_with_prompts(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)
        storage.create(Prompt(name='second', system_prompt='sys', group='other'))

        result = runner.invoke(app, ['index'])

        assert result.exit_code == 0
        assert 'Indexed 2 prompt(s)' in result.output
        assert '1 group(s)' in result.output

    def test_index_with_json_output(self, runner, storage, sample_prompt):
        storage.create(sample_prompt)

        result = runner.invoke(app, ['index', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'indexed'
        assert data['prompts_count'] == 1
        assert data['groups_count'] == 0
        assert data['groups'] == []


class TestConfigCommand:
    """Tests for pb config command."""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file path."""
        return tmp_path / 'config.yaml'

    @pytest.fixture
    def config_service_patch(self, monkeypatch, config_file):
        """Patch ConfigService to use temporary config file."""
        from prompt_butler.services import config as config_module

        original_init = config_module.ConfigService.__init__

        def patched_init(self, config_path=None):
            original_init(self, config_path=config_file)

        monkeypatch.setattr(config_module.ConfigService, '__init__', patched_init)
        return config_file

    def test_config_shows_all_values(self, runner, config_service_patch):
        result = runner.invoke(app, ['config'])

        assert result.exit_code == 0
        assert 'prompts_dir:' in result.output
        assert 'default_group:' in result.output

    def test_config_with_json_output(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'prompts_dir' in data
        assert 'default_group' in data
        assert 'config_file' in data

    def test_config_get_specific_key(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', 'prompts_dir'])

        assert result.exit_code == 0
        assert 'prompts_dir' in result.output

    def test_config_get_specific_key_json(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', 'prompts_dir', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['key'] == 'prompts_dir'

    def test_config_set_value(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', 'prompts_dir', '/new/path'])

        assert result.exit_code == 0
        assert 'Set prompts_dir' in result.output

    def test_config_set_value_json(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', 'prompts_dir', '/new/path', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'updated'
        assert data['key'] == 'prompts_dir'
        assert data['value'] == '/new/path'

    def test_config_unknown_key_fails(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', 'nonexistent'])

        assert result.exit_code == 1

    def test_config_set_unknown_key_fails(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', 'nonexistent', 'val'])

        assert result.exit_code == 1

    def test_config_edit_opens_editor(self, runner, config_service_patch, monkeypatch):
        monkeypatch.setenv('EDITOR', 'true')

        result = runner.invoke(app, ['config', '--edit'])

        assert result.exit_code == 0
        assert 'Configuration updated' in result.output

    def test_config_edit_creates_file_if_missing(self, runner, config_service_patch):
        result = runner.invoke(app, ['config', '--edit'], env={'EDITOR': 'true'})

        assert result.exit_code == 0
        assert config_service_patch.exists()


class TestTuiCommand:
    """Tests for pb tui command."""

    def test_tui_launches_successfully(self, runner, monkeypatch):
        from unittest.mock import MagicMock

        mock_run_tui = MagicMock()
        monkeypatch.setattr('prompt_butler.tui.run_tui', mock_run_tui)

        result = runner.invoke(app, ['tui'])

        assert result.exit_code == 0
        mock_run_tui.assert_called_once()


class TestTagCommands:
    """Tests for pb tag commands."""

    def test_tag_list_empty(self, runner):
        result = runner.invoke(app, ['tag', 'list'])

        assert result.exit_code == 0
        assert 'No tags found' in result.output

    def test_tag_list_shows_tags_with_counts(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', tags=['web', 'api']))
        storage.create(Prompt(name='p2', system_prompt='sys', tags=['web', 'cli']))
        storage.create(Prompt(name='p3', system_prompt='sys', tags=['api']))

        result = runner.invoke(app, ['tag', 'list'])

        assert result.exit_code == 0
        assert 'web' in result.output
        assert 'api' in result.output
        assert 'cli' in result.output

    def test_tag_list_json_output(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', tags=['web', 'api']))
        storage.create(Prompt(name='p2', system_prompt='sys', tags=['web']))

        result = runner.invoke(app, ['tag', 'list', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'tags' in data
        tags_dict = {t['name']: t['count'] for t in data['tags']}
        assert tags_dict['web'] == 2
        assert tags_dict['api'] == 1

    def test_tag_rename_updates_prompts(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', tags=['old-tag', 'other']))
        storage.create(Prompt(name='p2', system_prompt='sys', tags=['old-tag']))

        result = runner.invoke(app, ['tag', 'rename', 'old-tag', 'new-tag'])

        assert result.exit_code == 0
        assert 'Renamed' in result.output
        assert '2 prompt(s)' in result.output

        p1 = storage.get('p1', '')
        assert 'new-tag' in p1.tags
        assert 'old-tag' not in p1.tags
        assert 'other' in p1.tags

    def test_tag_rename_json_output(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', tags=['old']))

        result = runner.invoke(app, ['tag', 'rename', 'old', 'new', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'renamed'
        assert data['old'] == 'old'
        assert data['new'] == 'new'
        assert data['updated_count'] == 1

    def test_tag_rename_not_found(self, runner):
        result = runner.invoke(app, ['tag', 'rename', 'nonexistent', 'new'])

        assert result.exit_code == 1

    def test_tag_rename_not_found_json(self, runner):
        result = runner.invoke(app, ['tag', 'rename', 'nonexistent', 'new', '--json'])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data['status'] == 'error'


class TestGroupCommands:
    """Tests for pb group commands."""

    def test_group_list_empty(self, runner):
        result = runner.invoke(app, ['group', 'list'])

        assert result.exit_code == 0
        assert 'No groups found' in result.output

    def test_group_list_shows_groups(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', group='web'))
        storage.create(Prompt(name='p2', system_prompt='sys', group='cli'))

        result = runner.invoke(app, ['group', 'list'])

        assert result.exit_code == 0
        assert 'web' in result.output
        assert 'cli' in result.output

    def test_group_list_json_output(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', group='web'))

        result = runner.invoke(app, ['group', 'list', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'groups' in data
        assert 'web' in data['groups']

    def test_group_list_includes_empty_with_all_flag(self, runner, storage):
        storage.create_group('empty-group')
        storage.create(Prompt(name='p1', system_prompt='sys', group='with-prompt'))

        result = runner.invoke(app, ['group', 'list', '--all', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert 'empty-group' in data['groups']
        assert 'with-prompt' in data['groups']

    def test_group_create_success(self, runner, storage):
        result = runner.invoke(app, ['group', 'create', 'new-group'])

        assert result.exit_code == 0
        assert "Created group 'new-group'" in result.output
        assert 'new-group' in storage.list_groups(include_empty=True)

    def test_group_create_json_output(self, runner):
        result = runner.invoke(app, ['group', 'create', 'new-group', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'created'
        assert data['group'] == 'new-group'

    def test_group_create_already_exists(self, runner, storage):
        storage.create_group('existing')

        result = runner.invoke(app, ['group', 'create', 'existing'])

        assert result.exit_code == 1

    def test_group_create_already_exists_json(self, runner, storage):
        storage.create_group('existing')

        result = runner.invoke(app, ['group', 'create', 'existing', '--json'])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data['status'] == 'error'

    def test_group_rename_moves_prompts(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', group='old-group'))
        storage.create(Prompt(name='p2', system_prompt='sys', group='old-group'))

        result = runner.invoke(app, ['group', 'rename', 'old-group', 'new-group'])

        assert result.exit_code == 0
        assert 'Renamed' in result.output
        assert '2 prompt(s)' in result.output

        groups = storage.list_groups()
        assert 'new-group' in groups
        assert 'old-group' not in groups

    def test_group_rename_json_output(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', group='old'))

        result = runner.invoke(app, ['group', 'rename', 'old', 'new', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'renamed'
        assert data['old'] == 'old'
        assert data['new'] == 'new'
        assert data['moved_count'] == 1

    def test_group_rename_not_found(self, runner):
        result = runner.invoke(app, ['group', 'rename', 'nonexistent', 'new'])

        assert result.exit_code == 1

    def test_group_rename_not_found_json(self, runner):
        result = runner.invoke(app, ['group', 'rename', 'nonexistent', 'new', '--json'])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data['status'] == 'error'

    def test_group_rename_target_exists_with_prompts(self, runner, storage):
        storage.create(Prompt(name='p1', system_prompt='sys', group='source'))
        storage.create(Prompt(name='p2', system_prompt='sys', group='target'))

        result = runner.invoke(app, ['group', 'rename', 'source', 'target'])

        assert result.exit_code == 1
