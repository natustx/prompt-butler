from fastapi import APIRouter, HTTPException, status

from prompt_butler.models import TagCount, TagRenameRequest, TagRenameResponse
from prompt_butler.services.storage import PromptStorage, TagNotFoundError

router = APIRouter(prefix='/api/tags', tags=['tags'])

# Share storage instance with prompts router
_storage = PromptStorage()


@router.get('/', response_model=list[TagCount])
async def list_tags():
    """Get all unique tags with usage counts."""
    tag_counts = _storage.get_all_tags()

    return [TagCount(tag=tag, count=count) for tag, count in sorted(tag_counts.items())]


@router.post('/rename', response_model=TagRenameResponse)
async def rename_tag(request: TagRenameRequest) -> TagRenameResponse:
    """Rename a tag across all prompts.

    Updates all prompts that have the old_tag, replacing it with new_tag.
    Returns the count of prompts that were updated.
    """
    try:
        updated_count = _storage.rename_tag(request.old_tag, request.new_tag)
        return TagRenameResponse(updated_count=updated_count)
    except TagNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
