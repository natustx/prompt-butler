import shutil

from fastapi import APIRouter, HTTPException

from prompt_butler.models import GroupCount, GroupRenameRequest, GroupRenameResponse
from prompt_butler.services.storage import PromptStorage

router = APIRouter(prefix='/api/groups', tags=['groups'])

# Share storage instance with other routers
_storage = PromptStorage()


@router.get('/', response_model=list[GroupCount])
async def list_groups():
    """Get all groups with prompt counts."""
    group_counts = _storage.get_all_groups()

    return [GroupCount(group=group, count=count) for group, count in sorted(group_counts.items())]


@router.post('/rename', response_model=GroupRenameResponse)
async def rename_group(request: GroupRenameRequest):
    """Rename a group, moving all prompts to the new group name.

    Args:
        request: The rename request with old_group and new_group names.

    Returns:
        The count of prompts moved to the new group.

    Raises:
        HTTPException 404: If old_group doesn't exist.
        HTTPException 409: If new_group already exists.
    """
    old_path = _storage.prompts_dir / request.old_group
    new_path = _storage.prompts_dir / request.new_group

    # Check if old group exists
    if not old_path.exists() or not old_path.is_dir():
        raise HTTPException(status_code=404, detail=f'Group "{request.old_group}" not found')

    # Check if new group already exists
    if new_path.exists():
        raise HTTPException(status_code=409, detail=f'Group "{request.new_group}" already exists')

    # Count prompts before moving
    prompts_in_group = list(old_path.glob('*.md'))
    count = len(prompts_in_group)

    # Rename the folder
    try:
        shutil.move(str(old_path), str(new_path))
    except OSError as e:
        raise HTTPException(status_code=500, detail=f'Failed to rename group: {e}') from e

    return GroupRenameResponse(updated_count=count)
