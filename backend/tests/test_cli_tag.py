import json

import pytest
from typer.testing import CliRunner

from prompt_butler.cli import app
from prompt_butler.models import Prompt


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def storage_with_tagged_prompts(tmp_path, monkeypatch):
    """Create storage with prompts having various tags."""
    from prompt_butler.services.storage import PromptStorage

    test_storage = PromptStorage(prompts_dir=tmp_path)

    test_storage.create(Prompt(
        name='prompt1',
        description='First prompt',
        system_prompt='System 1',
        tags=['python', 'coding'],
    ))
    test_storage.create(Prompt(
        name='prompt2',
        description='Second prompt',
        system_prompt='System 2',
        tags=['python', 'testing'],
    ))
    test_storage.create(Prompt(
        name='prompt3',
        description='Third prompt',
        system_prompt='System 3',
        tags=['javascript'],
    ))

    import prompt_butler.cli as cli
    monkeypatch.setattr(cli, 'PromptStorage', lambda: test_storage)

    return test_storage


class TestTagList:
    def test_tag_list_shows_all_tags(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['tag', 'list'])

        assert result.exit_code == 0
        assert 'python' in result.output
        assert 'coding' in result.output
        assert 'testing' in result.output
        assert 'javascript' in result.output

    def test_tag_list_shows_counts(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['--json', 'tag', 'list'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['python'] == 2
        assert data['coding'] == 1
        assert data['testing'] == 1
        assert data['javascript'] == 1

    def test_tag_list_empty(self, runner, tmp_path, monkeypatch):
        from prompt_butler.services.storage import PromptStorage

        empty_storage = PromptStorage(prompts_dir=tmp_path)
        # Create prompt without tags
        empty_storage.create(Prompt(
            name='no-tags',
            system_prompt='System',
            tags=[],
        ))

        import prompt_butler.cli as cli
        monkeypatch.setattr(cli, 'PromptStorage', lambda: empty_storage)

        result = runner.invoke(app, ['tag', 'list'])

        assert result.exit_code == 0
        assert 'No tags found' in result.output

    def test_tag_list_json_output(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['--json', 'tag', 'list'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['python'] == 2
        assert data['coding'] == 1
        assert data['testing'] == 1
        assert data['javascript'] == 1


class TestTagRename:
    def test_tag_rename_updates_prompts(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['tag', 'rename', 'python', 'py'])

        assert result.exit_code == 0
        assert 'Renamed tag' in result.output
        assert 'python' in result.output
        assert 'py' in result.output
        assert '2 prompt(s) updated' in result.output

        # Verify prompts were updated
        prompt1 = storage_with_tagged_prompts.read('prompt1')
        prompt2 = storage_with_tagged_prompts.read('prompt2')
        assert 'py' in prompt1.tags
        assert 'python' not in prompt1.tags
        assert 'py' in prompt2.tags
        assert 'python' not in prompt2.tags

    def test_tag_rename_not_found(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['tag', 'rename', 'nonexistent', 'new'])

        assert result.exit_code == 1
        assert 'No prompts found with tag' in result.output

    def test_tag_rename_preserves_other_tags(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['tag', 'rename', 'python', 'py'])

        assert result.exit_code == 0

        # Verify other tags are preserved
        prompt1 = storage_with_tagged_prompts.read('prompt1')
        assert 'coding' in prompt1.tags  # Original tag preserved
        assert 'py' in prompt1.tags  # New tag added

    def test_tag_rename_json_output(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['--json', 'tag', 'rename', 'python', 'py'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['renamed'] is True
        assert data['old_tag'] == 'python'
        assert data['new_tag'] == 'py'
        assert data['prompts_updated'] == 2

    def test_tag_rename_single_prompt(self, runner, storage_with_tagged_prompts):
        result = runner.invoke(app, ['tag', 'rename', 'javascript', 'js'])

        assert result.exit_code == 0
        assert '1 prompt(s) updated' in result.output

        prompt3 = storage_with_tagged_prompts.read('prompt3')
        assert 'js' in prompt3.tags
        assert 'javascript' not in prompt3.tags


class TestLegacyTagsCommand:
    def test_legacy_tags_command_still_works(self, runner, storage_with_tagged_prompts):
        # The hidden 'tags' command should still work for backward compatibility
        result = runner.invoke(app, ['tags'])

        assert result.exit_code == 0
        assert 'python' in result.output
