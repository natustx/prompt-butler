import pytest
from pydantic import ValidationError

from prompt_butler.models import PROMPT_MAX_LENGTH, Prompt, PromptCreate, PromptUpdate


class TestPromptGroupField:
    def test_prompt_with_empty_group_is_valid(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            group='',
        )
        assert prompt.group == ''

    def test_prompt_with_valid_group_is_valid(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            group='my-group_123',
        )
        assert prompt.group == 'my-group_123'

    def test_prompt_with_alphanumeric_group_is_valid(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            group='TestGroup123',
        )
        assert prompt.group == 'TestGroup123'

    def test_prompt_with_hyphens_underscores_is_valid(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            group='my_group-name',
        )
        assert prompt.group == 'my_group-name'

    def test_prompt_with_invalid_group_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test_prompt',
                system_prompt='You are helpful.',
                group='invalid group!',
            )
        assert 'Group must contain only alphanumeric' in str(exc_info.value)

    def test_prompt_with_spaces_in_group_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test_prompt',
                system_prompt='You are helpful.',
                group='group with spaces',
            )
        assert 'Group must contain only alphanumeric' in str(exc_info.value)

    def test_prompt_defaults_group_to_empty(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
        )
        assert prompt.group == ''


class TestPromptCreateGroupField:
    def test_create_with_empty_group_is_valid(self):
        prompt = PromptCreate(
            name='test_prompt',
            system_prompt='You are helpful.',
            group='',
        )
        assert prompt.group == ''

    def test_create_with_valid_group_is_valid(self):
        prompt = PromptCreate(
            name='test_prompt',
            system_prompt='You are helpful.',
            group='my-group',
        )
        assert prompt.group == 'my-group'

    def test_create_with_none_group_converts_to_empty(self):
        prompt = PromptCreate(
            name='test_prompt',
            system_prompt='You are helpful.',
            group=None,
        )
        assert prompt.group == ''

    def test_create_with_invalid_group_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PromptCreate(
                name='test_prompt',
                system_prompt='You are helpful.',
                group='invalid!@#',
            )
        assert 'Group must contain only alphanumeric' in str(exc_info.value)

    def test_create_defaults_group_to_empty(self):
        prompt = PromptCreate(
            name='test_prompt',
            system_prompt='You are helpful.',
        )
        assert prompt.group == ''


class TestPromptTagsField:
    def test_prompt_with_valid_tags_is_valid(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            tags=['alpha', 'beta_tag', 'gamma-123'],
        )
        assert prompt.tags == ['alpha', 'beta_tag', 'gamma-123']

    def test_prompt_with_invalid_tag_characters_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test_prompt',
                system_prompt='You are helpful.',
                tags=['bad tag!'],
            )
        assert 'Tag must contain only alphanumeric' in str(exc_info.value)

    def test_prompt_with_empty_tag_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test_prompt',
                system_prompt='You are helpful.',
                tags=[''],
            )
        assert 'Tag must be at least 1 character' in str(exc_info.value)

    def test_prompt_with_too_long_tag_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test_prompt',
                system_prompt='You are helpful.',
                tags=['a' * 51],
            )
        assert 'Tag must be at most 50 characters' in str(exc_info.value)


class TestPromptCreateTagsField:
    def test_create_with_valid_tags_is_valid(self):
        prompt = PromptCreate(
            name='test_prompt',
            system_prompt='You are helpful.',
            tags=['tag_one', 'tag-two'],
        )
        assert prompt.tags == ['tag_one', 'tag-two']

    def test_create_with_invalid_tag_characters_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PromptCreate(
                name='test_prompt',
                system_prompt='You are helpful.',
                tags=['bad tag!'],
            )
        assert 'Tag must contain only alphanumeric' in str(exc_info.value)


class TestPromptUpdateTagsField:
    def test_update_with_none_tags_is_valid(self):
        update = PromptUpdate(tags=None)
        assert update.tags is None

    def test_update_with_invalid_tag_characters_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PromptUpdate(tags=['bad tag!'])
        assert 'Tag must contain only alphanumeric' in str(exc_info.value)


class TestPromptUpdateGroupField:
    def test_update_with_none_group_is_valid(self):
        update = PromptUpdate(group=None)
        assert update.group is None

    def test_update_with_empty_group_is_valid(self):
        update = PromptUpdate(group='')
        assert update.group == ''

    def test_update_with_valid_group_is_valid(self):
        update = PromptUpdate(group='new-group')
        assert update.group == 'new-group'

    def test_update_with_invalid_group_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PromptUpdate(group='invalid group!')
        assert 'Group must contain only alphanumeric' in str(exc_info.value)

    def test_update_defaults_group_to_none(self):
        update = PromptUpdate()
        assert update.group is None


class TestPromptUserPromptField:
    def test_prompt_with_empty_user_prompt_is_valid(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            user_prompt='',
        )
        assert prompt.user_prompt == ''

    def test_prompt_with_user_prompt_is_valid(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            user_prompt='Please help with {task}',
        )
        assert prompt.user_prompt == 'Please help with {task}'

    def test_prompt_defaults_user_prompt_to_empty(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
        )
        assert prompt.user_prompt == ''


class TestPromptContentLength:
    def test_prompt_system_prompt_too_long_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test_prompt',
                system_prompt='a' * (PROMPT_MAX_LENGTH + 1),
            )
        assert f'at most {PROMPT_MAX_LENGTH}' in str(exc_info.value)

    def test_prompt_user_prompt_too_long_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test_prompt',
                system_prompt='You are helpful.',
                user_prompt='b' * (PROMPT_MAX_LENGTH + 1),
            )
        assert f'at most {PROMPT_MAX_LENGTH}' in str(exc_info.value)

    def test_prompt_create_system_prompt_too_long_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PromptCreate(
                name='test_prompt',
                system_prompt='c' * (PROMPT_MAX_LENGTH + 1),
            )
        assert f'at most {PROMPT_MAX_LENGTH}' in str(exc_info.value)

    def test_prompt_update_user_prompt_too_long_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PromptUpdate(
                user_prompt='d' * (PROMPT_MAX_LENGTH + 1),
            )
        assert f'at most {PROMPT_MAX_LENGTH}' in str(exc_info.value)


class TestPromptModelSerialization:
    def test_prompt_serializes_with_group_field(self):
        prompt = Prompt(
            name='test_prompt',
            system_prompt='You are helpful.',
            group='my-group',
        )
        data = prompt.model_dump()
        assert data['group'] == 'my-group'

    def test_prompt_deserializes_with_group_field(self):
        data = {
            'name': 'test_prompt',
            'system_prompt': 'You are helpful.',
            'group': 'my-group',
            'user_prompt': '',
            'description': '',
            'tags': [],
        }
        prompt = Prompt.model_validate(data)
        assert prompt.group == 'my-group'

    def test_prompt_deserializes_without_group_uses_default(self):
        data = {
            'name': 'test_prompt',
            'system_prompt': 'You are helpful.',
        }
        prompt = Prompt.model_validate(data)
        assert prompt.group == ''
