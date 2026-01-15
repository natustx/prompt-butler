"""Integration tests for CLI commands.

Tests use real filesystem operations with temporary directories.
"""

from __future__ import annotations

import json
from argparse import Namespace
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from prompt_butler.cli import (
    cmd_add,
    cmd_clone,
    cmd_config,
    cmd_copy,
    cmd_delete,
    cmd_group,
    cmd_group_create,
    cmd_group_list,
    cmd_group_rename,
    cmd_index,
    cmd_list,
    cmd_show,
    cmd_tag,
    cmd_tag_list,
    cmd_tag_rename,
    cmd_tui,
    fuzzy_match,
    main,
    prompt_to_dict,
)
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
        group='default',
    )


@pytest.fixture
def mock_storage(storage, monkeypatch):
    """Patch get_storage to return a test storage instance."""
    monkeypatch.setattr('prompt_butler.cli.get_storage', lambda: storage)
    return storage


class TestFuzzyMatch:
    """Tests for fuzzy matching utility."""

    def test_exact_match(self):
        assert fuzzy_match('test', 'test') is True

    def test_substring_match(self):
        assert fuzzy_match('tst', 'test') is True

    def test_scattered_match(self):
        assert fuzzy_match('abc', 'aXbXc') is True

    def test_no_match(self):
        assert fuzzy_match('xyz', 'test') is False

    def test_case_insensitive(self):
        assert fuzzy_match('TEST', 'test') is True
        assert fuzzy_match('test', 'TEST') is True

    def test_empty_query_matches_all(self):
        assert fuzzy_match('', 'anything') is True


class TestPromptToDict:
    """Tests for prompt serialization."""

    def test_converts_all_fields(self, sample_prompt):
        result = prompt_to_dict(sample_prompt)

        assert result['name'] == 'test-prompt'
        assert result['description'] == 'A test prompt'
        assert result['system_prompt'] == 'You are a helpful assistant.'
        assert result['user_prompt'] == 'Help me with {task}.'
        assert result['tags'] == ['test', 'sample']
        assert result['group'] == 'default'


class TestCmdList:
    """Tests for pb list command."""

    def test_list_empty_returns_zero(self, mock_storage, capsys):
        args = Namespace(query=None, group=None, tag=None, json=False)
        result = cmd_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'No prompts found' in captured.out

    def test_list_shows_prompts_in_table(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(query=None, group=None, tag=None, json=False)
        result = cmd_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'test-prompt' in captured.out
        assert 'default' in captured.out

    def test_list_with_json_output(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(query=None, group=None, tag=None, json=True)
        result = cmd_list(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]['name'] == 'test-prompt'

    def test_list_filters_by_group(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='g1'))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', group='g2'))

        args = Namespace(query=None, group='g1', tag=None, json=True)
        result = cmd_list(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]['name'] == 'p1'

    def test_list_filters_by_tag(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', tags=['web']))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', tags=['cli']))

        args = Namespace(query=None, group=None, tag='web', json=True)
        result = cmd_list(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]['name'] == 'p1'

    def test_list_fuzzy_search(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='code-review', system_prompt='sys'))
        mock_storage.create(Prompt(name='summarize', system_prompt='sys'))

        args = Namespace(query='crv', group=None, tag=None, json=True)
        result = cmd_list(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]['name'] == 'code-review'


