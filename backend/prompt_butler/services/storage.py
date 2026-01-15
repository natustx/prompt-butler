from __future__ import annotations

import os
import re
from pathlib import Path

import frontmatter

from prompt_butler.models import Prompt

USER_SEPARATOR = '---user---'


class PromptStorage:
    """Storage service for prompts using markdown files with YAML frontmatter.

    File format:
        ---
        name: prompt-name
        description: Brief description
        tags:
          - tag1
          - tag2
        ---
        System prompt content here...

        ---user---
        User prompt content here...

    Folder structure: ~/.prompts/{group}/name.md
    """

    def __init__(self, prompts_dir: str | Path | None = None):
        if prompts_dir is None:
            prompts_dir = os.getenv('PROMPTS_DIR', os.path.expanduser('~/.prompts'))
        self.prompts_dir = Path(prompts_dir)
        self._ensure_prompts_dir()

    def _ensure_prompts_dir(self) -> None:
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def slugify(name: str) -> str:
        """Convert a name to a filename-safe slug."""
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def _get_group_dir(self, group: str) -> Path:
        """Get the directory path for a group."""
        return self.prompts_dir / self.slugify(group)

    def _get_prompt_path(self, name: str, group: str) -> Path:
        """Get the file path for a prompt."""
        group_dir = self._get_group_dir(group)
        return group_dir / f'{self.slugify(name)}.md'

    def _parse_content(self, content: str) -> tuple[str, str]:
        """Parse markdown content into system_prompt and user_prompt.

        Content is split by ---user--- separator.
        """
        if USER_SEPARATOR in content:
            parts = content.split(USER_SEPARATOR, 1)
            system_prompt = parts[0].strip()
            user_prompt = parts[1].strip() if len(parts) > 1 else ''
        else:
            system_prompt = content.strip()
            user_prompt = ''
        return system_prompt, user_prompt

    def _format_content(self, system_prompt: str, user_prompt: str) -> str:
        """Format system_prompt and user_prompt into markdown content."""
        if user_prompt:
            return f'{system_prompt}\n\n{USER_SEPARATOR}\n{user_prompt}'
        return system_prompt

    def _prompt_from_file(self, file_path: Path, group: str) -> Prompt | None:
        """Load a Prompt from a markdown file."""
        try:
            post = frontmatter.load(file_path)
            system_prompt, user_prompt = self._parse_content(post.content)

            return Prompt(
                name=post.get('name', file_path.stem),
                description=post.get('description', ''),
                tags=post.get('tags', []),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                group=group,
            )
        except Exception:
            return None

    def list(self, group: str | None = None) -> list[Prompt]:
        """List all prompts, optionally filtered by group.

        Args:
            group: Optional group name to filter by. If None, returns all prompts.

        Returns:
            List of Prompt objects sorted by name.
        """
        prompts = []

        if group:
            group_dir = self._get_group_dir(group)
            if group_dir.exists():
                for file_path in group_dir.glob('*.md'):
                    prompt = self._prompt_from_file(file_path, group)
                    if prompt:
                        prompts.append(prompt)
        else:
            for group_dir in self.prompts_dir.iterdir():
                if group_dir.is_dir():
                    group_name = group_dir.name
                    for file_path in group_dir.glob('*.md'):
                        prompt = self._prompt_from_file(file_path, group_name)
                        if prompt:
                            prompts.append(prompt)

        return sorted(prompts, key=lambda p: (p.group, p.name))

    def get(self, name: str, group: str = 'default') -> Prompt | None:
        """Get a prompt by name and group.

        Args:
            name: The prompt name.
            group: The group name (default: 'default').

        Returns:
            The Prompt if found, None otherwise.
        """
        file_path = self._get_prompt_path(name, group)
        if not file_path.exists():
            return None
        return self._prompt_from_file(file_path, group)

    def create(self, prompt: Prompt) -> Prompt:
        """Create a new prompt.

        Args:
            prompt: The Prompt to create.

        Returns:
            The created Prompt.

        Raises:
            PromptExistsError: If a prompt with the same name exists in the group.
        """
        file_path = self._get_prompt_path(prompt.name, prompt.group)

        if file_path.exists():
            raise PromptExistsError(f"Prompt '{prompt.name}' already exists in group '{prompt.group}'")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        post = frontmatter.Post(
            content=self._format_content(prompt.system_prompt, prompt.user_prompt),
            name=prompt.name,
            description=prompt.description,
            tags=prompt.tags,
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        return prompt

    def update(self, name: str, group: str, **kwargs) -> Prompt | None:
        """Update an existing prompt.

        Args:
            name: The prompt name.
            group: The group name.
            **kwargs: Fields to update (description, system_prompt, user_prompt, tags).

        Returns:
            The updated Prompt if found, None otherwise.
        """
        file_path = self._get_prompt_path(name, group)
        if not file_path.exists():
            return None

        prompt = self._prompt_from_file(file_path, group)
        if not prompt:
            return None

        update_data = prompt.model_dump()
        for key, value in kwargs.items():
            if value is not None and key in update_data:
                update_data[key] = value

        updated_prompt = Prompt(**update_data)

        post = frontmatter.Post(
            content=self._format_content(updated_prompt.system_prompt, updated_prompt.user_prompt),
            name=updated_prompt.name,
            description=updated_prompt.description,
            tags=updated_prompt.tags,
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        return updated_prompt

    def delete(self, name: str, group: str = 'default') -> bool:
        """Delete a prompt.

        Args:
            name: The prompt name.
            group: The group name (default: 'default').

        Returns:
            True if deleted, False if not found.
        """
        file_path = self._get_prompt_path(name, group)
        if not file_path.exists():
            return False

        file_path.unlink()

        group_dir = file_path.parent
        if group_dir.exists() and not any(group_dir.iterdir()):
            group_dir.rmdir()

        return True

    def exists(self, name: str, group: str = 'default') -> bool:
        """Check if a prompt exists.

        Args:
            name: The prompt name.
            group: The group name (default: 'default').

        Returns:
            True if exists, False otherwise.
        """
        file_path = self._get_prompt_path(name, group)
        return file_path.exists()

    def list_groups(self, include_empty: bool = False) -> list[str]:
        """List all groups.

        Args:
            include_empty: If True, include empty group directories.

        Returns:
            List of group names sorted alphabetically.
        """
        groups = []
        for group_dir in self.prompts_dir.iterdir():
            if group_dir.is_dir():
                if include_empty or any(group_dir.glob('*.md')):
                    groups.append(group_dir.name)
        return sorted(groups)

    def list_all_tags(self) -> dict[str, int]:
        """List all unique tags across all prompts with their counts.

        Returns:
            Dictionary mapping tag names to their usage counts.
        """
        tag_counts: dict[str, int] = {}
        for prompt in self.list():
            for tag in prompt.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return dict(sorted(tag_counts.items()))

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """Rename a tag across all prompts.

        Args:
            old_tag: The tag to rename.
            new_tag: The new tag name.

        Returns:
            Number of prompts updated.
        """
        updated_count = 0
        for prompt in self.list():
            if old_tag in prompt.tags:
                new_tags = [new_tag if t == old_tag else t for t in prompt.tags]
                self.update(prompt.name, prompt.group, tags=new_tags)
                updated_count += 1
        return updated_count

    def create_group(self, name: str) -> bool:
        """Create an empty group directory.

        Args:
            name: The group name to create.

        Returns:
            True if created, False if already exists.
        """
        group_dir = self._get_group_dir(name)
        if group_dir.exists():
            return False
        group_dir.mkdir(parents=True, exist_ok=True)
        return True

    def rename_group(self, old_name: str, new_name: str) -> int:
        """Rename a group by moving all prompts to the new group.

        Args:
            old_name: The current group name.
            new_name: The new group name.

        Returns:
            Number of prompts moved.

        Raises:
            GroupNotFoundError: If old group doesn't exist.
            GroupExistsError: If new group already exists with prompts.
        """
        old_dir = self._get_group_dir(old_name)
        new_dir = self._get_group_dir(new_name)

        if not old_dir.exists():
            raise GroupNotFoundError(f"Group '{old_name}' not found")

        if new_dir.exists() and any(new_dir.glob('*.md')):
            raise GroupExistsError(f"Group '{new_name}' already exists with prompts")

        new_dir.mkdir(parents=True, exist_ok=True)

        moved_count = 0
        for file_path in old_dir.glob('*.md'):
            new_path = new_dir / file_path.name
            file_path.rename(new_path)
            moved_count += 1

        if old_dir.exists() and not any(old_dir.iterdir()):
            old_dir.rmdir()

        return moved_count


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class PromptNotFoundError(StorageError):
    """Raised when a prompt is not found."""

    pass


class PromptExistsError(StorageError):
    """Raised when trying to create a prompt that already exists."""

    pass


class InvalidPromptDataError(StorageError):
    """Raised when prompt data is invalid."""

    pass


class GroupNotFoundError(StorageError):
    """Raised when a group is not found."""

    pass


class GroupExistsError(StorageError):
    """Raised when trying to create a group that already exists."""

    pass


# Legacy alias for backwards compatibility
StorageService = PromptStorage

# Default instance
storage_service = PromptStorage()
