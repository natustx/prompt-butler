"""Tests for Prompt models, focusing on group field validation."""

import pytest
from pydantic import ValidationError

from models import Prompt, PromptCreate, PromptUpdate


class TestPromptGroupField:
    """Tests for the group field on Prompt model."""

    def test_prompt_with_valid_group(self):
        """Prompt accepts valid group names."""
        prompt = Prompt(
            name='test-prompt',
            system_prompt='You are a test assistant.',
            group='my-group',
        )
        assert prompt.group == 'my-group'

    def test_prompt_with_empty_group(self):
        """Prompt accepts empty group (default)."""
        prompt = Prompt(
            name='test-prompt',
            system_prompt='You are a test assistant.',
        )
        assert prompt.group == ''

    def test_prompt_group_with_underscores(self):
        """Group name can contain underscores."""
        prompt = Prompt(
            name='test-prompt',
            system_prompt='Test',
            group='my_group_name',
        )
        assert prompt.group == 'my_group_name'

    def test_prompt_group_with_hyphens(self):
        """Group name can contain hyphens."""
        prompt = Prompt(
            name='test-prompt',
            system_prompt='Test',
            group='my-group-name',
        )
        assert prompt.group == 'my-group-name'

    def test_prompt_group_with_alphanumeric(self):
        """Group name can contain alphanumeric characters."""
        prompt = Prompt(
            name='test-prompt',
            system_prompt='Test',
            group='Group123',
        )
        assert prompt.group == 'Group123'

    def test_prompt_group_rejects_spaces(self):
        """Group name cannot contain spaces."""
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test-prompt',
                system_prompt='Test',
                group='my group',
            )
        assert 'Group must contain only alphanumeric' in str(exc_info.value)

    def test_prompt_group_rejects_special_chars(self):
        """Group name cannot contain special characters."""
        with pytest.raises(ValidationError) as exc_info:
            Prompt(
                name='test-prompt',
                system_prompt='Test',
                group='my@group!',
            )
        assert 'Group must contain only alphanumeric' in str(exc_info.value)


class TestPromptCreateGroupField:
    """Tests for the group field on PromptCreate model."""

    def test_create_with_valid_group(self):
        """PromptCreate accepts valid group names."""
        prompt = PromptCreate(
            name='test-prompt',
            system_prompt='You are a test assistant.',
            group='dev-prompts',
        )
        assert prompt.group == 'dev-prompts'

    def test_create_with_empty_group(self):
        """PromptCreate defaults to empty group."""
        prompt = PromptCreate(
            name='test-prompt',
            system_prompt='You are a test assistant.',
        )
        assert prompt.group == ''

    def test_create_with_none_group(self):
        """PromptCreate converts None to empty string."""
        prompt = PromptCreate(
            name='test-prompt',
            system_prompt='You are a test assistant.',
            group=None,
        )
        assert prompt.group == ''

    def test_create_group_validation_rejects_invalid(self):
        """PromptCreate rejects invalid group names."""
        with pytest.raises(ValidationError) as exc_info:
            PromptCreate(
                name='test-prompt',
                system_prompt='Test',
                group='invalid group!',
            )
        assert 'Group must contain only alphanumeric' in str(exc_info.value)


class TestPromptUpdateGroupField:
    """Tests for the group field on PromptUpdate model."""

    def test_update_with_valid_group(self):
        """PromptUpdate accepts valid group names."""
        update = PromptUpdate(group='new-group')
        assert update.group == 'new-group'

    def test_update_with_none_group(self):
        """PromptUpdate allows None (no change)."""
        update = PromptUpdate()
        assert update.group is None

    def test_update_with_empty_group(self):
        """PromptUpdate accepts empty string to clear group."""
        update = PromptUpdate(group='')
        assert update.group == ''

    def test_update_group_validation_rejects_invalid(self):
        """PromptUpdate rejects invalid group names."""
        with pytest.raises(ValidationError) as exc_info:
            PromptUpdate(group='bad group!')
        assert 'Group must contain only alphanumeric' in str(exc_info.value)


class TestPromptSerialization:
    """Tests for serialization with group field."""

    def test_prompt_serializes_with_group(self):
        """Prompt includes group in serialized output."""
        prompt = Prompt(
            name='test-prompt',
            system_prompt='Test',
            group='my-group',
        )
        data = prompt.model_dump()
        assert data['group'] == 'my-group'

    def test_prompt_deserializes_with_group(self):
        """Prompt can be created from dict with group."""
        data = {
            'name': 'test-prompt',
            'system_prompt': 'Test',
            'group': 'loaded-group',
        }
        prompt = Prompt.model_validate(data)
        assert prompt.group == 'loaded-group'

    def test_prompt_deserializes_without_group(self):
        """Prompt defaults group when missing from dict."""
        data = {
            'name': 'test-prompt',
            'system_prompt': 'Test',
        }
        prompt = Prompt.model_validate(data)
        assert prompt.group == ''