class TestCmdShow:
    """Tests for pb show command."""

    def test_show_displays_prompt(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(name='test-prompt', group='default', json=False)
        result = cmd_show(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'test-prompt' in captured.out
        assert 'You are a helpful assistant.' in captured.out

    def test_show_with_json_output(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(name='test-prompt', group='default', json=True)
        result = cmd_show(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['name'] == 'test-prompt'
        assert data['system_prompt'] == 'You are a helpful assistant.'

    def test_show_not_found(self, mock_storage, capsys):
        args = Namespace(name='nonexistent', group='default', json=False)
        result = cmd_show(args)

        assert result == 1

    def test_show_not_found_json(self, mock_storage, capsys):
        args = Namespace(name='nonexistent', group='default', json=True)
        result = cmd_show(args)

        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'error'


class TestCmdDelete:
    """Tests for pb delete command."""

    def test_delete_with_force_removes_prompt(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(name='test-prompt', group='default', force=True, json=False)
        result = cmd_delete(args)

        assert result == 0
        assert not mock_storage.exists('test-prompt', 'default')

    def test_delete_with_json_output(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(name='test-prompt', group='default', force=True, json=True)
        result = cmd_delete(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'deleted'

    def test_delete_not_found(self, mock_storage, capsys):
        args = Namespace(name='nonexistent', group='default', force=True, json=False)
        result = cmd_delete(args)

        assert result == 1

    def test_delete_confirmation_cancelled(self, mock_storage, sample_prompt, monkeypatch, capsys):
        mock_storage.create(sample_prompt)

        monkeypatch.setattr('builtins.input', lambda _: 'no')

        args = Namespace(name='test-prompt', group='default', force=False, json=False)
        result = cmd_delete(args)

        assert result == 0
        assert mock_storage.exists('test-prompt', 'default')
        captured = capsys.readouterr()
        assert 'Cancelled' in captured.out

    def test_delete_confirmation_accepted(self, mock_storage, sample_prompt, monkeypatch, capsys):
        mock_storage.create(sample_prompt)

        monkeypatch.setattr('builtins.input', lambda _: 'yes')

        args = Namespace(name='test-prompt', group='default', force=False, json=False)
        result = cmd_delete(args)

        assert result == 0
        assert not mock_storage.exists('test-prompt', 'default')


class TestCmdClone:
    """Tests for pb clone command."""

    def test_clone_creates_copy(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(name='test-prompt', newname='test-prompt-copy', group='default', target_group=None, json=False)
        result = cmd_clone(args)

        assert result == 0
        assert mock_storage.exists('test-prompt', 'default')
        assert mock_storage.exists('test-prompt-copy', 'default')

        cloned = mock_storage.get('test-prompt-copy', 'default')
        assert cloned.system_prompt == sample_prompt.system_prompt
        assert cloned.tags == sample_prompt.tags

    def test_clone_to_different_group(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(
            name='test-prompt', newname='test-prompt-copy', group='default', target_group='other', json=False
        )
        result = cmd_clone(args)

        assert result == 0
        assert mock_storage.exists('test-prompt-copy', 'other')

    def test_clone_with_json_output(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(name='test-prompt', newname='test-clone', group='default', target_group=None, json=True)
        result = cmd_clone(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'cloned'
        assert data['source'] == 'test-prompt'
        assert data['target'] == 'test-clone'

    def test_clone_source_not_found(self, mock_storage, capsys):
        args = Namespace(name='nonexistent', newname='new', group='default', target_group=None, json=False)
        result = cmd_clone(args)

        assert result == 1

    def test_clone_target_exists(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)
        mock_storage.create(Prompt(name='existing', system_prompt='sys', group='default'))

        args = Namespace(name='test-prompt', newname='existing', group='default', target_group=None, json=False)
        result = cmd_clone(args)

        assert result == 1


class TestCmdCopy:
    """Tests for pb copy command."""

    def test_copy_system_prompt(self, mock_storage, sample_prompt):
        mock_storage.create(sample_prompt)

        with patch.dict('sys.modules', {'pyperclip': MagicMock()}):
            import sys

            mock_pyperclip = sys.modules['pyperclip']
            args = Namespace(name='test-prompt', group='default', user=False, json=False)
            result = cmd_copy(args)

            assert result == 0
            mock_pyperclip.copy.assert_called_once_with('You are a helpful assistant.')

    def test_copy_user_prompt(self, mock_storage, sample_prompt):
        mock_storage.create(sample_prompt)

        with patch.dict('sys.modules', {'pyperclip': MagicMock()}):
            import sys

            mock_pyperclip = sys.modules['pyperclip']
            args = Namespace(name='test-prompt', group='default', user=True, json=False)
            result = cmd_copy(args)

            assert result == 0
            mock_pyperclip.copy.assert_called_once_with('Help me with {task}.')

    def test_copy_with_json_output(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        with patch.dict('sys.modules', {'pyperclip': MagicMock()}):
            args = Namespace(name='test-prompt', group='default', user=False, json=True)
            result = cmd_copy(args)

            assert result == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'copied'

    def test_copy_not_found(self, mock_storage, capsys):
        args = Namespace(name='nonexistent', group='default', user=False, json=False)
        result = cmd_copy(args)

        assert result == 1

    def test_copy_empty_user_prompt(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='no-user', system_prompt='sys', user_prompt='', group='default'))

        args = Namespace(name='no-user', group='default', user=True, json=False)
        result = cmd_copy(args)

        assert result == 1


class TestCmdAdd:
    """Tests for pb add command."""

    def test_add_with_stdin(self, mock_storage, monkeypatch, capsys):
        monkeypatch.setattr('sys.stdin', StringIO('System prompt content'))

        args = Namespace(name='new-prompt', group='default', edit=False, json=False)
        result = cmd_add(args)

        assert result == 0
        assert mock_storage.exists('new-prompt', 'default')

        prompt = mock_storage.get('new-prompt', 'default')
        assert prompt.system_prompt == 'System prompt content'

    def test_add_with_json_output(self, mock_storage, monkeypatch, capsys):
        monkeypatch.setattr('sys.stdin', StringIO('System prompt'))

        args = Namespace(name='json-prompt', group='default', edit=False, json=True)
        result = cmd_add(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'created'
        assert data['prompt']['name'] == 'json-prompt'

    def test_add_duplicate_fails(self, mock_storage, monkeypatch, capsys):
        mock_storage.create(Prompt(name='existing', system_prompt='sys', group='default'))
        monkeypatch.setattr('sys.stdin', StringIO('New content'))

        args = Namespace(name='existing', group='default', edit=False, json=False)
        result = cmd_add(args)

        assert result == 1

    def test_add_empty_prompt_fails(self, mock_storage, monkeypatch, capsys):
        monkeypatch.setattr('sys.stdin', StringIO(''))

        args = Namespace(name='empty', group='default', edit=False, json=False)
        result = cmd_add(args)

        assert result == 1


class TestMainEntryPoint:
    """Tests for main CLI entry point."""

    def test_no_command_shows_help(self, capsys):
        with patch('sys.argv', ['pb']):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert 'Prompt Butler' in captured.out or 'usage' in captured.out.lower()

    def test_list_command_routes_correctly(self, mock_storage, capsys):
        with patch('sys.argv', ['pb', 'list', '--json']):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)

    def test_show_command_routes_correctly(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        with patch('sys.argv', ['pb', 'show', 'test-prompt', '--json']):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['name'] == 'test-prompt'


class TestCmdIndex:
    """Tests for pb index command."""

    def test_index_empty_storage(self, mock_storage, capsys):
        args = Namespace(json=False)
        result = cmd_index(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'Indexed 0 prompt(s)' in captured.out

    def test_index_with_prompts(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)
        mock_storage.create(Prompt(name='second', system_prompt='sys', group='other'))

        args = Namespace(json=False)
        result = cmd_index(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'Indexed 2 prompt(s)' in captured.out
        assert '2 group(s)' in captured.out

    def test_index_with_json_output(self, mock_storage, sample_prompt, capsys):
        mock_storage.create(sample_prompt)

        args = Namespace(json=True)
        result = cmd_index(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'indexed'
        assert data['prompts_count'] == 1
        assert data['groups_count'] == 1
        assert 'default' in data['groups']


class TestCmdConfig:
    """Tests for pb config command."""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file path."""
        return tmp_path / 'config.yaml'

    @pytest.fixture
    def mock_config_service(self, config_file, monkeypatch):
        """Patch ConfigService to use temporary config file."""
        from prompt_butler.services.config import ConfigService

        service = ConfigService(config_path=config_file)

        def mock_init(self, config_path=None):
            self.config_path = config_file
            self._config = None

        monkeypatch.setattr(ConfigService, '__init__', mock_init)
        return service

    def test_config_shows_all_values(self, mock_config_service, capsys):
        args = Namespace(key=None, value=None, edit=False, json=False)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'prompts_dir:' in captured.out
        assert 'default_group:' in captured.out

    def test_config_with_json_output(self, mock_config_service, capsys):
        args = Namespace(key=None, value=None, edit=False, json=True)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'prompts_dir' in data
        assert 'default_group' in data
        assert 'config_file' in data

    def test_config_get_specific_key(self, mock_config_service, capsys):
        args = Namespace(key='prompts_dir', value=None, edit=False, json=False)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'prompts_dir' in captured.out

    def test_config_get_specific_key_json(self, mock_config_service, capsys):
        args = Namespace(key='prompts_dir', value=None, edit=False, json=True)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['key'] == 'prompts_dir'

    def test_config_set_value(self, mock_config_service, capsys):
        args = Namespace(key='prompts_dir', value='/new/path', edit=False, json=False)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'Set prompts_dir' in captured.out

    def test_config_set_value_json(self, mock_config_service, capsys):
        args = Namespace(key='prompts_dir', value='/new/path', edit=False, json=True)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'updated'
        assert data['key'] == 'prompts_dir'
        assert data['value'] == '/new/path'

    def test_config_unknown_key_fails(self, mock_config_service, capsys):
        args = Namespace(key='nonexistent', value=None, edit=False, json=False)
        result = cmd_config(args)

        assert result == 1

    def test_config_set_unknown_key_fails(self, mock_config_service, capsys):
        args = Namespace(key='nonexistent', value='val', edit=False, json=False)
        result = cmd_config(args)

        assert result == 1

    def test_config_edit_opens_editor(self, mock_config_service, monkeypatch, capsys):
        monkeypatch.setenv('EDITOR', 'true')

        args = Namespace(key=None, value=None, edit=True, json=False)
        result = cmd_config(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'Configuration updated' in captured.out

    def test_config_edit_creates_file_if_missing(self, mock_config_service, config_file, monkeypatch, capsys):
        monkeypatch.setenv('EDITOR', 'true')
        assert not config_file.exists()

        args = Namespace(key=None, value=None, edit=True, json=False)
        result = cmd_config(args)

        assert result == 0
        assert config_file.exists()


class TestCmdTui:
    """Tests for pb tui command."""

    def test_tui_not_implemented(self, capsys):
        args = Namespace()
        result = cmd_tui(args)

        assert result == 1
        captured = capsys.readouterr()
        assert 'not yet implemented' in captured.err.lower()


class TestCmdTagList:
    """Tests for pb tag list command."""

    def test_tag_list_empty(self, mock_storage, capsys):
        args = Namespace(json=False)
        result = cmd_tag_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'No tags found' in captured.out

    def test_tag_list_shows_tags_with_counts(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', tags=['web', 'api']))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', tags=['web', 'cli']))
        mock_storage.create(Prompt(name='p3', system_prompt='sys', tags=['api']))

        args = Namespace(json=False)
        result = cmd_tag_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'web' in captured.out
        assert 'api' in captured.out
        assert 'cli' in captured.out

    def test_tag_list_json_output(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', tags=['web', 'api']))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', tags=['web']))

        args = Namespace(json=True)
        result = cmd_tag_list(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'tags' in data
        tags_dict = {t['name']: t['count'] for t in data['tags']}
        assert tags_dict['web'] == 2
        assert tags_dict['api'] == 1


class TestCmdTagRename:
    """Tests for pb tag rename command."""

    def test_tag_rename_updates_prompts(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', tags=['old-tag', 'other']))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', tags=['old-tag']))

        args = Namespace(old='old-tag', new='new-tag', json=False)
        result = cmd_tag_rename(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'Renamed' in captured.out
        assert '2 prompt(s)' in captured.out

        p1 = mock_storage.get('p1', 'default')
        assert 'new-tag' in p1.tags
        assert 'old-tag' not in p1.tags
        assert 'other' in p1.tags

    def test_tag_rename_json_output(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', tags=['old']))

        args = Namespace(old='old', new='new', json=True)
        result = cmd_tag_rename(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'renamed'
        assert data['old'] == 'old'
        assert data['new'] == 'new'
        assert data['updated_count'] == 1

    def test_tag_rename_not_found(self, mock_storage, capsys):
        args = Namespace(old='nonexistent', new='new', json=False)
        result = cmd_tag_rename(args)

        assert result == 1

    def test_tag_rename_not_found_json(self, mock_storage, capsys):
        args = Namespace(old='nonexistent', new='new', json=True)
        result = cmd_tag_rename(args)

        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'error'


class TestCmdTag:
    """Tests for pb tag command router."""

    def test_tag_routes_to_list(self, mock_storage, capsys):
        args = Namespace(tag_command='list', json=False)
        result = cmd_tag(args)

        assert result == 0

    def test_tag_routes_to_rename(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', tags=['old']))

        args = Namespace(tag_command='rename', old='old', new='new', json=False)
        result = cmd_tag(args)

        assert result == 0

    def test_tag_unknown_command(self, capsys):
        args = Namespace(tag_command='unknown')
        result = cmd_tag(args)

        assert result == 1


class TestCmdGroupList:
    """Tests for pb group list command."""

    def test_group_list_empty(self, mock_storage, capsys):
        args = Namespace(all=False, json=False)
        result = cmd_group_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'No groups found' in captured.out

    def test_group_list_shows_groups(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='web'))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', group='cli'))

        args = Namespace(all=False, json=False)
        result = cmd_group_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'web' in captured.out
        assert 'cli' in captured.out

    def test_group_list_json_output(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='web'))

        args = Namespace(all=False, json=True)
        result = cmd_group_list(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'groups' in data
        assert 'web' in data['groups']

    def test_group_list_includes_empty_with_all_flag(self, mock_storage, capsys):
        mock_storage.create_group('empty-group')
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='with-prompt'))

        args = Namespace(all=True, json=True)
        result = cmd_group_list(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert 'empty-group' in data['groups']
        assert 'with-prompt' in data['groups']


class TestCmdGroupCreate:
    """Tests for pb group create command."""

    def test_group_create_success(self, mock_storage, capsys):
        args = Namespace(name='new-group', json=False)
        result = cmd_group_create(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Created group 'new-group'" in captured.out
        assert 'new-group' in mock_storage.list_groups(include_empty=True)

    def test_group_create_json_output(self, mock_storage, capsys):
        args = Namespace(name='new-group', json=True)
        result = cmd_group_create(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'created'
        assert data['group'] == 'new-group'

    def test_group_create_already_exists(self, mock_storage, capsys):
        mock_storage.create_group('existing')

        args = Namespace(name='existing', json=False)
        result = cmd_group_create(args)

        assert result == 1

    def test_group_create_already_exists_json(self, mock_storage, capsys):
        mock_storage.create_group('existing')

        args = Namespace(name='existing', json=True)
        result = cmd_group_create(args)

        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'error'


class TestCmdGroupRename:
    """Tests for pb group rename command."""

    def test_group_rename_moves_prompts(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='old-group'))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', group='old-group'))

        args = Namespace(old='old-group', new='new-group', json=False)
        result = cmd_group_rename(args)

        assert result == 0
        captured = capsys.readouterr()
        assert 'Renamed' in captured.out
        assert '2 prompt(s)' in captured.out

        groups = mock_storage.list_groups()
        assert 'new-group' in groups
        assert 'old-group' not in groups

    def test_group_rename_json_output(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='old'))

        args = Namespace(old='old', new='new', json=True)
        result = cmd_group_rename(args)

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'renamed'
        assert data['old'] == 'old'
        assert data['new'] == 'new'
        assert data['moved_count'] == 1

    def test_group_rename_not_found(self, mock_storage, capsys):
        args = Namespace(old='nonexistent', new='new', json=False)
        result = cmd_group_rename(args)

        assert result == 1

    def test_group_rename_not_found_json(self, mock_storage, capsys):
        args = Namespace(old='nonexistent', new='new', json=True)
        result = cmd_group_rename(args)

        assert result == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'error'

    def test_group_rename_target_exists_with_prompts(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='source'))
        mock_storage.create(Prompt(name='p2', system_prompt='sys', group='target'))

        args = Namespace(old='source', new='target', json=False)
        result = cmd_group_rename(args)

        assert result == 1


class TestCmdGroup:
    """Tests for pb group command router."""

    def test_group_routes_to_list(self, mock_storage, capsys):
        args = Namespace(group_command='list', all=False, json=False)
        result = cmd_group(args)

        assert result == 0

    def test_group_routes_to_create(self, mock_storage, capsys):
        args = Namespace(group_command='create', name='new', json=False)
        result = cmd_group(args)

        assert result == 0

    def test_group_routes_to_rename(self, mock_storage, capsys):
        mock_storage.create(Prompt(name='p1', system_prompt='sys', group='old'))

        args = Namespace(group_command='rename', old='old', new='new', json=False)
        result = cmd_group(args)

        assert result == 0

    def test_group_unknown_command(self, capsys):
        args = Namespace(group_command='unknown')
        result = cmd_group(args)

        assert result == 1
