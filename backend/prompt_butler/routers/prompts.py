from fastapi import APIRouter, HTTPException, Query, status

from prompt_butler.models import (
    GroupRenameRequest,
    GroupRenameResponse,
    Prompt,
    PromptCreate,
    PromptResponse,
    PromptUpdate,
    TagRenameRequest,
    TagRenameResponse,
    TagWithCount,
)
from prompt_butler.services.storage import (
    GroupExistsError,
    GroupNotFoundError,
    PromptExistsError,
    StorageError,
    storage_service,
)

router = APIRouter(prefix='/api', tags=['prompts'], responses={404: {'description': 'Prompt not found'}})


@router.get('/prompts', response_model=list[PromptResponse])
async def list_prompts(group: str | None = Query(None, description='Filter by group')):
    """List all available prompts with full details."""
    try:
        return storage_service.list(group=group)
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/groups', response_model=list[str], tags=['groups'])
async def list_groups():
    """List all available groups."""
    try:
        return storage_service.list_groups()
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/tags', response_model=list[TagWithCount], tags=['tags'])
async def list_tags():
    """List all tags with their usage counts."""
    try:
        tag_counts = storage_service.list_all_tags()
        return [TagWithCount(name=name, count=count) for name, count in tag_counts.items()]
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post('/tags/rename', response_model=TagRenameResponse, tags=['tags'])
async def rename_tag(request: TagRenameRequest):
    """Rename a tag across all prompts."""
    try:
        updated_count = storage_service.rename_tag(request.old_tag, request.new_tag)
        return TagRenameResponse(old_tag=request.old_tag, new_tag=request.new_tag, updated_count=updated_count)
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post('/groups/rename', response_model=GroupRenameResponse, tags=['groups'])
async def rename_group(request: GroupRenameRequest):
    """Rename a group by moving all prompts to the new group."""
    try:
        moved_count = storage_service.rename_group(request.old_name, request.new_name)
        return GroupRenameResponse(old_name=request.old_name, new_name=request.new_name, moved_count=moved_count)
    except GroupNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except GroupExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post('/prompts', response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt."""
    prompt = Prompt(
        name=prompt_data.name,
        description=prompt_data.description or '',
        system_prompt=prompt_data.system_prompt,
        user_prompt=prompt_data.user_prompt or '',
        tags=prompt_data.tags or [],
        group=prompt_data.group or '',
    )

    try:
        return storage_service.create(prompt)
    except PromptExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get('/prompts/{name}', response_model=PromptResponse)
async def get_prompt_by_name(name: str, group: str | None = Query(None, description='Optional group name')):
    """Get a specific prompt by name and optional group."""
    prompt = storage_service.get(name, group=group)
    if prompt is None:
        group_label = group or 'ungrouped'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group_label}"'
        )
    return prompt


@router.get('/prompts/{group}/{name}', response_model=PromptResponse)
async def get_prompt(group: str, name: str):
    """Get a specific prompt by group and name."""
    prompt = storage_service.get(name, group=group)
    if prompt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group}"'
        )
    return prompt


@router.put('/prompts/{name}', response_model=PromptResponse)
async def update_prompt_by_name(
    name: str,
    prompt_update: PromptUpdate,
    group: str | None = Query(None, description='Optional group name'),
):
    """Update an existing prompt by name and optional group."""
    update_data = prompt_update.model_dump(exclude_unset=True)

    try:
        updated_prompt = storage_service.update(name, group or '', **update_data)
        if updated_prompt is None:
            group_label = group or 'ungrouped'
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group_label}"'
            )
        return updated_prompt
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.put('/prompts/{group}/{name}', response_model=PromptResponse)
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


@router.delete('/prompts/{name}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_by_name(name: str, group: str | None = Query(None, description='Optional group name')):
    """Delete a prompt by name and optional group."""
    if not storage_service.delete(name, group=group):
        group_label = group or 'ungrouped'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group_label}"'
        )


@router.delete('/prompts/{group}/{name}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(group: str, name: str):
    """Delete a prompt."""
    if not storage_service.delete(name, group=group):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Prompt "{name}" not found in group "{group}"'
        )
