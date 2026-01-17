from fastapi import APIRouter, HTTPException, status

from prompt_butler.models import Prompt, PromptCreate, PromptResponse, PromptUpdate
from prompt_butler.services.storage import PromptExistsError, PromptNotFoundError, PromptStorage, StorageError

router = APIRouter(prefix='/api/prompts', tags=['prompts'], responses={404: {'description': 'Prompt not found'}})

# Global storage instance
_storage = PromptStorage()


@router.get('/', response_model=list[PromptResponse])
async def list_prompts():
    """List all available prompts with full details."""
    try:
        return _storage.list_all()
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/{name}', response_model=PromptResponse)
async def get_prompt(name: str):
    """Get a specific prompt by name."""
    prompt = _storage.read(name)
    if prompt is None:
        raise PromptNotFoundError(f'Prompt "{name}" not found')
    return prompt


@router.post('/', response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt."""
    prompt = Prompt(
        name=prompt_data.name,
        description=prompt_data.description or '',
        system_prompt=prompt_data.system_prompt,
        user_prompt=prompt_data.user_prompt or '',
        group=prompt_data.group or '',
        tags=prompt_data.tags or [],
    )

    try:
        return _storage.create(prompt)
    except PromptExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Prompt "{prompt_data.name}" already exists',
        ) from None


@router.put('/{name}', response_model=PromptResponse)
async def update_prompt(name: str, prompt_update: PromptUpdate):
    """Update an existing prompt."""
    existing_prompt = _storage.read(name)
    if existing_prompt is None:
        raise PromptNotFoundError(f'Prompt "{name}" not found')

    update_data = prompt_update.model_dump(exclude_unset=True)
    updated_prompt = existing_prompt.model_copy(update=update_data)

    return _storage.update(name, updated_prompt, existing_prompt.group)


@router.delete('/{name}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(name: str):
    """Delete a prompt."""
    if not _storage.delete(name):
        raise PromptNotFoundError(f'Prompt "{name}" not found')
