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
    cmd_copy,
    cmd_delete,
    cmd_list,
    cmd_show,
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
