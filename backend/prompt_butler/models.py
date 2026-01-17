import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

TAG_MAX_LENGTH = 50
TAG_PATTERN = re.compile(r'^[a-zA-Z0-9 _-]+$')
# Keep name/group patterns aligned with frontend validation in frontend/src/schemas/prompt.ts.
NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
GROUP_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
PROMPT_MAX_LENGTH = 50000


def _validate_tags(value: list[str] | None) -> list[str] | None:
    if value is None:
        return value
    if not isinstance(value, list):
        raise ValueError('Tags must be a list of strings')
    for tag in value:
        if not isinstance(tag, str):
            raise ValueError('Tags must be a list of strings')
        if tag == '':
            raise ValueError('Tag must be at least 1 character long')
        if len(tag) > TAG_MAX_LENGTH:
            raise ValueError('Tag must be at most 50 characters long')
        if not TAG_PATTERN.match(tag):
            raise ValueError('Tag must contain only alphanumeric characters, spaces, underscores, and hyphens')
    return value


class Prompt(BaseModel):
    name: str = Field(..., description='Unique identifier for the prompt', min_length=1, max_length=100)
    description: str = Field('', description="Brief description of the prompt's purpose")
    system_prompt: str = Field(
        ...,
        description='System prompt to set AI context and behavior',
        max_length=PROMPT_MAX_LENGTH,
    )
    user_prompt: str = Field(
        '',
        description='User prompt template or example',
        max_length=PROMPT_MAX_LENGTH,
    )
    group: str = Field('', description='Group name for organizing prompts')
    tags: list[str] = Field(default_factory=list, description='List of tags for categorizing the prompt')

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not NAME_PATTERN.match(v):
            raise ValueError('Name must contain only alphanumeric characters, underscores, and hyphens')
        return v

    @field_validator('group')
    @classmethod
    def validate_group(cls, v: str) -> str:
        if v and not GROUP_PATTERN.match(v):
            raise ValueError('Group must contain only alphanumeric characters, underscores, and hyphens')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        validated = _validate_tags(v)
        return validated if validated is not None else []

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'code_review',
                    'description': 'Reviews code for best practices and potential issues',
                    'system_prompt': 'You are an expert code reviewer. Analyze code for bugs and best practices.',
                    'user_prompt': 'Please review the following code:\n\n{code}',
                    'group': 'development',
                    'tags': ['code', 'review', 'development'],
                }
            ]
        }
    }


class PromptCreate(BaseModel):
    name: str = Field(..., description='Unique identifier for the prompt', min_length=1, max_length=100)
    description: Optional[str] = Field('', description="Brief description of the prompt's purpose")
    system_prompt: str = Field(
        ...,
        description='System prompt to set AI context and behavior',
        max_length=PROMPT_MAX_LENGTH,
    )
    user_prompt: Optional[str] = Field(
        '',
        description='User prompt template or example',
        max_length=PROMPT_MAX_LENGTH,
    )
    group: Optional[str] = Field('', description='Group name for organizing prompts')
    tags: Optional[list[str]] = Field(default_factory=list, description='List of tags for categorizing the prompt')

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not NAME_PATTERN.match(v):
            raise ValueError('Name must contain only alphanumeric characters, underscores, and hyphens')
        return v

    @field_validator('group')
    @classmethod
    def validate_group(cls, v: str | None) -> str:
        if v and not GROUP_PATTERN.match(v):
            raise ValueError('Group must contain only alphanumeric characters, underscores, and hyphens')
        return v or ''

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        return _validate_tags(v)


class PromptUpdate(BaseModel):
    description: Optional[str] = Field(None, description="Brief description of the prompt's purpose")
    system_prompt: Optional[str] = Field(
        None,
        description='System prompt to set AI context and behavior',
        max_length=PROMPT_MAX_LENGTH,
    )
    user_prompt: Optional[str] = Field(
        None,
        description='User prompt template or example',
        max_length=PROMPT_MAX_LENGTH,
    )
    group: Optional[str] = Field(None, description='Group name for organizing prompts')
    tags: Optional[list[str]] = Field(None, description='List of tags for categorizing the prompt')

    @field_validator('group')
    @classmethod
    def validate_group(cls, v: str | None) -> str | None:
        if v is not None and v != '' and not GROUP_PATTERN.match(v):
            raise ValueError('Group must contain only alphanumeric characters, underscores, and hyphens')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        return _validate_tags(v)


class PromptResponse(Prompt):
    pass


class ErrorResponse(BaseModel):
    detail: str = Field(..., description='Error message describing what went wrong')

    model_config = {
        'json_schema_extra': {'examples': [{'detail': 'Prompt not found'}, {'detail': 'Invalid prompt data'}]}
    }


class TagCount(BaseModel):
    tag: str = Field(..., description='Tag name')
    count: int = Field(..., description='Number of prompts with this tag')


class GroupCount(BaseModel):
    group: str = Field(..., description='Group name (empty string for ungrouped)')
    count: int = Field(..., description='Number of prompts in this group')


class TagRenameRequest(BaseModel):
    old_tag: str = Field(..., description='Current tag name to rename', min_length=1)
    new_tag: str = Field(..., description='New tag name', min_length=1, max_length=50)

    @field_validator('new_tag')
    @classmethod
    def validate_new_tag(cls, v: str) -> str:
        if not TAG_PATTERN.match(v):
            raise ValueError('Tag must contain only alphanumeric characters, spaces, underscores, and hyphens')
        return v


class TagRenameResponse(BaseModel):
    updated_count: int = Field(..., description='Number of prompts updated')


class GroupRenameRequest(BaseModel):
    old_group: str = Field(..., description='Current group name to rename', min_length=1)
    new_group: str = Field(..., description='New group name', min_length=1, max_length=50)

    @field_validator('new_group')
    @classmethod
    def validate_new_group(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Group must contain only alphanumeric characters, underscores, and hyphens')
        return v


class GroupRenameResponse(BaseModel):
    updated_count: int = Field(..., description='Number of prompts moved to new group')
