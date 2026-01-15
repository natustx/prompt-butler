"""Integration tests for PromptStorage service.

Tests use real filesystem operations with temporary directories.
"""

import pytest

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptExistsError, PromptStorage


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
        user_prompt='Please help me with {task}.',
        tags=['test', 'sample'],
        group='default',
    )


class TestPromptStorageCreate:
    """Tests for creating prompts."""

    def test_create_stores_prompt_as_markdown_file(self, storage, sample_prompt, tmp_path):
        storage.create(sample_prompt)

        file_path = tmp_path / 'default' / 'test-prompt.md'
        assert file_path.exists()

        content = file_path.read_text()
        assert 'name: test-prompt' in content
        assert 'description: A test prompt' in content
        assert 'You are a helpful assistant.' in content
        assert '---user---' in content
        assert 'Please help me with {task}.' in content

    def test_create_returns_created_prompt(self, storage, sample_prompt):
        result = storage.create(sample_prompt)

        assert result.name == sample_prompt.name
        assert result.description == sample_prompt.description
        assert result.system_prompt == sample_prompt.system_prompt
        assert result.user_prompt == sample_prompt.user_prompt
        assert result.tags == sample_prompt.tags
        assert result.group == sample_prompt.group

    def test_create_raises_error_for_duplicate(self, storage, sample_prompt):
        storage.create(sample_prompt)

        with pytest.raises(PromptExistsError) as exc_info:
            storage.create(sample_prompt)

        assert 'already exists' in str(exc_info.value)

    def test_create_in_custom_group(self, storage, tmp_path):
        prompt = Prompt(
            name='custom-prompt',
            system_prompt='System content',
            group='my-group',
        )

        storage.create(prompt)

        file_path = tmp_path / 'my-group' / 'custom-prompt.md'
        assert file_path.exists()

    def test_create_without_user_prompt(self, storage, tmp_path):
        prompt = Prompt(
            name='system-only',
            system_prompt='System content only',
            group='default',
        )

        storage.create(prompt)

        file_path = tmp_path / 'default' / 'system-only.md'
        content = file_path.read_text()
        assert '---user---' not in content
        assert 'System content only' in content


class TestPromptStorageGet:
    """Tests for retrieving prompts."""

    def test_get_returns_prompt_by_name_and_group(self, storage, sample_prompt):
        storage.create(sample_prompt)

        result = storage.get('test-prompt', group='default')

        assert result is not None
        assert result.name == 'test-prompt'
        assert result.system_prompt == 'You are a helpful assistant.'
        assert result.user_prompt == 'Please help me with {task}.'

    def test_get_returns_none_for_nonexistent(self, storage):
        result = storage.get('nonexistent', group='default')
        assert result is None

    def test_get_returns_none_for_wrong_group(self, storage, sample_prompt):
        storage.create(sample_prompt)

        result = storage.get('test-prompt', group='other-group')
        assert result is None


class TestPromptStorageList:
    """Tests for listing prompts."""

    def test_list_returns_all_prompts(self, storage):
        prompts = [
            Prompt(name='prompt-a', system_prompt='A', group='group1'),
            Prompt(name='prompt-b', system_prompt='B', group='group1'),
            Prompt(name='prompt-c', system_prompt='C', group='group2'),
        ]
        for p in prompts:
            storage.create(p)

        result = storage.list()

        assert len(result) == 3
        names = [p.name for p in result]
        assert 'prompt-a' in names
        assert 'prompt-b' in names
        assert 'prompt-c' in names

    def test_list_filters_by_group(self, storage):
        prompts = [
            Prompt(name='prompt-a', system_prompt='A', group='group1'),
            Prompt(name='prompt-b', system_prompt='B', group='group2'),
        ]
        for p in prompts:
            storage.create(p)

        result = storage.list(group='group1')

        assert len(result) == 1
        assert result[0].name == 'prompt-a'

    def test_list_returns_empty_for_empty_storage(self, storage):
        result = storage.list()
        assert result == []

    def test_list_sorts_by_group_then_name(self, storage):
        prompts = [
            Prompt(name='zebra', system_prompt='Z', group='beta'),
            Prompt(name='apple', system_prompt='A', group='alpha'),
            Prompt(name='banana', system_prompt='B', group='alpha'),
        ]
        for p in prompts:
            storage.create(p)

        result = storage.list()

        assert result[0].group == 'alpha'
        assert result[0].name == 'apple'
        assert result[1].group == 'alpha'
        assert result[1].name == 'banana'
        assert result[2].group == 'beta'
        assert result[2].name == 'zebra'


