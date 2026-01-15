from fastapi import APIRouter, HTTPException, Query, status

from prompt_butler.models import Prompt, PromptCreate, PromptResponse, PromptUpdate
from prompt_butler.services.storage import PromptExistsError, StorageError, storage_service

router = APIRouter(prefix='/api/prompts', tags=['prompts'], responses={404: {'description': 'Prompt not found'}})


@router.get('/', response_model=list[PromptResponse])
async def list_prompts(group: str | None = Query(None, description='Filter by group')):
    """List all available prompts with full details."""
    try:
        return storage_service.list(group=group)
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/groups', response_model=list[str])
async def list_groups():
    """List all available groups."""
    try:
        return storage_service.list_groups()
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/{group}/{name}', response_model=PromptResponse)
async def get_prompt(group: str, name: str):
    """Get a specific prompt by group and name."""
    prompt = storage_service.get(name, group=group)
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group}"'
        )
    return prompt


@router.post('/', response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt."""
    prompt = Prompt(
        name=prompt_data.name,
        description=prompt_data.description or '',
        system_prompt=prompt_data.system_prompt,
        user_prompt=prompt_data.user_prompt or '',
        tags=prompt_data.tags or [],
        group=prompt_data.group or 'default',
    )

    try:
        return storage_service.create(prompt)
    except PromptExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.put('/{group}/{name}', response_model=PromptResponse)
async def update_prompt(group: str, name: str, prompt_update: PromptUpdate):
    """Update an existing prompt."""
    update_data = prompt_update.model_dump(exclude_unset=True)

    try:
        updated_prompt = storage_service.update(name, group, **update_data)
        if updated_prompt is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group}"'
            )
        return updated_prompt
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.delete('/{group}/{name}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(group: str, name: str):
    """Delete a prompt."""
    if not storage_service.delete(name, group=group):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group}"'
        )
