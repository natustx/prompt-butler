import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Prompt(BaseModel):
    name: str = Field(..., description='Unique identifier for the prompt', min_length=1, max_length=100)
    description: str = Field('', description="Brief description of the prompt's purpose")
    system_prompt: str = Field(..., description='System prompt to set AI context and behavior')
    user_prompt: str = Field('', description='User prompt template or example')

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, underscores, and hyphens')
        return v

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'name': 'code_review',
                    'description': 'Reviews code for best practices and potential issues',
                    'system_prompt': 'You are an expert code reviewer. Analyze code for bugs and best practices.',
                    'user_prompt': 'Please review the following code:\n\n{code}',
                }
            ]
        }
    }


class PromptCreate(BaseModel):
    name: str = Field(..., description='Unique identifier for the prompt', min_length=1, max_length=100)
    description: Optional[str] = Field('', description="Brief description of the prompt's purpose")
    system_prompt: str = Field(..., description='System prompt to set AI context and behavior')
    user_prompt: Optional[str] = Field('', description='User prompt template or example')

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, underscores, and hyphens')
        return v


class PromptUpdate(BaseModel):
    description: Optional[str] = Field(None, description="Brief description of the prompt's purpose")
    system_prompt: Optional[str] = Field(None, description='System prompt to set AI context and behavior')
    user_prompt: Optional[str] = Field(None, description='User prompt template or example')


class PromptResponse(Prompt):
    pass


class ErrorResponse(BaseModel):
    detail: str = Field(..., description='Error message describing what went wrong')

    model_config = {
        'json_schema_extra': {'examples': [{'detail': 'Prompt not found'}, {'detail': 'Invalid prompt data'}]}
    }