class TestPromptStorageUpdate:
    """Tests for updating prompts."""

    def test_update_modifies_prompt_fields(self, storage, sample_prompt):
        storage.create(sample_prompt)

        result = storage.update(
            'test-prompt',
            'default',
            description='Updated description',
            system_prompt='Updated system prompt',
        )

        assert result is not None
        assert result.description == 'Updated description'
        assert result.system_prompt == 'Updated system prompt'
        assert result.user_prompt == sample_prompt.user_prompt

    def test_update_returns_none_for_nonexistent(self, storage):
        result = storage.update('nonexistent', 'default', description='New')
        assert result is None

    def test_update_persists_changes(self, storage, sample_prompt):
        storage.create(sample_prompt)
        storage.update('test-prompt', 'default', description='Persisted')

        retrieved = storage.get('test-prompt', 'default')
        assert retrieved.description == 'Persisted'


class TestPromptStorageDelete:
    """Tests for deleting prompts."""

    def test_delete_removes_prompt_file(self, storage, sample_prompt, tmp_path):
        storage.create(sample_prompt)
        file_path = tmp_path / 'default' / 'test-prompt.md'
        assert file_path.exists()

        result = storage.delete('test-prompt', 'default')

        assert result is True
        assert not file_path.exists()

    def test_delete_returns_false_for_nonexistent(self, storage):
        result = storage.delete('nonexistent', 'default')
        assert result is False

    def test_delete_removes_empty_group_directory(self, storage, sample_prompt, tmp_path):
        storage.create(sample_prompt)
        group_dir = tmp_path / 'default'
        assert group_dir.exists()

        storage.delete('test-prompt', 'default')

        assert not group_dir.exists()

    def test_delete_preserves_group_with_other_prompts(self, storage, tmp_path):
        prompts = [
            Prompt(name='keep', system_prompt='Keep', group='group'),
            Prompt(name='delete', system_prompt='Delete', group='group'),
        ]
        for p in prompts:
            storage.create(p)

        storage.delete('delete', 'group')

        group_dir = tmp_path / 'group'
        assert group_dir.exists()
        assert (group_dir / 'keep.md').exists()


class TestPromptStorageExists:
    """Tests for checking prompt existence."""

    def test_exists_returns_true_for_existing(self, storage, sample_prompt):
        storage.create(sample_prompt)
        assert storage.exists('test-prompt', 'default') is True

    def test_exists_returns_false_for_nonexistent(self, storage):
        assert storage.exists('nonexistent', 'default') is False


class TestPromptStorageListGroups:
    """Tests for listing groups."""

    def test_list_groups_returns_all_groups(self, storage):
        prompts = [
            Prompt(name='a', system_prompt='A', group='alpha'),
            Prompt(name='b', system_prompt='B', group='beta'),
            Prompt(name='c', system_prompt='C', group='gamma'),
        ]
        for p in prompts:
            storage.create(p)

        groups = storage.list_groups()

        assert sorted(groups) == ['alpha', 'beta', 'gamma']

    def test_list_groups_returns_empty_for_no_prompts(self, storage):
        groups = storage.list_groups()
        assert groups == []


class TestPromptStorageSlugify:
    """Tests for name slugification."""

    def test_slugify_lowercases(self):
        assert PromptStorage.slugify('MyPrompt') == 'myprompt'

    def test_slugify_replaces_spaces_with_hyphens(self):
        assert PromptStorage.slugify('my prompt') == 'my-prompt'

    def test_slugify_removes_special_characters(self):
        assert PromptStorage.slugify('my@prompt!') == 'myprompt'

    def test_slugify_handles_multiple_hyphens(self):
        assert PromptStorage.slugify('my--prompt') == 'my-prompt'


class TestMarkdownFormat:
    """Tests for markdown file format with YAML frontmatter."""

    def test_file_has_yaml_frontmatter(self, storage, tmp_path):
        prompt = Prompt(
            name='format-test',
            description='Test description',
            tags=['tag1', 'tag2'],
            system_prompt='System content',
            group='default',
        )
        storage.create(prompt)

        content = (tmp_path / 'default' / 'format-test.md').read_text()

        assert content.startswith('---\n')
        assert '\n---\n' in content
        assert 'name: format-test' in content
        assert 'description: Test description' in content
        assert 'tag1' in content
        assert 'tag2' in content

    def test_user_separator_placed_correctly(self, storage, tmp_path):
        prompt = Prompt(
            name='separator-test',
            system_prompt='System part',
            user_prompt='User part',
            group='default',
        )
        storage.create(prompt)

        content = (tmp_path / 'default' / 'separator-test.md').read_text()

        lines = content.split('\n')
        frontmatter_end = False
        system_found = False
        separator_found = False
        user_found = False

        for line in lines:
            if line == '---' and not frontmatter_end:
                frontmatter_end = True
                continue
            if frontmatter_end and 'System part' in line:
                system_found = True
            if frontmatter_end and '---user---' in line:
                separator_found = True
            if separator_found and 'User part' in line:
                user_found = True

        assert system_found, 'System prompt not found after frontmatter'
        assert separator_found, '---user--- separator not found'
        assert user_found, 'User prompt not found after separator'
