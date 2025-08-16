
from fastapi import APIRouter, HTTPException, status

from models import Prompt, PromptCreate, PromptResponse, PromptUpdate
from services.storage import PromptNotFoundError, StorageError, storage_service

router = APIRouter(prefix='/api/prompts', tags=['prompts'], responses={404: {'description': 'Prompt not found'}})


@router.get('/', response_model=list[PromptResponse])
async def list_prompts():
    """List all available prompts with full details."""
    try:
        return storage_service.list_prompts()
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/{name}', response_model=PromptResponse)
async def get_prompt(name: str):
    """Get a specific prompt by name."""
    prompt = storage_service.get_prompt(name)
    if prompt is None:
        raise PromptNotFoundError(f'Prompt "{name}" not found')
    return prompt


@router.post('/', response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt."""
    if storage_service.prompt_exists(prompt_data.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Prompt "{prompt_data.name}" already exists')

    prompt = Prompt(
        name=prompt_data.name,
        description=prompt_data.description or '',
        system_prompt=prompt_data.system_prompt,
        user_prompt=prompt_data.user_prompt or '',
        tags=prompt_data.tags or [],
    )

    storage_service.save_prompt(prompt)
    return prompt


@router.put('/{name}', response_model=PromptResponse)
async def update_prompt(name: str, prompt_update: PromptUpdate):
    """Update an existing prompt."""
    existing_prompt = storage_service.get_prompt(name)
    if existing_prompt is None:
        raise PromptNotFoundError(f'Prompt "{name}" not found')

    update_data = prompt_update.model_dump(exclude_unset=True)
    updated_prompt = existing_prompt.model_copy(update=update_data)

    storage_service.save_prompt(updated_prompt)
    return updated_prompt


@router.delete('/{name}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(name: str):
    """Delete a prompt."""
    if not storage_service.delete_prompt(name):
        raise PromptNotFoundError(f'Prompt "{name}" not found')
