import logging

import pytest

from prompt_butler.models import Prompt
from prompt_butler.services.storage import PromptExistsError, PromptNotFoundError, PromptStorage


class TestPromptStorageSlugify:
    def test_slugify_simple_name(self):
        assert PromptStorage.slugify('code-review') == 'code-review'

    def test_slugify_with_spaces(self):
        assert PromptStorage.slugify('code review') == 'code-review'

    def test_slugify_with_special_chars(self):
        assert PromptStorage.slugify('code@review!') == 'codereview'

    def test_slugify_uppercase(self):
        assert PromptStorage.slugify('Code-Review') == 'code-review'

    def test_slugify_multiple_spaces(self):
        assert PromptStorage.slugify('code   review') == 'code-review'


class TestPromptStorageParseContent:
    def test_parse_content_without_user_section(self):
        storage = PromptStorage.__new__(PromptStorage)
        content = 'You are a helpful assistant.'
        system, user = storage._parse_content(content)
        assert system == 'You are a helpful assistant.'
        assert user == ''

    def test_parse_content_with_user_section(self):
        storage = PromptStorage.__new__(PromptStorage)
        content = 'You are a helpful assistant.\n\n---user---\n\nPlease help me with {task}'
        system, user = storage._parse_content(content)
        assert system == 'You are a helpful assistant.'
        assert user == 'Please help me with {task}'

    def test_parse_content_strips_whitespace(self):
        storage = PromptStorage.__new__(PromptStorage)
        content = '  System prompt  \n\n---user---\n\n  User prompt  '
        system, user = storage._parse_content(content)
        assert system == 'System prompt'
        assert user == 'User prompt'


class TestPromptStorageFormatContent:
    def test_format_content_without_user_prompt(self):
        storage = PromptStorage.__new__(PromptStorage)
        content = storage._format_content('System prompt')
        assert content == 'System prompt'

    def test_format_content_with_user_prompt(self):
        storage = PromptStorage.__new__(PromptStorage)
        content = storage._format_content('System prompt', 'User prompt')
        assert content == 'System prompt\n\n---user---\n\nUser prompt'

    def test_format_content_empty_user_prompt(self):
        storage = PromptStorage.__new__(PromptStorage)
        content = storage._format_content('System prompt', '')
        assert content == 'System prompt'


class TestPromptStorageCreate:
    def test_create_prompt_in_root(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        prompt = Prompt(
            name='test-prompt',
            description='Test description',
            system_prompt='You are helpful.',
            tags=['test'],
        )

        result = storage.create(prompt)

        assert result.name == 'test-prompt'
        assert (tmp_path / 'test-prompt.md').exists()

    def test_create_prompt_in_group(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        prompt = Prompt(
            name='test-prompt',
            description='Test description',
            system_prompt='You are helpful.',
            group='coding',
            tags=['test'],
        )

        result = storage.create(prompt)

        assert result.name == 'test-prompt'
        assert (tmp_path / 'coding' / 'test-prompt.md').exists()

    def test_create_prompt_with_user_prompt(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        prompt = Prompt(
            name='test-prompt',
            system_prompt='System content',
            user_prompt='User content',
        )

        storage.create(prompt)

        # Read the file and verify format
        content = (tmp_path / 'test-prompt.md').read_text()
        assert '---user---' in content
        assert 'System content' in content
        assert 'User content' in content

    def test_create_duplicate_raises_error(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        prompt = Prompt(name='test', system_prompt='Test')

        storage.create(prompt)

        with pytest.raises(PromptExistsError):
            storage.create(prompt)

    def test_create_existing_file_raises_error(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        (tmp_path / 'test.md').write_text('preexisting')
        prompt = Prompt(name='test', system_prompt='Test')

        with pytest.raises(PromptExistsError):
            storage.create(prompt)


class TestPromptStorageRead:
    def test_read_existing_prompt(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        original = Prompt(
            name='test-prompt',
            description='Test description',
            system_prompt='System content',
            user_prompt='User content',
            tags=['tag1', 'tag2'],
        )
        storage.create(original)

        result = storage.read('test-prompt')

        assert result is not None
        assert result.name == 'test-prompt'
        assert result.description == 'Test description'
        assert result.system_prompt == 'System content'
        assert result.user_prompt == 'User content'
        assert result.tags == ['tag1', 'tag2']

    def test_read_nonexistent_prompt(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)

        result = storage.read('nonexistent')

        assert result is None

    def test_read_prompt_in_group(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        original = Prompt(
            name='test-prompt',
            system_prompt='System content',
            group='coding',
        )
        storage.create(original)

        result = storage.read('test-prompt', group='coding')

        assert result is not None
        assert result.group == 'coding'

    def test_read_finds_prompt_across_groups(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        original = Prompt(
            name='test-prompt',
            system_prompt='System content',
            group='coding',
        )
        storage.create(original)

        # Read without specifying group
        result = storage.read('test-prompt')

        assert result is not None
        assert result.group == 'coding'


class TestPromptStorageUpdate:
    def test_update_existing_prompt(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        original = Prompt(name='test', system_prompt='Original')
        storage.create(original)

        updated = Prompt(name='test', system_prompt='Updated')
        result = storage.update('test', updated)

        assert result.system_prompt == 'Updated'

        # Verify file content
        read_back = storage.read('test')
        assert read_back.system_prompt == 'Updated'

    def test_update_nonexistent_raises_error(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        prompt = Prompt(name='nonexistent', system_prompt='Test')

        with pytest.raises(PromptNotFoundError):
            storage.update('nonexistent', prompt)

    def test_update_moves_to_new_group(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        original = Prompt(name='test', system_prompt='Content', group='')
        storage.create(original)

        updated = Prompt(name='test', system_prompt='Content', group='coding')
        storage.update('test', updated)

        # Old file should be gone
        assert not (tmp_path / 'test.md').exists()
        # New file should exist
        assert (tmp_path / 'coding' / 'test.md').exists()

    def test_update_renames_prompt(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        original = Prompt(name='old-name', system_prompt='Content')
        storage.create(original)

        updated = Prompt(name='new-name', system_prompt='Content')
        storage.update('old-name', updated)

        # Old file should be gone
        assert not (tmp_path / 'old-name.md').exists()
        # New file should exist
        assert (tmp_path / 'new-name.md').exists()


class TestPromptStorageDelete:
    def test_delete_existing_prompt(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        prompt = Prompt(name='test', system_prompt='Content')
        storage.create(prompt)

        result = storage.delete('test')

        assert result is True
        assert not (tmp_path / 'test.md').exists()

    def test_delete_nonexistent_returns_false(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)

        result = storage.delete('nonexistent')

        assert result is False

    def test_delete_prompt_in_group(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        prompt = Prompt(name='test', system_prompt='Content', group='coding')
        storage.create(prompt)

        result = storage.delete('test', group='coding')

        assert result is True
        assert not (tmp_path / 'coding' / 'test.md').exists()


class TestPromptStorageListAll:
    def test_list_empty_directory(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)

        result = storage.list_all()

        assert result == []

    def test_list_all_prompts(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='prompt1', system_prompt='Content 1'))
        storage.create(Prompt(name='prompt2', system_prompt='Content 2'))

        result = storage.list_all()

        assert len(result) == 2
        names = [p.name for p in result]
        assert 'prompt1' in names
        assert 'prompt2' in names

    def test_list_filter_by_tag(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='prompt1', system_prompt='Content', tags=['coding']))
        storage.create(Prompt(name='prompt2', system_prompt='Content', tags=['writing']))

        result = storage.list_all(tag='coding')

        assert len(result) == 1
        assert result[0].name == 'prompt1'

    def test_list_filter_by_group(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='prompt1', system_prompt='Content', group='coding'))
        storage.create(Prompt(name='prompt2', system_prompt='Content', group=''))

        result = storage.list_all(group='coding')

        assert len(result) == 1
        assert result[0].name == 'prompt1'

    def test_list_filter_by_empty_group(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='prompt1', system_prompt='Content', group='coding'))
        storage.create(Prompt(name='prompt2', system_prompt='Content', group=''))

        result = storage.list_all(group='')

        assert len(result) == 1
        assert result[0].name == 'prompt2'

    def test_list_sorted_by_group_then_name(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='zebra', system_prompt='Content', group=''))
        storage.create(Prompt(name='apple', system_prompt='Content', group='coding'))
        storage.create(Prompt(name='banana', system_prompt='Content', group=''))

        result = storage.list_all()

        # Empty group first, then 'coding'
        assert result[0].name == 'banana'
        assert result[1].name == 'zebra'
        assert result[2].name == 'apple'

    def test_list_logs_warning_on_unparseable_file(self, tmp_path, caplog):
        storage = PromptStorage(prompts_dir=tmp_path)
        (tmp_path / 'bad.md').write_text('---\nname: [\n---\ncontent')
        storage.create(Prompt(name='good', system_prompt='Content'))

        with caplog.at_level(logging.WARNING):
            result = storage.list_all()

        assert any('Failed to parse prompt file' in record.message for record in caplog.records)
        assert any(prompt.name == 'good' for prompt in result)


class TestPromptStorageSearch:
    def test_search_by_name(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='code-review', system_prompt='Content'))
        storage.create(Prompt(name='unit-test', system_prompt='Content'))

        result = storage.search('code')

        assert len(result) >= 1
        assert any(p.name == 'code-review' for p in result)

    def test_search_by_description(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='prompt1', description='Reviews Python code', system_prompt='Content'))
        storage.create(Prompt(name='prompt2', description='Writes documentation', system_prompt='Content'))

        result = storage.search('python')

        assert len(result) >= 1
        assert any(p.name == 'prompt1' for p in result)

    def test_search_fuzzy_match(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='code-review', system_prompt='Content'))

        # Typo: 'reveiw' instead of 'review'
        result = storage.search('reveiw')

        assert len(result) >= 1
        assert any(p.name == 'code-review' for p in result)

    def test_search_empty_query_returns_all(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='prompt1', system_prompt='Content'))
        storage.create(Prompt(name='prompt2', system_prompt='Content'))

        result = storage.search('')

        assert len(result) == 2

    def test_search_respects_limit(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        for i in range(5):
            storage.create(Prompt(name=f'prompt{i}', system_prompt='Content'))

        result = storage.search('prompt', limit=3)

        assert len(result) <= 3


class TestPromptStorageGetAllTags:
    def test_get_all_tags_empty(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)

        result = storage.get_all_tags()

        assert result == {}

    def test_get_all_tags_with_counts(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='p1', system_prompt='C', tags=['coding', 'python']))
        storage.create(Prompt(name='p2', system_prompt='C', tags=['coding']))
        storage.create(Prompt(name='p3', system_prompt='C', tags=['writing']))

        result = storage.get_all_tags()

        assert result['coding'] == 2
        assert result['python'] == 1
        assert result['writing'] == 1


class TestPromptStorageGetAllGroups:
    def test_get_all_groups_empty(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)

        result = storage.get_all_groups()

        assert result == {}

    def test_get_all_groups_with_counts(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(name='p1', system_prompt='C', group='coding'))
        storage.create(Prompt(name='p2', system_prompt='C', group='coding'))
        storage.create(Prompt(name='p3', system_prompt='C', group=''))

        result = storage.get_all_groups()

        assert result['coding'] == 2
        assert result[''] == 1


class TestPromptStorageFileFormat:
    def test_file_has_correct_frontmatter(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        storage.create(Prompt(
            name='test-prompt',
            description='Test description',
            system_prompt='System content',
            tags=['tag1', 'tag2'],
        ))

        content = (tmp_path / 'test-prompt.md').read_text()

        # Check frontmatter structure
        assert content.startswith('---\n')
        assert 'name: test-prompt' in content
        assert 'description: Test description' in content
        assert 'tag1' in content
        assert 'tag2' in content

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        storage = PromptStorage(prompts_dir=tmp_path)
        original = Prompt(
            name='test-prompt',
            description='Test description',
            system_prompt='System content\nWith multiple lines',
            user_prompt='User content\nAlso multiple lines',
            tags=['tag1', 'tag2'],
            group='coding',
        )

        storage.create(original)
        result = storage.read('test-prompt', group='coding')

        assert result.name == original.name
        assert result.description == original.description
        assert result.system_prompt == original.system_prompt
        assert result.user_prompt == original.user_prompt
        assert result.tags == original.tags
        assert result.group == original.group
